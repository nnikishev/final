from datetime import datetime
from uuid import UUID
from app.models.board import Board
from app.models.defect import Defect
from app.services.cutting_algorithm import GreedyCutter
from app.services.price_service import PriceService
from app.core.database import AsyncSessionLocal

class BoardAggregator:
    def __init__(self, price_service: PriceService):
        self.active_boards = {}  # board_id -> dict с данными
        self.price_service = price_service

    async def process_event(self, event: dict):
        event_type = event.get("type")
        if event_type == "board_start":
            board_id = UUID(event["board_id"])
            self.active_boards[board_id] = {
                "camera_id": event["camera_id"],
                "start_time": datetime.fromisoformat(event["timestamp"]),
                "defects": [],
                "total_length_mm": None
            }
            # Сохраняем начало доски в БД (пока без длины)
            async with AsyncSessionLocal() as db:
                board = Board(
                    id=board_id,
                    camera_id=event["camera_id"],
                    start_time=self.active_boards[board_id]["start_time"]
                )
                db.add(board)
                await db.commit()

        elif event_type == "defect":
            board_id = UUID(event["board_id"])
            if board_id in self.active_boards:
                defect = {
                    "defect_type": event["defect_type"],
                    "confidence": event["confidence"],
                    "position_mm": event["position_mm"]["from_start_mm"],
                    "width_mm": event["position_mm"]["width_mm"],
                    "bbox_px": event["bbox_px"],
                    "frame_idx": event["frame_idx"],
                    "position_from_start_mm": event["position_mm"]["from_start_mm"],
                    "timestamp": datetime.fromisoformat(event["timestamp"])
                }
                self.active_boards[board_id]["defects"].append(defect)
                # Сохраняем дефект в БД сразу
                async with AsyncSessionLocal() as db:
                    defect_db = Defect(
                        board_id=board_id,
                        defect_type=defect["defect_type"],
                        confidence=defect["confidence"],
                        position_from_start_mm=defect["position_mm"],
                        width_mm=defect["width_mm"],
                        bbox_px=defect["bbox_px"],
                        frame_idx=defect["frame_idx"],
                        timestamp=defect["timestamp"]
                    )
                    db.add(defect_db)
                    await db.commit()

        elif event_type == "board_end":
            board_id = UUID(event["board_id"])
            if board_id in self.active_boards:
                board_data = self.active_boards[board_id]
                board_data["total_length_mm"] = event["total_length_mm"]
                board_data["defects_summary"] = event["defects_summary"]
                board_data["end_time"] = datetime.fromisoformat(event["timestamp"])

                # Обновляем запись доски в БД (длина, время окончания)
                async with AsyncSessionLocal() as db:
                    board = await db.get(Board, board_id)
                    if board:
                        board.end_time = board_data["end_time"]
                        board.total_length_mm = board_data["total_length_mm"]
                        board.defects_summary = board_data["defects_summary"]
                        await db.commit()

                # Запускаем алгоритм раскроя
                cutter = GreedyCutter(self.price_service)
                cut_plan = await cutter.optimize(board_id, board_data["total_length_mm"], board_data["defects"])

                # Сохраняем карту раскроя в БД
                async with AsyncSessionLocal() as db:
                    from app.models.cut_plan import CutPlan
                    plan_db = CutPlan(
                        board_id=board_id,
                        segments=cut_plan["segments"],
                        total_revenue=cut_plan["total_revenue"],
                        algorithm=cut_plan["algorithm"]
                    )
                    db.add(plan_db)
                    await db.commit()

                # Удаляем доску из активных
                del self.active_boards[board_id]