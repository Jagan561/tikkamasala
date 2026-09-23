"""
Razorpay payment routes with server-side signature verification.
In DEMO_MODE=true, skips real Razorpay calls for local testing.
"""
import hmac
import hashlib
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.config.database import get_db
from app.config.settings import settings
from app.models.order import Order
from app.models.payment import Payment
from app.models.order_status_history import OrderStatusHistory
from app.schemas.payment import CreatePaymentRequest, VerifyPaymentRequest
from app.utils.jwt import decode_token
from app.services.websocket_manager import ws_manager
from app.services.sms_service import send_delivery_otp_sms
from app.utils.otp import generate_otp
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/payments", tags=["Payments"])


async def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_token(auth.split(" ")[1])
    if payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer access required.")
    return int(payload["sub"])


@router.post("/create")
async def create_payment(req: CreatePaymentRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Create payment order. In DEMO_MODE, returns a fake Razorpay order without hitting the gateway."""
    user_id = await get_current_user_id(request)

    order_result = await db.execute(select(Order).where(Order.id == req.order_id, Order.user_id == user_id))
    order = order_result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    pay_result = await db.execute(select(Payment).where(Payment.order_id == order.id))
    existing_payment = pay_result.scalars().first()
    if existing_payment and existing_payment.status == "PAID":
        raise HTTPException(status_code=400, detail="Order already paid.")

    # --- DEMO MODE: skip real Razorpay ---
    if settings.DEMO_MODE:
        demo_rzp_order_id = f"demo_order_{uuid.uuid4().hex[:12]}"
        if existing_payment:
            existing_payment.razorpay_order_id = demo_rzp_order_id
            existing_payment.status = "PENDING"
        else:
            db.add(Payment(
                order_id=order.id,
                razorpay_order_id=demo_rzp_order_id,
                amount=order.total,
                currency="INR",
                status="PENDING",
            ))
        await db.commit()
        return {
            "razorpay_order_id": demo_rzp_order_id,
            "razorpay_key_id": "DEMO_MODE",
            "amount": int(float(order.total) * 100),
            "currency": "INR",
            "order_number": order.order_number,
            "demo_mode": True,
        }

    # --- PRODUCTION: real Razorpay ---
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount_paise = int(float(order.total) * 100)
        rzp_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": order.order_number,
            "notes": {"order_id": str(order.id)},
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment gateway error: {str(e)}")

    if existing_payment:
        existing_payment.razorpay_order_id = rzp_order["id"]
        existing_payment.status = "PENDING"
    else:
        db.add(Payment(
            order_id=order.id,
            razorpay_order_id=rzp_order["id"],
            amount=order.total,
            currency="INR",
            status="PENDING",
        ))
    await db.commit()

    return {
        "razorpay_order_id": rzp_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": int(float(order.total) * 100),
        "currency": "INR",
        "order_number": order.order_number,
    }


@router.post("/verify")
async def verify_payment(req: VerifyPaymentRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Verify payment. In DEMO_MODE, skips HMAC check."""
    user_id = await get_current_user_id(request)

    # --- Signature check (skip in demo mode) ---
    if not settings.DEMO_MODE:
        msg = f"{req.razorpay_order_id}|{req.razorpay_payment_id}"
        expected_sig = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            msg.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, req.razorpay_signature):
            raise HTTPException(status_code=400, detail="Invalid payment signature.")

    pay_result = await db.execute(select(Payment).where(Payment.razorpay_order_id == req.razorpay_order_id))
    payment = pay_result.scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    if payment.status == "PAID":
        return {"message": "Payment already verified.", "order_id": payment.order_id}

    payment.razorpay_payment_id = req.razorpay_payment_id
    payment.status = "PAID"

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalars().first()
    order.status = "PAYMENT_VERIFIED"

    otp = generate_otp(6)
    order.delivery_otp = otp
    order.otp_expires_at = datetime.utcnow() + timedelta(hours=12)
    order.otp_attempts = 0

    db.add(OrderStatusHistory(order_id=order.id, status="PAYMENT_VERIFIED", changed_by="system"))
    await db.commit()

    from app.models.user import User
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    if user:
        await send_delivery_otp_sms(user.mobile, otp)

    await ws_manager.broadcast_to_admins({
        "event": "PAYMENT_VERIFIED",
        "order_id": order.id,
        "order_number": order.order_number,
        "status": "PAYMENT_VERIFIED",
    })
    await ws_manager.send_to_customer(user_id, {
        "event": "ORDER_STATUS_CHANGED",
        "order_id": order.id,
        "order_number": order.order_number,
        "status": "PAYMENT_VERIFIED",
    })

    return {
        "message": "Payment verified. Order confirmed.",
        "order_id": order.id,
        "order_number": order.order_number,
    }


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Idempotent Razorpay webhook handler."""
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    import json
    payload = json.loads(body)
    event = payload.get("event", "")

    if event == "payment.captured":
        payment_entity = payload["payload"]["payment"]["entity"]
        rzp_payment_id = payment_entity["id"]
        rzp_order_id = payment_entity["order_id"]

        pay_result = await db.execute(select(Payment).where(Payment.razorpay_order_id == rzp_order_id))
        payment = pay_result.scalars().first()
        if payment and payment.status != "PAID":
            payment.razorpay_payment_id = rzp_payment_id
            payment.status = "PAID"
            order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
            order = order_result.scalars().first()
            if order and order.status == "NEW":
                order.status = "PAYMENT_VERIFIED"
                db.add(OrderStatusHistory(order_id=order.id, status="PAYMENT_VERIFIED", changed_by="webhook"))
            await db.commit()

    return {"status": "ok"}
