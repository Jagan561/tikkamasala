from pydantic import BaseModel
from typing import Optional


class CreatePaymentRequest(BaseModel):
    order_id: int


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    razorpay_order_id: str
    amount: float
    currency: str
    status: str

    class Config:
        from_attributes = True
