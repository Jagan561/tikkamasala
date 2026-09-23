"""
Delivery OTP routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from pydantic import BaseModel

from app.config.database import get_db
from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory
from app.utils.jwt import decode_token
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/api/delivery-otp", tags=["Delivery"])


class VerifyDeliveryOTPRequest(BaseModel):
    order_id: int
    otp: str


async def get_admin_payload(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_token(auth.split(" ")[1])
    if payload.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return payload


@router.post("/verify")
async def verify_delivery_otp(req: VerifyDeliveryOTPRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Admin verifies customer delivery OTP to mark order as DELIVERED."""
    await get_admin_payload(request)

    result = await db.execute(select(Order).where(Order.id == req.order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.status == "DELIVERED":
        raise HTTPException(status_code=400, detail="Order already delivered.")

    if order.status not in ("OUT_FOR_DELIVERY", "READY"):
        raise HTTPException(status_code=400, detail=f"Cannot verify OTP for order in status: {order.status}")

    if not order.delivery_otp:
        raise HTTPException(status_code=400, detail="No delivery OTP set for this order.")

    if datetime.utcnow() > order.otp_expires_at:
        raise HTTPException(status_code=400, detail="Delivery OTP has expired.")

    order.otp_attempts += 1
    if order.otp_attempts > 5:
        await db.commit()
        raise HTTPException(status_code=400, detail="Too many OTP attempts.")

    if order.delivery_otp != req.otp:
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid delivery OTP.")

    # Mark as delivered
    order.status = "DELIVERED"
    db.add(OrderStatusHistory(order_id=order.id, status="DELIVERED", changed_by="admin"))
    await db.commit()

    # Notify customer in real-time
    await ws_manager.send_to_customer(order.user_id, {
        "event": "ORDER_STATUS_CHANGED",
        "order_id": order.id,
        "order_number": order.order_number,
        "status": "DELIVERED",
        "message": "Your order has been delivered. Thank you!",
    })

    return {"message": "Order marked as DELIVERED.", "order_id": order.id}
