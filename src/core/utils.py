import secrets
import string

from src.config.settings import settings


def build_vpn_subscription_link_from_params(
        domain: str,
        port: int,
        prefix: str,
        sub_id: str
) -> str:
    return f"{domain}:{port}/{prefix}/{sub_id}"


def create_referral_code(length: int = settings.referral.code_length) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

