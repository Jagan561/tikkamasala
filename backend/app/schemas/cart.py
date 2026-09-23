from pydantic import BaseModel
from typing import List, Optional


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    unit_price: float
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    items: List[CartItemResponse]
    subtotal: float
    item_count: int


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1


class UpdateCartItemRequest(BaseModel):
    quantity: int
