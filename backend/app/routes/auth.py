"""
Authentication routes: register, OTP, login, logout, me.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User
from app.models.admin import Admin
from app.schemas.auth import (
    SendOTPRequest, VerifyOTPRequest, RegisterRequest,
    LoginRequest, AdminLoginRequest, TokenResponse, AdminTokenResponse, UserResponse
)
from app.services.otp_service import create_otp, verify_otp
from app.services.sms_service import send_otp_sms
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, decode_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Temporary in-memory store for OTP-verified tokens (use Redis in production)
_verified_mobiles: dict = {}


@router.post("/send-otp")
async def send_otp(req: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    """Generate OTP and send to mobile number."""
    # For REGISTRATION: check if mobile already registered
    if req.purpose == "REGISTRATION":
        result = await db.execute(select(User).where(User.mobile == req.mobile))
        existing = result.scalars().first()
        if existing and existing.is_verified:
            raise HTTPException(status_code=400, detail="Mobile already registered. Please login.")

    code = await create_otp(db, req.mobile, req.purpose)
    await send_otp_sms(req.mobile, code)

    response = {"message": f"OTP sent to {req.mobile}."}
    # In demo mode, include OTP in response for testing
    if settings.DEMO_MODE:
        response["demo_otp"] = code
    return response


@router.post("/verify-otp")
async def verify_otp_route(req: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP. On success return a short-lived verification token."""
    await verify_otp(db, req.mobile, req.code, req.purpose)

    # Issue temporary token proving OTP was verified
    token = create_access_token({"mobile": req.mobile, "purpose": req.purpose, "otp_verified": True})
    _verified_mobiles[req.mobile + ":" + req.purpose] = True
    return {"message": "OTP verified.", "otp_verified_token": token}


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create customer account after OTP verification."""
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    # Validate the OTP-verified token
    try:
        payload = decode_token(req.otp_verified_token)
        if not payload.get("otp_verified") or payload.get("mobile") != req.mobile:
            raise HTTPException(status_code=400, detail="OTP verification required before registration.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired verification session.")

    # Check duplicate
    result = await db.execute(select(User).where(User.mobile == req.mobile))
    existing = result.scalars().first()
    if existing and existing.is_verified:
        raise HTTPException(status_code=400, detail="Mobile already registered.")

    if existing:
        existing.name = req.name
        existing.password_hash = hash_password(req.password)
        existing.is_verified = True
        user = existing
    else:
        user = User(
            name=req.name,
            mobile=req.mobile,
            password_hash=hash_password(req.password),
            is_verified=True,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "mobile": user.mobile,
        "role": "customer",
    })
    return {
        "message": "Registration successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "mobile": user.mobile},
    }


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.mobile == req.mobile))
    user = result.scalars().first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid mobile or password.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Account not verified. Please complete OTP verification.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = create_access_token({
        "sub": str(user.id),
        "mobile": user.mobile,
        "role": "customer",
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "mobile": user.mobile},
    }


@router.post("/admin/login")
async def admin_login(req: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).where(Admin.username == req.username))
    admin = result.scalars().first()

    if not admin or not verify_password(req.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid admin credentials.")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account deactivated.")

    token = create_access_token({
        "sub": str(admin.id),
        "username": admin.username,
        "role": admin.role,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": admin.role,
        "username": admin.username,
    }


@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = auth.split(" ")[1]
    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))
    role = payload.get("role", "")

    if role in ("admin", "superadmin"):
        result = await db.execute(select(Admin).where(Admin.id == user_id))
        admin = result.scalars().first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found.")
        return {"id": admin.id, "username": admin.username, "role": admin.role}

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"id": user.id, "name": user.name, "mobile": user.mobile, "role": "customer"}
