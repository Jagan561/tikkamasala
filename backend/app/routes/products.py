"""
Product and category routes for customers.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.config.database import get_db
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductResponse, CategoryResponse

router = APIRouter(tags=["Products"])


@router.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.is_active == True).order_by(Category.sort_order))
    return result.scalars().all()


@router.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    category_id: Optional[int] = Query(None),
    available_only: bool = Query(False),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product)
    if category_id:
        query = query.where(Product.category_id == category_id)
    if available_only:
        query = query.where(Product.is_available == True)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    query = query.order_by(Product.sort_order, Product.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product
