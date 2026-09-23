from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    stock_quantity: int
    is_available: bool
    is_featured: bool

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    stock_quantity: int = 100
    is_available: bool = True
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    stock_quantity: Optional[int] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
