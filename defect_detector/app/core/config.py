import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Настройки приложения."""
    # Общие
    APP_NAME: str = "CV Defect Service"
    DEBUG: bool = False

    # Пути к моделям
    STATE_MODEL_PATH: Path = Path("models/state_classifier.pth")
    DEFECT_MODEL_PATH: Path = Path("models/best.pt")

    # Параметры обработки
    FPS_TARGET: int = 30
    STATE_WINDOW_SIZE: int = 16          # кол-во кадров для определения BOARD/GAP
    STATE_SMOOTHING: int = 5             # размер буфера сглаживания
    DEFECT_INFERENCE_EVERY_N_FRAMES: int = 28   # частота детекции дефектов
    STATE_INFERENCE_EVERY_N_FRAMES: int = 8     # частота определения состояния

    # Конвертация координат (мм)
    CONVEYOR_SPEED_MM_PER_SEC: float = 1000.0   # скорость движения доски (настраивается)
    PX_TO_MM_WIDTH_FACTOR: float = 0.5          # для перевода ширины (зависит от камеры)

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PUBSUB_CHANNEL: str = "cv_events"

    # Сохранение изображений дефектов
    SAVE_DEFECT_IMAGES: bool = True
    DEFECT_IMAGES_ROOT: Path = Path("defects")

    # RTSP настройки
    RTSP_RECONNECT_INTERVAL_SEC: int = 5

    class Config:
        env_file = ".env"

settings = Settings()