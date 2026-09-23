from sqlalchemy import Column, Integer, DECIMAL, ForeignKey, DateTime, func
from app.config.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(DECIMAL(10, 2), nullable=True)  # snapshot at order time
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)   # price at order time
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
