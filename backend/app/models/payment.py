from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime, func
from app.config.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    razorpay_order_id = Column(String(100), unique=True, nullable=False, index=True)
    razorpay_payment_id = Column(String(100), unique=True, nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(5), default="INR")
    status = Column(String(20), default="PENDING")  # PENDING | PAID | FAILED | REFUNDED
    # No card/CVV/UPI data stored — Razorpay handles that
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
