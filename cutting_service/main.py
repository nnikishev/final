from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager
from app.routers import boards, cut_plans, prices
from app.services.redis_listener import RedisListener
from app.services.board_aggregator import BoardAggregator
from app.services.price_service import PriceService
from app.core.database import AsyncSessionLocal
from app.core.config import settings

from fastapi.middleware.cors import CORSMiddleware

# Глобальные переменные для фоновых задач
background_tasks = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация сервисов
    async with AsyncSessionLocal() as db:
        price_service = PriceService(db)
        aggregator = BoardAggregator(price_service)
        listener = RedisListener(aggregator)
        # Запускаем фоновую задачу прослушки Redis
        task = asyncio.create_task(listener.listen())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        yield
        # При завершении отменяем задачу
        for t in background_tasks:
            t.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)

app = FastAPI(title="Cutting Optimization Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["0.0.0.0", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(boards.router)
app.include_router(cut_plans.router)
app.include_router(prices.router)

@app.get("/health")
async def health():
    return {"status": "ok"}