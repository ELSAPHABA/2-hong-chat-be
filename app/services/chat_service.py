import json
from datetime import datetime
from app.core.redis_client import redis_client
from app.database import db

class ChatService:
    async def publish_message(self, room_id: str, sender_id: str, message_text: str):
        message_data = {
            "room_id": room_id,
            "sender_id": sender_id,
            "message_text": message_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        channel_name = f"room_{room_id}"
        # Redis에 메시지 발행 (모든 Pod로 전파)
        await redis_client.publish(channel_name, json.dumps(message_data))

    async def save_message(self, room_id: str, sender_id: str, message_text: str):
        message_doc = {
            "room_id": room_id,
            "sender_id": sender_id,
            "message_text": message_text,
            "timestamp": datetime.utcnow()
        }
        # MongoDB에 영속화
        await db.db["messages"].insert_one(message_doc)

chat_service = ChatService()
