import asyncio
import json
import redis.asyncio as redis
from app.core.config import settings
from app.services.board_aggregator import BoardAggregator

class RedisListener:
    def __init__(self, aggregator: BoardAggregator):
        self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        self.aggregator = aggregator
        self.channel = settings.REDIS_CHANNEL

    async def listen(self):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel)
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    await self.aggregator.process_event(data)
                except Exception as e:
                    print(f"Error processing event: {e}")