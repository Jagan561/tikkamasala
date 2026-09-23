from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text
from app.config.database import Base


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    changed_by = Column(String(50), nullable=True)   # "admin" | "system" | "customer"
    changed_by_id = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
