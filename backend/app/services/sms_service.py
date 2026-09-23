"""
SMS provider abstraction with mock implementation for demo mode.
"""
import logging
from abc import ABC, abstractmethod
from app.config.settings import settings

logger = logging.getLogger(__name__)


class SMSProvider(ABC):
    @abstractmethod
    async def send_sms(self, mobile: str, message: str) -> bool:
        pass


class MockSMSProvider(SMSProvider):
    """Console-based mock for development/demo mode."""

    async def send_sms(self, mobile: str, message: str) -> bool:
        logger.info(f"\n{'='*50}")
        logger.info(f"📱 MOCK SMS TO: {mobile}")
        logger.info(f"MESSAGE: {message}")
        logger.info(f"{'='*50}\n")
        print(f"\n{'='*50}")
        print(f"📱 MOCK SMS TO: {mobile}")
        print(f"MESSAGE: {message}")
        print(f"{'='*50}\n")
        return True


class MSG91Provider(SMSProvider):
    """MSG91 SMS provider stub — wire up API key when ready."""

    async def send_sms(self, mobile: str, message: str) -> bool:
        import httpx
        # TODO: Replace with actual MSG91 API call
        url = "https://api.msg91.com/api/sendhttp.php"
        params = {
            "authkey": settings.SMS_API_KEY,
            "mobiles": mobile,
            "message": message,
            "sender": settings.SMS_SENDER_ID,
            "route": "4",
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"MSG91 SMS failed: {e}")
            return False


def get_sms_provider() -> SMSProvider:
    provider = settings.SMS_PROVIDER.lower()
    if provider == "msg91":
        return MSG91Provider()
    return MockSMSProvider()


async def send_otp_sms(mobile: str, otp: str) -> bool:
    provider = get_sms_provider()
    message = (
        f"Tikka Masala Chat Corner: Your verification OTP is {otp}. "
        f"Valid for 10 minutes. Do not share with anyone."
    )
    return await provider.send_sms(mobile, message)


async def send_delivery_otp_sms(mobile: str, otp: str) -> bool:
    provider = get_sms_provider()
    message = (
        f"Tikka Masala Chat Corner: Your delivery verification OTP is {otp}. "
        f"Share this OTP with the delivery person when receiving your order."
    )
    return await provider.send_sms(mobile, message)
