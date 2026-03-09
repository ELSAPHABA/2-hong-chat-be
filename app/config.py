from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "chat_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "SECRET"
    
    class Config:
        env_file = ".env"

settings = Settings()
