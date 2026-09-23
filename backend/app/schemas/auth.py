from pydantic import BaseModel, field_validator
from typing import Optional
import re


class SendOTPRequest(BaseModel):
    mobile: str
    purpose: str = "REGISTRATION"

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        v = v.strip()
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Enter a valid 10-digit Indian mobile number.")
        return v


class VerifyOTPRequest(BaseModel):
    mobile: str
    code: str
    purpose: str = "REGISTRATION"


class RegisterRequest(BaseModel):
    name: str
    mobile: str
    password: str
    confirm_password: str
    otp_verified_token: str  # returned after OTP verify step

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v


class LoginRequest(BaseModel):
    mobile: str
    password: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    mobile: str
    is_verified: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
