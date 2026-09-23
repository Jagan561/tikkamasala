from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.config.database import Base


class OTP(Base):
    __tablename__ = "otp"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String(15), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    purpose = Column(String(30), nullable=False)  # REGISTRATION | LOGIN | DELIVERY
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
