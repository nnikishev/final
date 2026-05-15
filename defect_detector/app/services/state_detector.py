import cv2
import torch
import numpy as np
from typing import List, Deque, Optional
from collections import deque
from pathlib import Path

from app.services.state_classifier import StateClassifier  # наш новый класс

class StateDetector:
    """
    Детектор границ доски: использует 3D CNN классификатор состояний (BOARD / GAP)
    на основе накопленного окна кадров.
    """
    def __init__(self, model_path: Path, window_size: int = 16,
                 smoothing_buffer: int = 3, inference_every_n: int = 2):
        """
        :param model_path: путь к state_classifier.pth
        :param window_size: сколько кадров подаётся на вход модели (временная глубина)
        :param smoothing_buffer: размер буфера для сглаживания решений
        :param inference_every_n: запуск модели каждые N кадров
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = StateClassifier(num_classes=2)
        state_dict = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        self.window_size = window_size
        self.smoothing_buf = smoothing_buffer
        self.inference_every_n = inference_every_n

        self.frame_buffer: Deque[np.ndarray] = deque(maxlen=window_size)
        self.state_buffer: Deque[str] = deque(maxlen=smoothing_buffer)

        self.last_state: Optional[str] = None

    def _preprocess_frames(self, frames: List[np.ndarray]) -> torch.Tensor:
        """
        Преобразует список кадров (H,W,C) в нормализованный тензор (1, C, T, H, W).
        Кадры предполагаются размером 224x224, значения float32 в диапазоне [0,1].
        """
        clip = np.array(frames, dtype=np.float32)          # (T, H, W, C)
        clip = torch.FloatTensor(clip).permute(3, 0, 1, 2)  # (C, T, H, W)
        clip = clip.unsqueeze(0)                           # (1, C, T, H, W)
        return clip.to(self.device)

    def predict_state(self, frames: List[np.ndarray]) -> str:
        """Возвращает 'BOARD' или 'GAP' для окна кадров."""
        with torch.no_grad():
            tensor = self._preprocess_frames(frames)
            logits = self.model(tensor)          # (1, num_classes)
            pred = torch.argmax(logits, dim=1).item()
        return 'BOARD' if pred == 0 else 'GAP'

    def process_frame(self, frame: np.ndarray, frame_idx: int,
                      fps: float) -> Optional[dict]:
        """
        Обрабатывает очередной кадр. Если накоплено достаточно и пришло время
        инференса, предсказывает состояние и возвращает событие изменения
        (board_start / board_end) или None.
        """
        # Приводим кадр к размеру 224x224 и нормируем
        frame_resized = cv2.resize(frame, (224, 224))
        frame_norm = frame_resized / 255.0
        self.frame_buffer.append(frame_norm)

        event = None
        if (len(self.frame_buffer) == self.window_size and
                frame_idx % self.inference_every_n == 0):
            current_state = self.predict_state(list(self.frame_buffer))
            self.state_buffer.append(current_state)

            if len(self.state_buffer) == self.smoothing_buf:
                # Сглаженное состояние – наиболее частое в буфере
                smooth_state = max(set(self.state_buffer), key=self.state_buffer.count)

                if self.last_state is None:
                    self.last_state = smooth_state

                # GAP -> BOARD = начало доски
                if self.last_state == 'GAP' and smooth_state == 'BOARD':
                    event = {
                        'type': 'board_start',
                        'board_id': None,        # будет задан выше
                        'start_frame': frame_idx,
                        'start_time_sec': frame_idx / fps
                    }
                # BOARD -> GAP = конец доски
                elif self.last_state == 'BOARD' and smooth_state == 'GAP':
                    event = {
                        'type': 'board_end',
                        'board_id': None,
                        'end_frame': frame_idx,
                        'end_time_sec': frame_idx / fps
                    }

                self.last_state = smooth_state

        return event