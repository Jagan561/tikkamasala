"""
Database seeder — runs on startup in DEMO_MODE.
Populates categories, products, inventory, and default admin.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.admin import Admin
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory
from app.utils.security import hash_password
from app.config.settings import settings

CATEGORIES = [
    {"name": "Chaat", "description": "Street-style chaat delights", "image_url": "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=400"},
    {"name": "Snacks", "description": "Crispy snacks & bites", "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400"},
    {"name": "Meals", "description": "Full meals & dosas", "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=400"},
    {"name": "Beverages", "description": "Fresh drinks & juices", "image_url": "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400"},
]

PRODUCTS = [
    {
        "name": "Pani Puri",
        "description": "Crispy puris filled with tangy tamarind water, chickpeas, and spices. A classic street food experience!",
        "price": 50.00,
        "category": "Chaat",
        "image_url": "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=600",
        "is_featured": True,
        "stock_quantity": 200,
    },
    {
        "name": "Bhel Puri",
        "description": "Puffed rice tossed with vegetables, chutneys and sev. Light, crispy and absolutely delicious.",
        "price": 60.00,
        "category": "Chaat",
        "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600",
        "is_featured": True,
        "stock_quantity": 150,
    },
    {
        "name": "Samosa",
        "description": "Golden-fried pastry filled with spiced potatoes and peas. Served hot with mint chutney.",
        "price": 30.00,
        "category": "Snacks",
        "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600",
        "is_featured": True,
        "stock_quantity": 300,
    },
    {
        "name": "Masala Sandwich",
        "description": "Toasted bread stuffed with spiced potato filling, onions and green chutney.",
        "price": 80.00,
        "category": "Snacks",
        "image_url": "https://images.unsplash.com/photo-1528736235302-52922df5c122?w=600",
        "is_featured": False,
        "stock_quantity": 100,
    },
    {
        "name": "Masala Dosa",
        "description": "Crispy rice crepe filled with spiced potato masala. Served with sambar and chutneys.",
        "price": 90.00,
        "category": "Meals",
        "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=600",
        "is_featured": True,
        "stock_quantity": 80,
    },
    {
        "name": "Fresh Lime Soda",
        "description": "Freshly squeezed lime juice with soda water. Sweet, salty or masala — your choice!",
        "price": 40.00,
        "category": "Beverages",
        "image_url": "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=600",
        "is_featured": False,
        "stock_quantity": 500,
    },
]


async def seed_database(db: AsyncSession):
    """Seed initial data if tables are empty."""
    # Seed admin
    result = await db.execute(select(Admin).where(Admin.username == settings.ADMIN_USERNAME))
    if not result.scalars().first():
        admin = Admin(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
        )
        db.add(admin)
        print(f"✅ Admin seeded: {settings.ADMIN_USERNAME}")

    # Seed categories
    cat_map = {}
    for cat_data in CATEGORIES:
        result = await db.execute(select(Category).where(Category.name == cat_data["name"]))
        cat = result.scalars().first()
        if not cat:
            cat = Category(**cat_data)
            db.add(cat)
            await db.flush()
            print(f"✅ Category seeded: {cat_data['name']}")
        cat_map[cat_data["name"]] = cat.id

    # Seed products
    for p_data in PRODUCTS:
        result = await db.execute(select(Product).where(Product.name == p_data["name"]))
        prod = result.scalars().first()
        if not prod:
            category_name = p_data.pop("category")
            prod = Product(category_id=cat_map.get(category_name), **p_data)
            db.add(prod)
            await db.flush()
            # Create inventory entry
            inv = Inventory(product_id=prod.id, current_stock=p_data.get("stock_quantity", 100))
            db.add(inv)
            print(f"✅ Product seeded: {prod.name}")
        else:
            p_data.pop("category", None)

    await db.commit()
    print("✅ Database seeding complete.")
