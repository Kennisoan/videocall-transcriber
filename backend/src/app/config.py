import os
from dotenv import load_dotenv

load_dotenv()  # This will load from .env in local dev, or from .env.prod in production


class Settings:
    PROJECT_NAME = "Video Call Transcriber"
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
    ENV = os.getenv("ENV", "dev")  # 'dev' or 'prod'


settings = Settings()
