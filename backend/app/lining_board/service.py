from typing import List, Dict, Any, Optional, Annotated
from uuid import UUID
from datetime import datetime
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.lining_board.repository import BoardRepository
from app.lining_board.model import Board
from app.lining_board.schemas import (

    TopDefectDTO, QualityDistributionDTO, DefectDTO, BoardsByHourDTO, FrontendBoardDTO, CuttingPlanDTO
)

class StatisticsService:
    def __init__(self, session: AsyncSession):
        self.board_repo = BoardRepository(session)

    async def get_boards_for_frontend(
        self,
        search: Optional[str] = None,
        quality: Optional[str] = None,
        defect_type: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        # преобразуем sort_by в поле модели
        sort_field_map = {
            "date": "start_time",
            "quality": "quality",
            "length": "total_length_mm"
        }
        sort_field = sort_field_map.get(sort_by, "start_time")
        offset = (page - 1) * limit

        boards, total = await self.board_repo.get_list(
            limit=limit,
            offset=offset,
            sort_field=sort_field,
            sort_order=sort_order,
            search=search,
            quality=quality,
            defect_type=defect_type,
        )

        frontend_boards = []
        for board in boards:
            defects = await self.board_repo.get_defects_for_board(board.id)
            # преобразуем дефекты в DefectDTO
            defect_dtos = [
                DefectDTO(
                    id=str(d.id),
                    defect_type=d.defect_type,
                    severity=self._get_severity(d.defect_type),  # функция преобразования
                    location=f"{d.position_from_start_mm:.0f}мм" if d.position_from_start_mm else "unknown"
                )
                for d in defects
            ]
            # вычисляем processing_duration (секунды)
            duration = 0.0
            if board.end_time and board.start_time:
                duration = (board.end_time - board.start_time).total_seconds()
            cut_plan = await self.board_repo.get_cut_plan_for_board(board.id)
            cut_plan_dto = CuttingPlanDTO(
                board_id=str(cut_plan.board_id),
                segments=cut_plan.segments,
                total_revenue=cut_plan.total_revenue,
                algorithm=cut_plan.algorithm
            ) if cut_plan else None
            frontend_boards.append(
                FrontendBoardDTO(
                    board_id=str(board.id),
                    cutting_plan=cut_plan_dto,
                    quality=board.quality or "C",
                    defects=defect_dtos,
                    timestamp=board.created_at,
                    processing_duration=duration,
                    total_length_mm=board.total_length_mm
                )
            )

        return {
            "boards": [b.model_dump() for b in frontend_boards],
            "total": total,
        }

    async def get_metrics_for_frontend(self) -> Dict[str, Any]:
        metrics = await self.board_repo.get_metrics()
        return {
            "totalBoards": metrics["totalBoards"],
            "avgProcessingDuration": metrics["avgProcessingDuration"],
            "qualityDistribution": QualityDistributionDTO(
                A=metrics["qualityDistribution"]["A"],
                B=metrics["qualityDistribution"]["B"],
                C=metrics["qualityDistribution"]["C"],
                D=metrics["qualityDistribution"]["D"],
            ).model_dump(),
            "totalDefects": metrics["totalDefects"],
            "topDefects": [TopDefectDTO(type=t["type"], count=t["count"]).model_dump() for t in metrics["topDefects"]],
            "boardsByHour": [BoardsByHourDTO(hour=b["hour"], count=b["count"]).model_dump() for b in metrics["boardsByHour"]],
        }

    @staticmethod
    def _get_severity(defect_type: str) -> str:
        high = ["broken_board", "missed_knot"]
        medium = ["dead_knot", "resin_pocket"]
        if defect_type in high:
            return "critical"
        if defect_type in medium:
            return "medium"
        return "low"

    async def get_one_board(self, board_id: UUID) -> Board:
        board = await self.board_repo.get_by_id(board_id)
        if not board:
            raise RuntimeError("Board not found")
        return board


# Dependency для получения сервиса
async def get_statistics_service(session: AsyncSession = Depends(get_async_session)) -> StatisticsService:
    return StatisticsService(session)

StatisticsServiceDep = Annotated[StatisticsService, Depends(get_statistics_service)]