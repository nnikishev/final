"""
Главный модуль FastAPI приложения.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import camera, test

app = FastAPI(
    title="CV Defect Detection Service",
    description="""
    Сервис компьютерного зрения для обнаружения дефектов пиломатериалов.
    - Определяет начало/конец доски на конвейере (BOARD/GAP)
    - Детектирует 5 типов дефектов (сучки, трещины, смоляные карманы и т.д.)
    - Публикует события в Redis Pub/Sub для модуля раскроя
    """,
    version="1.0.0",
    contact={
        "name": "Разработчик",
        "email": "nikolay.nikishev@gmail.com",
    },
    license_info={
        "name": "Proprietary",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(camera.router)
app.include_router(test.router)

@app.on_event("shutdown")
async def shutdown_event():
    """Закрывает активные подключения при остановке сервиса."""
    from app.routers.camera import _active_processor
    if _active_processor:
        await _active_processor.stop()