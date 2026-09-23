"""
Order creation and retrieval routes.
Full 12-step order process with Haversine 3km validation.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
from decimal import Decimal

from app.config.database import get_db
from app.config.settings import settings
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.payment import Payment
from app.models.product import Product
from app.schemas.order import CreateOrderRequest
from app.utils.jwt import decode_token
from app.utils.location import haversine_distance
from app.services.websocket_manager import ws_manager
import random
import string

router = APIRouter(prefix="/api/orders", tags=["Orders"])


async def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_token(auth.split(" ")[1])
    if payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer access required.")
    return int(payload["sub"])


def generate_order_number() -> str:
    return "TM" + "".join(random.choices(string.digits, k=6))


@router.post("")
async def create_order(req: CreateOrderRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Full order creation with all validations."""
    user_id = await get_current_user_id(request)

    # Step 1: Get cart
    cart_result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = cart_result.scalars().first()
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    # Step 2: Get cart items
    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    cart_items = items_result.scalars().all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    # Step 3-4: Validate products + fetch real prices
    subtotal = Decimal("0.00")
    order_items_data = []
    for item in cart_items:
        prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = prod_result.scalars().first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found.")
        if not product.is_available:
            raise HTTPException(status_code=400, detail=f"'{product.name}' is currently unavailable.")
        item_subtotal = product.price * item.quantity
        subtotal += Decimal(str(item_subtotal))
        order_items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit_price": Decimal(str(product.price)),
            "subtotal": Decimal(str(item_subtotal)),
        })

    # Step 5: Delivery validation
    delivery_fee = Decimal("0.00")
    if req.order_type == "DELIVERY":
        if not req.delivery_address or req.delivery_lat is None or req.delivery_lng is None:
            raise HTTPException(status_code=400, detail="Delivery address and location are required.")

        distance = haversine_distance(
            settings.SHOP_LATITUDE, settings.SHOP_LONGITUDE,
            req.delivery_lat, req.delivery_lng
        )
        if distance > settings.DELIVERY_RADIUS_KM:
            raise HTTPException(
                status_code=400,
                detail=f"Sorry, delivery is available only within {settings.DELIVERY_RADIUS_KM} km of Tikka Masala Chat Corner. Your location is {distance:.1f} km away."
            )
        delivery_fee = Decimal(str(settings.DELIVERY_CHARGE))

    discount = Decimal("0.00")
    total = subtotal + delivery_fee - discount

    # Step 6: Create order
    order_number = generate_order_number()
    # Ensure uniqueness
    while True:
        existing = await db.execute(select(Order).where(Order.order_number == order_number))
        if not existing.scalars().first():
            break
        order_number = generate_order_number()

    order = Order(
        order_number=order_number,
        user_id=user_id,
        order_type=req.order_type,
        delivery_address=req.delivery_address,
        delivery_lat=Decimal(str(req.delivery_lat)) if req.delivery_lat else None,
        delivery_lng=Decimal(str(req.delivery_lng)) if req.delivery_lng else None,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount=discount,
        total=total,
        status="NEW",
        notes=req.notes,
    )
    db.add(order)
    await db.flush()  # get order.id

    # Step 7: Create order items
    for oi in order_items_data:
        db.add(OrderItem(
            order_id=order.id,
            product_id=oi["product_id"],
            quantity=oi["quantity"],
            unit_price=oi["unit_price"],
            subtotal=oi["subtotal"],
        ))

    # Step 8: Status history
    db.add(OrderStatusHistory(order_id=order.id, status="NEW", changed_by="system"))

    await db.commit()
    await db.refresh(order)

    # Step 9: Clear cart
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()

    # Step 10: Notify admins via WebSocket
    await ws_manager.broadcast_to_admins({
        "event": "NEW_ORDER",
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "user_id": user_id,
            "total": float(order.total),
            "status": order.status,
            "order_type": order.order_type,
            "items": order_items_data and [
                {"name": oi["product_name"], "quantity": oi["quantity"]} for oi in order_items_data
            ],
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
    })

    return {
        "message": "Order created successfully.",
        "order_id": order.id,
        "order_number": order.order_number,
        "total": float(order.total),
        "status": order.status,
    }


@router.get("")
async def get_my_orders(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id(request)
    result = await db.execute(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()))
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "order_type": o.order_type,
            "total": float(o.total),
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@router.get("/{order_id}")
async def get_order(order_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id(request)
    result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = items_result.scalars().all()
    items_data = []
    for item in items:
        prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
        prod = prod_result.scalars().first()
        items_data.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": prod.name if prod else "Unknown",
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
        })

    # Status history
    hist_result = await db.execute(
        select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id).order_by(OrderStatusHistory.created_at)
    )
    history = [{"status": h.status, "created_at": h.created_at.isoformat()} for h in hist_result.scalars().all()]

    # Payment info
    pay_result = await db.execute(select(Payment).where(Payment.order_id == order.id))
    payment = pay_result.scalars().first()

    return {
        "id": order.id,
        "order_number": order.order_number,
        "order_type": order.order_type,
        "delivery_address": order.delivery_address,
        "subtotal": float(order.subtotal),
        "delivery_fee": float(order.delivery_fee),
        "discount": float(order.discount),
        "total": float(order.total),
        "status": order.status,
        "items": items_data,
        "history": history,
        "payment_status": payment.status if payment else "PENDING",
        "razorpay_order_id": payment.razorpay_order_id if payment else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }
