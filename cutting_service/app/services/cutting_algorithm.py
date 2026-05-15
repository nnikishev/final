import math
from typing import List, Dict, Any
from app.services.price_service import PriceService
from app.core.config import settings

class GreedyCutter:
    def __init__(self, price_service: PriceService):
        self.price_service = price_service

    async def optimize(self, board_id: str, total_length_mm: float, defects: List[Dict[str, Any]]):
        """
        Жадный алгоритм раскроя с учётом дефектов.
        Если total_length_mm <= 0, используется значение по умолчанию 6000 мм.
        Всегда создаётся хотя бы один сегмент, чтобы алгоритм мог вырезать заготовки.
        """
        # 1. Нормализация длины доски
        if total_length_mm is None or total_length_mm <= 0:
            total_length_mm = 6000.0  # 6 метров по умолчанию
            print(f"WARNING: board {board_id} has invalid total_length_mm, set to {total_length_mm} mm")

        # 2. Построение сегментов с учётом дефектов
        if not defects:
            segments = [{"from_mm": 0, "to_mm": total_length_mm, "max_grade": 0}]
        else:
            margin = 50  # мм, зона влияния дефекта
            events = []
            for d in defects:
                # Извлекаем позицию дефекта в миллиметрах
                pos = d.get("position_from_start_mm")
                if pos is None:
                    pos = d.get("position_mm")
                    if isinstance(pos, dict):
                        pos = pos.get("from_start_mm")
                if pos is None:
                    continue
                start = max(0, pos - margin)
                end = min(total_length_mm, pos + margin)
                events.append((start, 'start', d))
                events.append((end, 'end', d))
            events.sort(key=lambda x: x[0])

            segments = []
            active_defects = []
            last_pos = 0
            for coord, typ, defect in events:
                if coord > last_pos and last_pos < total_length_mm:
                    grade = self._calculate_segment_grade(active_defects)
                    if grade <= settings.MAX_GRADE:
                        segments.append({
                            "from_mm": last_pos,
                            "to_mm": min(coord, total_length_mm),
                            "max_grade": grade
                        })
                last_pos = coord
                if typ == 'start':
                    active_defects.append(defect)
                else:
                    active_defects = [d for d in active_defects if d is not defect]
            if last_pos < total_length_mm:
                grade = self._calculate_segment_grade(active_defects)
                if grade <= settings.MAX_GRADE:
                    segments.append({
                        "from_mm": last_pos,
                        "to_mm": total_length_mm,
                        "max_grade": grade
                    })

        # 3. Гарантия: если сегментов нет (например, все зоны дефектов перекрыли всю доску), создаём один сегмент
        if not segments:
            segments = [{"from_mm": 0, "to_mm": total_length_mm, "max_grade": 0}]
            print(f"WARNING: no segments created for board {board_id}, using full board as one segment")

        # 4. Получение и сортировка заготовок по цене за мм
        all_prices = await self.price_service.get_all_prices()
        items = []
        for p in all_prices:
            length_mm = p.length_m * settings.M_TO_MM
            if length_mm <= 0 or length_mm > total_length_mm:
                continue
            price_per_mm = p.price / length_mm
            items.append({
                "length_m": p.length_m,
                "length_mm": length_mm,
                "grade": p.grade,
                "price": p.price,
                "price_per_mm": price_per_mm
            })
        items.sort(key=lambda x: x["price_per_mm"], reverse=True)

        if not items:
            # Если нет подходящих заготовок (пустой прайс-лист или все длиннее доски)
            return {
                "board_id": str(board_id),
                "segments": [],
                "total_revenue": 0,
                "algorithm": "greedy_with_rules",
                "error": "No price items available"
            }

        # 5. Жадный раскрой
        used_segments = []
        remaining_segments = [seg.copy() for seg in segments]
        for item in items:
            for seg in remaining_segments[:]:
                seg_len = seg["to_mm"] - seg["from_mm"]
                if seg_len >= item["length_mm"] and seg["max_grade"] <= item["grade"]:
                    cut = {
                        "from_mm": seg["from_mm"],
                        "to_mm": seg["from_mm"] + item["length_mm"],
                        "grade": item["grade"],
                        "length_m": item["length_m"],
                        "price": item["price"]
                    }
                    used_segments.append(cut)
                    seg["from_mm"] += item["length_mm"]
                    if seg["from_mm"] >= seg["to_mm"]:
                        remaining_segments.remove(seg)
                    break  # переходим к следующей заготовке

        total_revenue = sum(s["price"] for s in used_segments)
        return {
            "board_id": str(board_id),
            "segments": used_segments,
            "total_revenue": total_revenue,
            "algorithm": "greedy_with_rules"
        }

    def _calculate_segment_grade(self, defects: List[Dict]) -> int:
        """
        Вычисляет максимально допустимый сорт для отрезка по правилам.
        Возвращает целое число: 0 - A, 1 - B, 2 - C, 3 - D.
        """
        # 1. Битые доски -> D
        if any(d.get("defect_type") == "broken_board" for d in defects):
            return 3
        # 2. Смоляные карманы -> не выше C
        if any(d.get("defect_type") == "resin_pocket" for d in defects):
            return 2
        # 3. Сучки: если их более 3 в зоне (margin) -> C, иначе B (если есть хотя бы один)
        knot_count = sum(1 for d in defects if d.get("defect_type") in ["alive_knot", "dead_knot", "missed_knot"])
        if knot_count > 3:
            return 2  # C
        if knot_count > 0:
            return 1  # B
        return 0  # A