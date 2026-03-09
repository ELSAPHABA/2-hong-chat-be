import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from app.core.redis_client import redis_client

class ConnectionManager:
    """
    K8s Distributed State Sharing:
    각 Pod는 자신에게 연결된 WebSocket 세션만 관리(local_connections).
    메시지는 Redis Pub/Sub을 통해 모든 Pod에 전파되며, 
    각 Pod는 해당 유저가 자신에게 붙어있는지 확인 후 메시지를 전달함.
    """
    def __init__(self):
        # {room_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.room_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            # 해당 방의 Redis 구독 태스크가 없으면 생성
            self.room_tasks[room_id] = asyncio.create_task(self._redis_listener(room_id))
        
        self.active_connections[room_id][user_id] = websocket

    async def disconnect(self, room_id: str, user_id: str):
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]
            
            # 방에 연결된 유저가 더 이상 없으면 Redis 구독 태스크 종료
            if not self.active_connections[room_id]:
                self.room_tasks[room_id].cancel()
                del self.room_tasks[room_id]
                del self.active_connections[room_id]

    async def _redis_listener(self, room_id: str):
        """
        Redis Pub/Sub을 통해 전파된 메시지를 수신하여 
        이 Pod에 연결된 해당 룸 유저들에게 실시간 전달.
        """
        channel_name = f"room_{room_id}"
        pubsub = redis_client.get_pubsub()
        await pubsub.subscribe(channel_name)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    # 이 Pod에 해당 방 유저들이 연결되어 있는지 확인
                    if room_id in self.active_connections:
                        # 방 안의 모든 활성 세션에 메시지 전달 (State Sharing)
                        for websocket in self.active_connections[room_id].values():
                            await websocket.send_json(data)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()
        except Exception as e:
            print(f"Error in Redis listener for room {room_id}: {e}")

manager = ConnectionManager()
