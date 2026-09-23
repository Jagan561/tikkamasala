"""
Application settings loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# .env lives one level up from backend/
_env_file = Path(__file__).resolve().parents[3] / ".env"


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

    class Config:
        env_file = str(_env_file)
        extra = "ignore"


settings = Settings()
