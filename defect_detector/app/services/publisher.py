import json
import redis.asyncio as redis
from typing import Any
from app.models.schemas import BoardStartEvent, BoardEndEvent, DefectEvent

class RedisPublisher:
    """Асинхронный издатель событий в Redis."""
    def __init__(self, host: str, port: int, channel: str):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
        self.channel = channel

    async def publish(self, event: Any) -> None:
        """Публикует событие (Pydantic модель) в канал."""
        if hasattr(event, "model_dump_json"):
            message = event.model_dump_json()
        else:
            message = json.dumps(event)
        await self.redis.publish(self.channel, message)

    async def close(self):
        await self.redis.close()