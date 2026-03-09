from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, GetJsonSchemaHandler, GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Optional, Any, List
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(lambda v: ObjectId(v)),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
        )

class MessageModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    room_id: str
    sender_id: str
    message_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "room_id": "room1",
                "sender_id": "user123",
                "message_text": "Hello, K8s!",
            }
        }
    )

class MessageResponse(BaseModel):
    id: str
    room_id: str
    sender_id: str
    message_text: str
    timestamp: datetime
