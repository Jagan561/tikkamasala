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
    {"name": "Chats", "description": "Street-style chat delights", "sort_order": 1},
    {"name": "Sandwiches", "description": "Freshly prepared sandwiches", "sort_order": 2},
    {"name": "Toasts", "description": "Crispy toasted favorites", "sort_order": 3},
    {"name": "Grill", "description": "Grilled favorites", "sort_order": 4},
    {"name": "Puffs", "description": "Fresh baked puffs", "sort_order": 5},
    {"name": "Wraps", "description": "Loaded wraps", "sort_order": 6},
    {"name": "Pizza", "description": "Hot, cheesy pizzas", "sort_order": 7},
    {"name": "Pasta", "description": "Comforting pasta dishes", "sort_order": 8},
    {"name": "Burger", "description": "Fresh burgers", "sort_order": 9},
    {"name": "Fries", "description": "Crispy fries", "sort_order": 10},
    {"name": "Pav Bhaji", "description": "Mumbai-style pav bhaji", "sort_order": 11},
    {"name": "Pulav", "description": "Aromatic pulav", "sort_order": 12},
    {"name": "Rice", "description": "Rice favorites", "sort_order": 13},
    {"name": "Noodles", "description": "Wok-tossed noodles", "sort_order": 14},
    {"name": "Maggi", "description": "Loaded Maggi", "sort_order": 15},
    {"name": "Combos", "description": "Value meal combos", "sort_order": 16},
    {"name": "Drinks", "description": "Fresh drinks", "sort_order": 17},
]

TMCC_MENU = {
    "Chats": [
        ("Pani Puri", 40), ("Sev Puri", 60), ("Cheese Sev Puri", 80),
        ("Bhel", 60), ("Chinese Bhel", 110), ("Dahi Puri", 80),
        ("Masala Puri", 60), ("Papdi Chaat", 70), ("Cheese Papdi Chaat", 90),
        ("Dahi Papdi Chaat", 90), ("Corn Canapes", 70),
        ("Kanda Bhajiya (Onion)", 90), ("Vada Pav", 40),
        ("Cheese Vada Pav", 70), ("Pani Puri Family Pack", 160),
        ("Muffin", 60), ("Mayo Puri", 80), ("Extra Cheese", 30),
        ("Chutney (Big)", 70), ("Chutney (Small)", 20),
    ],
    "Sandwiches": [
        ("Plain Sandwich", 50), ("Veg. Cheese Sandwich", 70),
        ("Mayo Cheese Sandwich", 80), ("Khakhra Sandwich", 80),
        ("Cheese Khakhra Sandwich", 110), ("Murukku Sandwich", 80),
        ("Cheese Murukku Sandwich", 100), ("Bread Butter", 40),
        ("Bread Jam", 50), ("Bhujia Sandwich", 70),
        ("Cheese Bhujia Sandwich", 90), ("Tikki Sandwich", 110),
        ("Corn Sandwich", 110), ("Bombay Special Sandwich", 130),
    ],
    "Toasts": [
        ("Vegetable Toast", 80), ("Vegetable Cheese Toast", 100),
        ("Aloo Masala Toast", 90), ("Aloo Masala Cheese Toast", 120),
        ("Chilli / Chutney Cheese Toast", 80), ("Com Cheese Toast", 130),
        ("Paneer Cheese Toast", 100), ("TMCC Special Toast", 140),
        ("Nutella Toast", 110), ("Open Chilli Toast", 100),
        ("Open Garlic Toast", 110), ("Open Veg Toast", 130),
        ("Open Veg Paneer Toast", 170), ("Paneer Twister", 160),
        ("Dugout Special", 180), ("Hot Dog", 90),
        ("Bread Jam / Butter Toast", 70), ("Bread Stick Toast", 110),
        ("Bread Corn Stick", 120),
    ],
    "Grill": [
        ("Vegetable Grill", 130), ("Masala Grill", 150),
        ("Veg. Paneer Grill", 170), ("Schezwan Paneer Grill", 190),
        ("Jantar Mantar Grill", 190), ("TMCC Special Grill", 210),
    ],
    "Puffs": [
        ("Puff", 50), ("Cheese Puff", 70), ("Bhujia Puff", 70),
        ("Cheese Bhujia Puff", 90), ("Paneer Puff", 110),
        ("Cheese Paneer Puff", 130), ("Schezwan Puff", 90),
        ("Cheese Schezwan Puff", 110), ("Pizza Puff", 150),
    ],
    "Wraps": [
        ("Vegetable Wrap", 140), ("Paneer Wrap", 160),
        ("Schezwan Paneer Wrap", 190), ("Manchurian Wrap", 180),
        ("Aloo Tikki Wrap", 170),
    ],
    "Pizza": [
        ("Veg. Pizza", 190), ("Cheese Pizza", 170), ("Corn Pizza", 180),
        ("Paneer Pizza", 210), ("Overloaded Pizza", 260),
        ("Cheese Burst Pizza", 300),
    ],
    "Pasta": [
        ("White Sauce Pasta", 90), ("Red Sauce Pasta", 70),
        ("Pink Sauce Pasta", 100),
    ],
    "Burger": [
        ("Vegetable Burger", 110), ("Maharaja Burger", 190),
        ("Jain Burger", 140), ("Hide & Seek Burger", 160),
        ("Paneer Burger", 190),
    ],
    "Fries": [("French Fries", 110), ("Peri Peri Fries", 140), ("Cheese Ball", 110)],
    "Pav Bhaji": [
        ("Pav Bhaji", 120), ("Cheese Pav Bhaji", 150),
        ("Hari Bhari Bhaji", 150), ("Masala Pav", 140),
        ("Extra Pav (1pcs)", 10),
    ],
    "Pulav": [
        ("Tawa Pulav", 160), ("Cheese Tawa Pulav", 180),
        ("Paneer Tawa Pulav", 200),
    ],
    "Rice": [
        ("Schezwan Rice", 230), ("Schezwan Paneer Rice", 270),
        ("Fried Rice", 200), ("Paneer Fried Rice", 230),
        ("Mangolian Rice", 250), ("Burnt Garlic Rice", 250),
    ],
    "Noodles": [
        ("Noodles", 200), ("Schezwan Noodles", 230),
        ("Hakka Noodles", 210), ("Manchurian", 200),
        ("Chilli Paneer", 290),
    ],
    "Maggi": [
        ("Classic Maggi", 60), ("Masala Maggi", 70),
        ("Vegetable Maggi", 80), ("Schezwan Maggi", 80),
        ("Peri Peri Maggi", 100), ("Jain Maggi", 80),
        ("Cheese Maggi", 90),
    ],
    "Combos": [
        ("Shz Rice + Chilli Paneer", 300), ("Shz Rice + Manchurian", 270),
        ("Noodles + Manchurian", 250), ("Grill S/W + Ice Tea", 150),
        ("Cheese Puff + Thumbs Up", 110),
        ("Shz Rice + Chilli Paneer + Pepsi", 320),
        ("Shz Rice + Chilli Paneer + Ice Tea", 350),
        ("Shz Rice + Noodles", 330), ("Shz Rice + Noodles + Ice Tea", 350),
        ("Puff + Ice Tea", 100), ("Veg Wrap + Ice Tea", 190),
        ("Veg Pizza + Tang", 230),
    ],
    "Drinks": [
        ("Lemon Juice / Soda", 30), ("Mint Juice / Soda", 30),
        ("Masala Thumbs up", 30), ("Cold Coffee", 70),
        ("Chocolate Shake", 70), ("Ice Tea / Tang", 60),
        ("200 ML Water Bottle", 10), ("250 ML Water Bottle", 20),
        ("650 ML Soft Drinks", 40), ("Tin", 40), ("Hell", 65),
        ("Red Bull", 130), ("Goli Soda", 40),
    ],
}

PRODUCTS = [
    {
        "name": name,
        "price": price,
        "category": category_name,
        "is_available": True,
        "sort_order": sort_order,
        "stock_quantity": 100,
    }
    for category_name, menu_items in TMCC_MENU.items()
    for sort_order, (name, price) in enumerate(menu_items, 1)
]

LEGACY_CATEGORIES = {"Chaat", "Meals", "Beverages", "Juices", "Snacks"}


async def seed_database(db: AsyncSession):
    """Create missing TMCC rows and update matching rows without deleting data."""
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

    # Synchronize catalog categories while retaining legacy rows for history.
    cat_map = {}
    for cat_data in CATEGORIES:
        result = await db.execute(select(Category).where(Category.name == cat_data["name"]))
        cat = result.scalars().first()
        if not cat:
            cat = Category(**cat_data)
            db.add(cat)
            await db.flush()
            print(f"✅ Category added: {cat_data['name']}")
        else:
            for field, value in cat_data.items():
                setattr(cat, field, value)
            cat.is_active = True
        cat_map[cat_data["name"]] = cat.id

    result = await db.execute(select(Category).where(Category.name.in_(LEGACY_CATEGORIES)))
    for cat in result.scalars():
        cat.is_active = False

    # Upsert products by name so reruns never create duplicates.
    for source_data in PRODUCTS:
        p_data = dict(source_data)
        category_name = p_data.pop("category")
        result = await db.execute(select(Product).where(Product.name == p_data["name"]))
        prod = result.scalars().first()
        if not prod:
            prod = Product(category_id=cat_map.get(category_name), **p_data)
            db.add(prod)
            await db.flush()
            inv = Inventory(product_id=prod.id, current_stock=p_data.get("stock_quantity", 100))
            db.add(inv)
        else:
            for field, value in p_data.items():
                setattr(prod, field, value)
            prod.category_id = cat_map.get(category_name)

    await db.commit()
    print("✅ Database seeding complete.")
