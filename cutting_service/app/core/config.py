from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Cutting Optimization Service"
    DEBUG: bool = False

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cutting_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_CHANNEL: str = "cv_events"

    # Алгоритм
    # Список допустимых длин заготовок в метрах (будет конвертироваться в мм)
    ALLOWED_LENGTHS_M: list = [1.0, 1.5, 2.0, 3.0, 6.0]
    # Коэффициент перевода метров в миллиметры
    M_TO_MM: int = 1000

    # Справочник соответствия дефектов и сортов (чем ниже номер сорта, тем лучше)
    DEFECT_MARGIN_MM: int = 3  # или 20, по желанию
    DEFECT_PENALTY: dict = {
        'alive_knot': 0.0,
        'dead_knot': 0.5,
        'missed_knot': 1.0,
        'resin_pocket': 0.5,
        'broken_board': 2.0,
    }
    MAX_GRADE: int = 3

    # Цены по умолчанию (руб/шт) для комбинаций длина_м × сорт
    # Позже будут загружаться из БД, здесь для инициализации
    DEFAULT_PRICES: dict = {
        (1.0, 0): 150,
        (1.0, 1): 120,
        (1.0, 2): 90,
        (1.0, 3): 50,
        (1.5, 0): 220,
        (1.5, 1): 180,
        (1.5, 2): 130,
        (1.5, 3): 70,
        (2.0, 0): 290,
        (2.0, 1): 230,
        (2.0, 2): 160,
        (2.0, 3): 90,
        (3.0, 0): 430,
        (3.0, 1): 340,
        (3.0, 2): 240,
        (3.0, 3): 130,
        (6.0, 0): 850,
        (6.0, 1): 670,
        (6.0, 2): 480,
        (6.0, 3): 260,
    }

    class Config:
        env_file = ".env"

settings = Settings()