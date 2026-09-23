"""
Admin customer management route.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config.database import get_db
from app.models.user import User
from app.models.order import Order
from app.routes.admin.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/customers")
async def list_customers(request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(User).where(User.is_verified == True).order_by(User.created_at.desc()))
    users = result.scalars().all()

    out = []
    for u in users:
        orders_result = await db.execute(
            select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0))
            .where(Order.user_id == u.id)
        )
        row = orders_result.first()
        out.append({
            "id": u.id,
            "name": u.name,
            "mobile": u.mobile,
            "is_active": u.is_active,
            "registered_at": u.created_at.isoformat() if u.created_at else None,
            "total_orders": row[0] or 0,
            "total_spent": float(row[1] or 0),
        })
    return out
