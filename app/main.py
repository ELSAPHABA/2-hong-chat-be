import asyncio
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database import db
from app.core.redis_client import redis_client
from app.core.connection_manager import manager
from app.services.chat_service import chat_service
from app.models.schemas import MessageResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB & Redis 커넥션 풀 초기화
    await db.connect()
    await redis_client.connect()
    yield
    # Shutdown: 연결 해제
    await db.disconnect()
    await redis_client.disconnect()

app = FastAPI(
    title="K8s Distributed Chat Server",
    description="State Sharing via Redis Pub/Sub",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/messages/{room_id}", response_model=List[MessageResponse])
async def get_chat_history(room_id: str):
    """최근 50개 메시지 조회 API"""
    messages = await db.db["messages"].find(
        {"room_id": room_id}
    ).sort("timestamp", -1).limit(50).to_list(length=50)
    
    return [
        MessageResponse(
            id=str(msg["_id"]),
            room_id=msg["room_id"],
            sender_id=msg["sender_id"],
            message_text=msg["message_text"],
            timestamp=msg["timestamp"]
        ) for msg in reversed(messages)
    ]

@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    """
    WebSocket 연결:
    1. 연결 수립 및 Local Manager에 등록
    2. Redis Pub/Sub을 통한 메시지 수신 (Manager 내부 Task)
    3. 클라이언트 메시지 수신 시 Redis 발행 및 DB 저장
    """
    await manager.connect(websocket, room_id, user_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            # 1. Redis 발행 (모든 Pod로 전파하여 실시간 동기화)
            await chat_service.publish_message(room_id, user_id, data)
            
            # 2. DB 저장 (비동기)
            asyncio.create_task(chat_service.save_message(room_id, user_id, data))
            
    except WebSocketDisconnect:
        await manager.disconnect(room_id, user_id)
    except Exception as e:
        print(f"WebSocket error for {user_id}: {e}")
        await manager.disconnect(room_id, user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
