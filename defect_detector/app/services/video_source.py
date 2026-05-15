import cv2
import time
from abc import ABC, abstractmethod
from typing import Tuple, Optional

class VideoSource(ABC):
    """Базовый класс для источника видеокадров."""
    @abstractmethod
    def read(self) -> Tuple[bool, Optional[cv2.typing.MatLike]]:
        """Возвращает (ret, frame)."""
        pass

    @abstractmethod
    def release(self):
        """Освобождает ресурсы."""
        pass

class FileVideoSource(VideoSource):
    """Источник из видеофайла."""
    def __init__(self, path: str):
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {path}")

    def read(self) -> Tuple[bool, Optional[cv2.typing.MatLike]]:
        return self.cap.read()

    def release(self):
        self.cap.release()

class RTSPSource(VideoSource):
    """Источник из RTSP-камеры с автоматическим переподключением."""
    def __init__(self, url: str, reconnect_interval_sec: int = 5):
        self.url = url
        self.reconnect_interval = reconnect_interval_sec
        self.cap = None
        self._connect()

    def _connect(self):
        self.cap = cv2.VideoCapture(self.url)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open RTSP stream: {self.url}")

    def read(self) -> Tuple[bool, Optional[cv2.typing.MatLike]]:
        if self.cap is None or not self.cap.isOpened():
            time.sleep(self.reconnect_interval)
            self._connect()
        ret, frame = self.cap.read()
        if not ret:
            # Возможно временная потеря, переподключаемся в следующий раз
            self.release()
            time.sleep(self.reconnect_interval)
            self._connect()
            ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None