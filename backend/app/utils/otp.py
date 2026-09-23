"""
OTP generation helper.
"""
import secrets


def generate_otp(length: int = 6) -> str:
    """Generate a secure numeric OTP of given length."""
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])
