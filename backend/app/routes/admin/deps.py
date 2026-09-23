"""
Shared admin authentication dependency.
"""
from fastapi import Request, HTTPException
from app.utils.jwt import decode_token


async def require_admin(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_token(auth.split(" ")[1])
    if payload.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return payload
