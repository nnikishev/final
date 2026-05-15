from ultralytics import YOLO
from pathlib import Path
from typing import List, Dict, Any
import cv2

class DefectDetector:
    """
    Детектор дефектов на основе предобученной YOLO модели.
    """
    CLASS_NAMES = {
        0: 'alive_knot',
        1: 'dead_knot',
        2: 'missed_knot',
        3: 'resin_pocket',
        4: 'broken_board'
    }

    def __init__(self, model_path: Path, conf_threshold: float = 0.4):
        """
        :param model_path: путь к best.pt
        :param conf_threshold: порог уверенности
        """
        self.model = YOLO(str(model_path))
        self.conf_threshold = conf_threshold

    def detect(self, frame: cv2.typing.MatLike) -> List[Dict[str, Any]]:
        """
        Выполняет детекцию на одном кадре.
        Возвращает список дефектов с полями:
          - type: str
          - class_id: int
          - confidence: float
          - bbox: [x1, y1, x2, y2]
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        defects = []
        if results[0].boxes is None:
            return defects

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            defect_type = self.CLASS_NAMES.get(class_id, 'unknown')
            if defect_type == 'unknown':
                continue
            defects.append({
                'type': defect_type,
                'class_id': class_id,
                'confidence': conf,
                'bbox': [x1, y1, x2, y2]
            })
        return defects