from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime, func, Enum, Text
from app.config.database import Base
import enum


class OrderType(str, enum.Enum):
    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"


class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    PAYMENT_VERIFIED = "PAYMENT_VERIFIED"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    READY = "READY"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    PICKED_UP = "PICKED_UP"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)
    order_type = Column(String(20), default="DELIVERY")  # DELIVERY or PICKUP
    delivery_address = Column(Text, nullable=True)
    delivery_lat = Column(DECIMAL(10, 7), nullable=True)
    delivery_lng = Column(DECIMAL(10, 7), nullable=True)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    delivery_fee = Column(DECIMAL(10, 2), default=0)
    discount = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(30), default="NEW")
    delivery_otp = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
