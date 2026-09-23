"""
OTP lifecycle: generate, store, verify, expire.
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.otp import OTP
from app.utils.otp import generate_otp
from app.config.settings import settings
from fastapi import HTTPException, status

OTP_EXPIRE_MINUTES = 10
MAX_ATTEMPTS = 3
RESEND_COOLDOWN_SECONDS = 60


async def create_otp(db: AsyncSession, mobile: str, purpose: str) -> str:
    """Generate OTP, enforce cooldown, save to DB, return code."""
    # Cooldown check
    cutoff = datetime.utcnow() - timedelta(seconds=RESEND_COOLDOWN_SECONDS)
    result = await db.execute(
        select(OTP).where(and_(
            OTP.mobile == mobile,
            OTP.purpose == purpose,
            OTP.is_used == False,
            OTP.created_at > cutoff,
        ))
    )
    recent = result.scalars().first()
    if recent:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {RESEND_COOLDOWN_SECONDS}s before requesting a new OTP.",
        )

    # Expire old OTPs for this mobile + purpose
    old = await db.execute(
        select(OTP).where(and_(OTP.mobile == mobile, OTP.purpose == purpose, OTP.is_used == False))
    )
    for o in old.scalars().all():
        o.is_used = True

    code = generate_otp()
    otp = OTP(
        mobile=mobile,
        code=code,
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    await db.commit()
    return code


async def verify_otp(db: AsyncSession, mobile: str, code: str, purpose: str) -> bool:
    """Verify OTP. Raise HTTPException on failure."""
    result = await db.execute(
        select(OTP).where(and_(
            OTP.mobile == mobile,
            OTP.purpose == purpose,
            OTP.is_used == False,
        )).order_by(OTP.created_at.desc())
    )
    otp = result.scalars().first()

    if not otp:
        raise HTTPException(status_code=400, detail="OTP not found. Please request a new one.")

    if datetime.utcnow() > otp.expires_at:
        otp.is_used = True
        await db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

    otp.attempts += 1
    if otp.attempts > MAX_ATTEMPTS:
        otp.is_used = True
        await db.commit()
        raise HTTPException(status_code=400, detail="Too many failed attempts. Please request a new OTP.")

    if otp.code != code:
        await db.commit()
        remaining = MAX_ATTEMPTS - otp.attempts
        raise HTTPException(status_code=400, detail=f"Invalid OTP. {remaining} attempts remaining.")

    otp.is_used = True
    await db.commit()
    return True
