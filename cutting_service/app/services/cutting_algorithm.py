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
        Сортировка заготовок: сначала самый высокий сорт (0 = Экстра), внутри – по убыванию длины.
        """
        # 1. Нормализация длины доски
        if total_length_mm is None or total_length_mm <= 0:
            total_length_mm = 6000.0
            print(f"WARNING: board {board_id} has invalid total_length_mm, set to {total_length_mm} mm")

        # 2. Построение сегментов с учётом дефектов (зона влияния 50 мм)
        if not defects:
            segments = [{"from_mm": 0, "to_mm": total_length_mm, "max_grade": 0}]
        else:
            margin = 50  # мм
            events = []
            for d in defects:
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

        # 4. Получение всех доступных заготовок и их сортировка по классу (сорт → длина ↓)
        all_prices = await self.price_service.get_all_prices()
        items = []
        for p in all_prices:
            length_mm = p.length_m * settings.M_TO_MM
            if length_mm <= 0 or length_mm > total_length_mm:
                continue
            items.append({
                "length_m": p.length_m,
                "length_mm": length_mm,
                "grade": p.grade,      # 0=Экстра, 1=А, 2=В, 3=С
                "price": p.price
            })
        # Сортировка: сначала лучший сорт (меньше число), внутри – самая длинная заготовка
        items.sort(key=lambda x: (x["grade"], -x["length_mm"]))

        if not items:
            return {
                "board_id": str(board_id),
                "segments": [],
                "total_revenue": 0,
                "algorithm": "greedy_with_rules",
                "error": "No price items available"
            }

        # 5. Жадный раскрой (перебираем заготовки в отсортированном порядке)
        used_segments = []
        remaining_segments = [seg.copy() for seg in segments]
        for item in items:
            for seg in remaining_segments[:]:
                seg_len = seg["to_mm"] - seg["from_mm"]
                # Сегмент должен быть не хуже требуемого сорта (max_grade <= grade заготовки)
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
        Вычисляет сорт отрезка лицевой стороны по правилам задания.
        Возвращает:
            0 – Экстра (идеально)
            1 – А (только живые светлые сучки)
            2 – В (тёмные сучки, смоляные кармашки, сколы, сердцевина)
            3 – С (выпавшие сучки, трещины, синева, сквозные отверстия)
        """
        # Дефекты, которые сразу дают сорт С
        grade_c_defects = {"missed_knot", "broken_board"}
        # Дефекты, дающие сорт В (при отсутствии дефектов С)
        grade_b_defects = {"dead_knot", "resin_pocket",}
        # Дефекты, дающие сорт А (только живые сучки, при отсутствии более серьёзных)
        grade_a_defects = {"alive_knot"}

        max_grade = 0  # пока Экстра

        for d in defects:
            defect_type = d.get("defect_type")
            if defect_type in grade_c_defects:
                return 3  # сразу С, так как это самый низкий сорт
            elif defect_type in grade_b_defects:
                max_grade = max(max_grade, 2)
            elif defect_type in grade_a_defects:
                max_grade = max(max_grade, 1)

        return max_grade