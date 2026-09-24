"""
Application settings loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path

# .env lives one level up from backend/
_project_dir = Path(__file__).resolve().parents[2]
_env_file = _project_dir.parent / ".env"


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./tikkamasala.db"

    # Security
    JWT_SECRET: str = "change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Admin Seed
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_EMAIL: str = "admin@tikkamasala.com"

    # Shop Location
    SHOP_LATITUDE: float = 13.0827
    SHOP_LONGITUDE: float = 80.2707
    DELIVERY_RADIUS_KM: float = 3.0

    # Delivery
    DELIVERY_CHARGE: float = 30.0

    # Razorpay
    RAZORPAY_KEY_ID: str = "rzp_test_demo"
    RAZORPAY_KEY_SECRET: str = "demo_secret"
    RAZORPAY_WEBHOOK_SECRET: str = "demo_webhook_secret"

    # SMS
    SMS_PROVIDER: str = "mock"
    SMS_API_KEY: str = ""
    SMS_SENDER_ID: str = "TIKKA"

    # Demo Mode
    DEMO_MODE: bool = True

    # AWS
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "tikkamasala-images"
    USE_S3: bool = False

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5500"
    CORS_ORIGINS: str = ""
    CORS_ORIGINS_LIST: List[str] = []

    class Config:
        env_file = str(_env_file)
        extra = "ignore"


settings = Settings()

if settings.CORS_ORIGINS:
    settings.CORS_ORIGINS_LIST = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
else:
    settings.CORS_ORIGINS_LIST = [settings.FRONTEND_URL, "http://127.0.0.1:5500", "http://localhost:5500"]

# Resolve relative SQLite URLs from the backend directory, independent of the
# directory used to launch Uvicorn.
if settings.DATABASE_URL.startswith("sqlite") and "///" in settings.DATABASE_URL:
    _sqlite_path = settings.DATABASE_URL.split("///", 1)[1]
    if not Path(_sqlite_path).is_absolute():
        settings.DATABASE_URL = f"sqlite+aiosqlite:///{_project_dir / _sqlite_path}"
