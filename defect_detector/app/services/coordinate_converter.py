import math

class CoordinateConverter:
    """
    Преобразует позицию дефекта из системы координат кадра (пиксели)
    в продольные и поперечные координаты на доске (мм).
    """
    def __init__(self, speed_mm_per_sec: float, px_to_mm_width_factor: float):
        """
        :param speed_mm_per_sec: скорость движения доски (мм/с)
        :param px_to_mm_width_factor: перевод пикселей в мм по ширине (зависит от камеры)
        """
        self.speed = speed_mm_per_sec
        self.width_factor = px_to_mm_width_factor

    def convert(self, frame_idx: int, board_start_frame: int, fps: float,
                bbox_center_x: int, bbox_center_y: int) -> dict:
        """
        Возвращает словарь с ключами 'from_start_mm' и 'width_mm'.

        :param frame_idx: текущий индекс кадра
        :param board_start_frame: кадр, на котором доска началась
        :param fps: кадров в секунду
        :param bbox_center_x: центр bounding box по X (пиксели, продольная ось)
        :param bbox_center_y: центр bounding box по Y (пиксели, поперечная ось)
        """
        elapsed_time = (frame_idx - board_start_frame) / fps
        length_mm = elapsed_time * self.speed
        width_mm = bbox_center_y * self.width_factor   # предположение: центр дефекта по ширине
        return {
            "from_start_mm": round(length_mm, 2),
            "width_mm": round(width_mm, 2)
        }