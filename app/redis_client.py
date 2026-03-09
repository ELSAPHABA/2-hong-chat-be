import redis.asyncio as redis
from app.config import settings

class RedisClient:
    def __init__(self):
        self.redis = None

    async def connect(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def publish(self, channel: str, message: str):
        await self.redis.publish(channel, message)

    def get_pubsub(self):
        return self.redis.pubsub()

redis_client = RedisClient()
