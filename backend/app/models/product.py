from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, func, Text
from app.config.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    image_url = Column(String(500), nullable=True)
    stock_quantity = Column(Integer, default=100)
    is_available = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
