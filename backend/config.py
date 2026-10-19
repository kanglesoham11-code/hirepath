from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./hirepath.db"
    
    # Groq LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    
    # GitHub
    GITHUB_TOKEN: str = ""
    
    # Gmail / SMTP
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    
    # Google Calendar
    GOOGLE_CREDENTIALS_JSON: str = ""
    
    # Slack
    SLACK_WEBHOOK_URL: str = ""
    
    # Auth — required on all write endpoints and used to sign privacy links
    API_SECRET_KEY: str = ""

    # Candidate privacy links expire after this many days.
    PRIVACY_TOKEN_TTL_DAYS: int = 30
    
    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Stale threshold (days)
    STALE_THRESHOLD_DAYS: int = 3

    class Config:
        import os
        env_file = (
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
            ".env",
        )
        extra = "allow"

settings = Settings()
