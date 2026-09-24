"""
Admin dashboard stats route.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date

from app.config.database import get_db
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.models.product import Product
from app.models.inventory import Inventory
from app.routes.admin.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard")
async def get_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    # Today's orders
    orders_today_result = await db.execute(
        select(func.count(Order.id)).where(Order.created_at >= today_start)
    )
    orders_today = orders_today_result.scalar() or 0

    # Today's sales (PAYMENT_VERIFIED or beyond)
    sales_today_result = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            and_(Order.created_at >= today_start, Order.status.not_in(["NEW", "CANCELLED"]))
        )
    )
    sales_today = float(sales_today_result.scalar() or 0)

    # Pending orders
    pending_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == "PAYMENT_VERIFIED")
    )
    pending = pending_result.scalar() or 0

    # Preparing
    preparing_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == "PREPARING")
    )
    preparing = preparing_result.scalar() or 0

    # Completed today
    completed_result = await db.execute(
        select(func.count(Order.id)).where(
            and_(Order.created_at >= today_start, Order.status.in_(["DELIVERED", "PICKED_UP"]))
        )
    )
    completed = completed_result.scalar() or 0

    # Total customers
    customers_result = await db.execute(select(func.count(User.id)).where(User.is_verified == True))
    total_customers = customers_result.scalar() or 0

    # Low stock
    low_stock_result = await db.execute(
        select(func.count(Inventory.id)).where(Inventory.current_stock <= Inventory.low_stock_threshold)
    )
    low_stock = low_stock_result.scalar() or 0

    return {
        "orders_today": orders_today,
        "sales_today": sales_today,
        "pending_orders": pending,
        "preparing_orders": preparing,
        "completed_today": completed,
        "total_customers": total_customers,
        "low_stock_items": low_stock,
    }
