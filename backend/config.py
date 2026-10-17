from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./hirepath.db"
    
    # Groq LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # GitHub
    GITHUB_TOKEN: str = ""
    
    # Gmail / SMTP
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    
    # Google Calendar
    GOOGLE_CREDENTIALS_JSON: str = ""
    
    # Slack
    SLACK_WEBHOOK_URL: str = ""
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Stale threshold (days)
    STALE_THRESHOLD_DAYS: int = 3

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
