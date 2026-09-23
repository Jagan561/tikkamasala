"""
Admin product + category CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from app.config.database import get_db
from app.models.product import Product
from app.models.category import Category
from app.models.inventory import Inventory
from app.routes.admin.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    stock_quantity: int = 100
    is_available: bool = True
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    stock_quantity: Optional[int] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/products")
async def create_product(req: ProductCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    product = Product(**req.model_dump())
    db.add(product)
    await db.flush()
    # Create inventory record
    db.add(Inventory(product_id=product.id, current_stock=req.stock_quantity))
    await db.commit()
    await db.refresh(product)
    return {"message": "Product created.", "id": product.id}


@router.put("/products/{product_id}")
async def update_product(product_id: int, req: ProductUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    await db.commit()
    return {"message": "Product updated."}


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted."}


# ---------- Categories ----------

@router.post("/categories")
async def create_category(req: CategoryCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    cat = Category(**req.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return {"message": "Category created.", "id": cat.id}


@router.put("/categories/{cat_id}")
async def update_category(cat_id: int, req: CategoryUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalars().first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    await db.commit()
    return {"message": "Category updated."}


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    await require_admin(request)
    result = await db.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalars().first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    await db.delete(cat)
    await db.commit()
    return {"message": "Category deleted."}
