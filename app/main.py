import json
import asyncio
from datetime import datetime
from typing import List

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.database import db
from app.redis_client import redis_client
from app.models import MessageModel
from app.schemas import MessageResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    await redis_client.connect()
    yield
    # Shutdown
    await db.disconnect()
    await redis_client.disconnect()

app = FastAPI(title="Real-time 1:1 Chat Server", lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API to load last 50 messages
@app.get("/messages/{room_id}", response_model=List[MessageResponse])
async def get_messages(room_id: str):
    print(f"Loading messages for room: {room_id}")
    messages = await db.db["messages"].find(
        {"room_id": room_id}
    ).sort("timestamp", -1).limit(50).to_list(length=50)
    
    print(f"Found {len(messages)} messages")
    # Reverse to show in chronological order
    return [
        MessageResponse(
            id=str(msg["_id"]),
            room_id=msg["room_id"],
            sender_id=msg["sender_id"],
            message_text=msg["message_text"],
            timestamp=msg["timestamp"]
        ) for msg in reversed(messages)
    ]

# WebSocket Handler
@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    await websocket.accept()
    
    channel_name = f"room_{room_id}"
    pubsub = redis_client.get_pubsub()
    await pubsub.subscribe(channel_name)
    
    async def redis_listener():
        """Listen to Redis messages and send to WebSocket."""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
        except Exception as e:
            print(f"Redis listener error: {e}")

    # Start redis listener as a background task
    listener_task = asyncio.create_task(redis_listener())
    
    try:
        while True:
            # Receive message from WebSocket client
            data = await websocket.receive_text()
            message_data = {
                "room_id": room_id,
                "sender_id": user_id,
                "message_text": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 1. Publish to Redis (Broadcast)
            await redis_client.publish(channel_name, json.dumps(message_data))
            
            # 2. Persist to MongoDB (Async)
            try:
                await save_message_to_db(room_id, user_id, data)
            except Exception as e:
                print(f"Failed to save message to MongoDB: {e}")
            
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected from room {room_id}")
    finally:
        listener_task.cancel()
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()

async def save_message_to_db(room_id: str, sender_id: str, message_text: str):
    """Save chat message to MongoDB."""
    try:
        message_doc = {
            "room_id": room_id,
            "sender_id": sender_id,
            "message_text": message_text,
            "timestamp": datetime.utcnow()
        }
        await db.db["messages"].insert_one(message_doc)
    except Exception as e:
        # Re-raise so the caller can catch it and print context
        raise e

def main():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
