"""
Admin inventory management route.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from app.config.database import get_db
from app.models.inventory import Inventory
from app.models.product import Product
from app.routes.admin.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class UpdateInventoryRequest(BaseModel):
    current_stock: Optional[int] = None
    low_stock_threshold: Optional[int] = None


@router.get("/inventory")
async def get_inventory(request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Inventory))
    inventory = result.scalars().all()
    out = []
    for inv in inventory:
        prod_result = await db.execute(select(Product).where(Product.id == inv.product_id))
        product = prod_result.scalars().first()
        out.append({
            "id": inv.id,
            "product_id": inv.product_id,
            "product_name": product.name if product else "Unknown",
            "current_stock": inv.current_stock,
            "low_stock_threshold": inv.low_stock_threshold,
            "is_low_stock": inv.current_stock <= inv.low_stock_threshold,
            "is_available": product.is_available if product else False,
        })
    return out


@router.patch("/inventory/{inv_id}")
async def update_inventory(inv_id: int, req: UpdateInventoryRequest, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Inventory).where(Inventory.id == inv_id))
    inv = result.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found.")
    if req.current_stock is not None:
        inv.current_stock = req.current_stock
        # Auto-update product availability
        prod_result = await db.execute(select(Product).where(Product.id == inv.product_id))
        product = prod_result.scalars().first()
        if product:
            product.stock_quantity = req.current_stock
            if req.current_stock <= 0:
                product.is_available = False
    if req.low_stock_threshold is not None:
        inv.low_stock_threshold = req.low_stock_threshold
    await db.commit()
    return {"message": "Inventory updated."}
