"""
Admin sales analytics routes.
"""
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, Date
from datetime import datetime, date, timedelta
from typing import Optional

from app.config.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.category import Category
from app.routes.admin.deps import require_admin

router = APIRouter(prefix="/api/admin/sales", tags=["Admin"])


@router.get("/daily")
async def daily_sales(
    request: Request,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(request)
    start = datetime.combine(date.today() - timedelta(days=days - 1), datetime.min.time())

    result = await db.execute(
        select(
            cast(Order.created_at, Date).label("sale_date"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .where(and_(
            Order.created_at >= start,
            Order.status.not_in(["NEW", "CANCELLED"])
        ))
        .group_by("sale_date")
        .order_by("sale_date")
    )
    rows = result.all()
    return [{"date": str(r.sale_date), "orders": r.orders, "revenue": float(r.revenue)} for r in rows]


@router.get("/monthly")
async def monthly_sales(
    request: Request,
    months: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(request)
    start = date.today().replace(day=1) - timedelta(days=30 * (months - 1))
    start_dt = datetime.combine(start, datetime.min.time())

    result = await db.execute(
        select(
            func.year(Order.created_at).label("year"),
            func.month(Order.created_at).label("month"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .where(and_(
            Order.created_at >= start_dt,
            Order.status.not_in(["NEW", "CANCELLED"])
        ))
        .group_by("year", "month")
        .order_by("year", "month")
    )
    rows = result.all()
    return [
        {"year": r.year, "month": r.month, "orders": r.orders, "revenue": float(r.revenue)}
        for r in rows
    ]


@router.get("/products")
async def product_sales(request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(
        select(
            Product.name,
            func.sum(OrderItem.quantity).label("total_qty"),
            func.sum(OrderItem.subtotal).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.name)
        .order_by(func.sum(OrderItem.subtotal).desc())
    )
    rows = result.all()
    return [{"product": r.name, "quantity": int(r.total_qty), "revenue": float(r.total_revenue)} for r in rows]


@router.get("/summary")
async def sales_summary(request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())

    async def get_stats(start_dt):
        r = await db.execute(
            select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0))
            .where(and_(Order.created_at >= start_dt, Order.status.not_in(["NEW", "CANCELLED"])))
        )
        return r.first()

    today_stats = await get_stats(today_start)
    month_stats = await get_stats(month_start)

    return {
        "today": {"orders": today_stats[0], "revenue": float(today_stats[1])},
        "this_month": {"orders": month_stats[0], "revenue": float(month_stats[1])},
    }
