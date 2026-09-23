from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, Boolean
from app.config.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True, index=True)
    current_stock = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)
    is_tracked = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
