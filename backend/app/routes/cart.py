"""
Cart routes — all prices computed server-side.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.config.database import get_db
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.schemas.cart import AddToCartRequest, UpdateCartItemRequest
from app.utils.jwt import decode_token

router = APIRouter(prefix="/api/cart", tags=["Cart"])


async def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_token(auth.split(" ")[1])
    if payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer access required.")
    return int(payload["sub"])


async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = result.scalars().first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart


async def build_cart_response(db: AsyncSession, cart: Cart) -> dict:
    result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    items_raw = result.scalars().all()
    items = []
    subtotal = 0.0
    for item in items_raw:
        prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = prod_result.scalars().first()
        if not product:
            continue
        item_subtotal = float(product.price) * item.quantity
        subtotal += item_subtotal
        items.append({
            "id": item.id,
            "product_id": product.id,
            "product_name": product.name,
            "product_image": product.image_url,
            "unit_price": float(product.price),
            "quantity": item.quantity,
            "subtotal": item_subtotal,
        })
    return {"id": cart.id, "items": items, "subtotal": round(subtotal, 2), "item_count": len(items)}


@router.get("")
async def get_cart(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id(request)
    cart = await get_or_create_cart(db, user_id)
    return await build_cart_response(db, cart)


@router.post("/items")
async def add_to_cart(req: AddToCartRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id(request)

    # Validate product
    prod_result = await db.execute(select(Product).where(Product.id == req.product_id))
    product = prod_result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    if not product.is_available:
        raise HTTPException(status_code=400, detail="Product is not available.")
    if req.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1.")

    cart = await get_or_create_cart(db, user_id)

    # Check if item already in cart
    item_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == req.product_id)
    )
    existing = item_result.scalars().first()
    if existing:
        existing.quantity = req.quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=req.product_id, quantity=req.quantity)
        db.add(cart_item)

    await db.commit()
    return await build_cart_response(db, cart)


@router.patch("/items/{item_id}")
async def update_cart_item(item_id: int, req: UpdateCartItemRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id(request)
    cart = await get_or_create_cart(db, user_id)

    result = await db.execute(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")

    if req.quantity < 1:
        await db.delete(item)
    else:
        item.quantity = req.quantity

    await db.commit()
    return await build_cart_response(db, cart)


@router.delete("/items/{item_id}")
async def remove_cart_item(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id(request)
    cart = await get_or_create_cart(db, user_id)
    result = await db.execute(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    await db.delete(item)
    await db.commit()
    return await build_cart_response(db, cart)


@router.delete("")
async def clear_cart(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id(request)
    cart = await get_or_create_cart(db, user_id)
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()
    return {"message": "Cart cleared."}
