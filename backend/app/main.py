"""
FastAPI application entry point.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.config.settings import settings
from app.config.database import engine, AsyncSessionLocal, Base
import app.models  # Import all models so Base knows about them

from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as orders_router
from app.routes.payments import router as payments_router
from app.routes.delivery import router as delivery_router
from app.routes.websocket import router as ws_router
from app.routes.admin.dashboard import router as admin_dashboard_router
from app.routes.admin.orders import router as admin_orders_router
from app.routes.admin.products import router as admin_products_router
from app.routes.admin.customers import router as admin_customers_router
from app.routes.admin.inventory import router as admin_inventory_router
from app.routes.admin.sales import router as admin_sales_router

app = FastAPI(
    title="Tikka Masala Chat Corner API",
    description="Full-stack chaat ordering & delivery system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(delivery_router)
app.include_router(ws_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_orders_router)
app.include_router(admin_products_router)
app.include_router(admin_customers_router)
app.include_router(admin_inventory_router)
app.include_router(admin_sales_router)


@app.on_event("startup")
async def startup():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created/verified.")

    # Seed initial data
    async with AsyncSessionLocal() as db:
        from app.services.seed_service import seed_database
        await seed_database(db)


# Mount frontend static files (must be AFTER all API routes)
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
_frontend_dir = os.path.abspath(_frontend_dir)
if os.path.isdir(_frontend_dir):
    # Mount sub-directories so absolute paths like /customer/, /css/, /js/ resolve correctly
    import os as _os
    for _sub in ("customer", "admin", "css", "js"):
        _sub_dir = _os.path.join(_frontend_dir, _sub)
        if _os.path.isdir(_sub_dir):
            app.mount(f"/{_sub}", StaticFiles(directory=_sub_dir), name=_sub)
    # Also keep /app mount for backward compatibility
    app.mount("/app", StaticFiles(directory=_frontend_dir, html=True), name="frontend")


@app.get("/")
async def root():
    # Serve index.html directly from frontend dir
    _index = os.path.join(_frontend_dir, "index.html")
    if os.path.isfile(_index):
        return FileResponse(_index)
    return RedirectResponse(url="/app/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
