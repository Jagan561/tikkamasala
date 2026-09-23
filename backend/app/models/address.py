from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, func
from app.config.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    label = Column(String(50), default="Home")  # Home / Work / Other
    address = Column(String(500), nullable=False)
    latitude = Column(DECIMAL(10, 7), nullable=True)
    longitude = Column(DECIMAL(10, 7), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
