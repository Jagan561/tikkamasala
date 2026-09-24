"""
Admin order management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.config.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.payment import Payment
from app.models.product import Product
from app.models.user import User
from app.routes.admin.deps import require_admin
from app.services.websocket_manager import ws_manager
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["Admin"])

VALID_TRANSITIONS = {
    "PAYMENT_VERIFIED": ["PREPARING", "CANCELLED"],
    "PREPARING": ["READY", "READY_FOR_PICKUP"],
    "READY": ["OUT_FOR_DELIVERY"],
    "READY_FOR_PICKUP": ["PICKED_UP"],
    "OUT_FOR_DELIVERY": ["DELIVERED"],
}


class UpdateStatusRequest(BaseModel):
    status: str
    note: Optional[str] = None


@router.get("/orders")
async def list_orders(request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    orders = result.scalars().all()

    out = []
    for o in orders:
        user_result = await db.execute(select(User).where(User.id == o.user_id))
        user = user_result.scalars().first()
        pay_result = await db.execute(select(Payment).where(Payment.order_id == o.id))
        payment = pay_result.scalars().first()
        items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == o.id))
        items = items_result.scalars().all()
        items_data = []
        for item in items:
            prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
            prod = prod_result.scalars().first()
            items_data.append({
                "product_name": prod.name if prod else "Unknown",
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            })
        out.append({
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": user.name if user else "Unknown",
            "customer_mobile": user.mobile if user else "",
            "order_type": o.order_type,
            "delivery_address": o.delivery_address,
            "subtotal": float(o.subtotal),
            "delivery_fee": float(o.delivery_fee),
            "total": float(o.total),
            "status": o.status,
            "payment_status": payment.status if payment else "PENDING",
            "items": items_data,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })
    return out


@router.get("/orders/{order_id}")
async def get_order(order_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    user_result = await db.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalars().first()

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = items_result.scalars().all()
    items_data = []
    for item in items:
        prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
        prod = prod_result.scalars().first()
        items_data.append({
            "product_name": prod.name if prod else "Unknown",
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
        })

    hist_result = await db.execute(
        select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id).order_by(OrderStatusHistory.created_at)
    )
    history = [{"status": h.status, "created_at": h.created_at.isoformat()} for h in hist_result.scalars().all()]

    pay_result = await db.execute(select(Payment).where(Payment.order_id == order.id))
    payment = pay_result.scalars().first()

    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": user.name if user else "Unknown",
        "customer_mobile": user.mobile if user else "",
        "order_type": order.order_type,
        "delivery_address": order.delivery_address,
        "delivery_lat": float(order.delivery_lat) if order.delivery_lat else None,
        "delivery_lng": float(order.delivery_lng) if order.delivery_lng else None,
        "subtotal": float(order.subtotal),
        "delivery_fee": float(order.delivery_fee),
        "discount": float(order.discount),
        "total": float(order.total),
        "status": order.status,
        "payment_status": payment.status if payment else "PENDING",
        "items": items_data,
        "history": history,
        "notes": order.notes,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "delivery_otp": order.delivery_otp,  # Admin sees OTP for delivery verification
    }


@router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: int, req: UpdateStatusRequest, request: Request, db: AsyncSession = Depends(get_db)):
    payload = await require_admin(request)
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    allowed = VALID_TRANSITIONS.get(order.status, [])
    if req.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {order.status} to {req.status}. Allowed: {allowed}"
        )

    order.status = req.status
    db.add(OrderStatusHistory(
        order_id=order.id,
        status=req.status,
        changed_by="admin",
        changed_by_id=int(payload.get("sub", 0)),
        note=req.note,
    ))
    await db.commit()

    # Real-time: notify customer
    status_messages = {
        "PREPARING": "Your order is being prepared. 🍽️",
        "READY": "Your order is ready!",
        "READY_FOR_PICKUP": "Your order is ready for pickup!",
        "OUT_FOR_DELIVERY": "Your order is out for delivery! 🛵",
        "PICKED_UP": "Order picked up. Thank you!",
        "CANCELLED": "Your order has been cancelled.",
    }
    await ws_manager.send_to_customer(order.user_id, {
        "event": "ORDER_STATUS_CHANGED",
        "order_id": order.id,
        "order_number": order.order_number,
        "status": req.status,
        "message": status_messages.get(req.status, f"Order status: {req.status}"),
    })
    await ws_manager.broadcast_to_admins({
        "event": "ORDER_UPDATED",
        "order_id": order.id,
        "order_number": order.order_number,
        "status": req.status,
    })

    return {"message": f"Order status updated to {req.status}.", "order_id": order.id, "status": req.status}
