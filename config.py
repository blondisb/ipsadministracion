from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_API_KEY: str
    GROQ_API_KEY: str
    AI_MODEL_NAME: str
    
    SECRET_KEY: str 
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    
    ALLOWED_ORIGINS: List[str]
    
    class Config:
        env_file = ".env"

settings = Settings()