from functools import lru_cache
from app.services.publisher import RedisPublisher
from app.services.state_detector import StateDetector
from app.services.defect_detector import DefectDetector
from app.services.coordinate_converter import CoordinateConverter
from app.core.config import settings

@lru_cache()
def get_publisher() -> RedisPublisher:
    """Возвращает экземпляр издателя событий Redis."""
    return RedisPublisher(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        channel=settings.REDIS_PUBSUB_CHANNEL
    )

@lru_cache()
def get_state_detector() -> StateDetector:
    """Возвращает детектор состояния (BOARD/GAP)."""
    return StateDetector(
        model_path=settings.STATE_MODEL_PATH,
        window_size=settings.STATE_WINDOW_SIZE,
        smoothing_buffer=settings.STATE_SMOOTHING,
        inference_every_n=settings.STATE_INFERENCE_EVERY_N_FRAMES
    )

@lru_cache()
def get_defect_detector() -> DefectDetector:
    """Возвращает детектор дефектов YOLO."""
    return DefectDetector(model_path=settings.DEFECT_MODEL_PATH)

@lru_cache()
def get_coordinate_converter() -> CoordinateConverter:
    """Возвращает конвертер пикселей в миллиметры."""
    return CoordinateConverter(
        speed_mm_per_sec=settings.CONVEYOR_SPEED_MM_PER_SEC,
        px_to_mm_width_factor=settings.PX_TO_MM_WIDTH_FACTOR
    )