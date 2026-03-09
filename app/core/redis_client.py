import redis.asyncio as redis
from app.config import settings

class RedisClient:
    def __init__(self):
        self.pool = None
        self.client = None

    async def connect(self):
        # Redis Connection Pool for high availability and performance
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=100
        )
        self.client = redis.Redis(connection_pool=self.pool)

    async def disconnect(self):
        if self.pool:
            await self.pool.disconnect()

    async def publish(self, channel: str, message: str):
        await self.client.publish(channel, message)

    def get_pubsub(self):
        return self.client.pubsub()

redis_client = RedisClient()
