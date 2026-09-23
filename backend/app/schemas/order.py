from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class CreateOrderRequest(BaseModel):
    order_type: str = "DELIVERY"   # DELIVERY | PICKUP
    delivery_address: Optional[str] = None
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    order_type: str
    delivery_address: Optional[str] = None
    subtotal: float
    delivery_fee: float
    discount: float
    total: float
    status: str
    items: List[OrderItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateOrderStatusRequest(BaseModel):
    status: str
    note: Optional[str] = None
