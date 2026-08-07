from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.api_security import APISecurityConfig
from src.config.crypto import CryptoConfig
from src.config.game import DailyGameConfig
from src.config.rmq import RabbitMQConfig
from src.config.referral import ReferralProgramConfig
from src.config.logs import LoggingConfig
from src.config.payment import PaymentConfig
from src.config.bot import TgBotConfig
from src.config.VPNPanelConfig import VPNPanelConfig
from src.config.db import DBConfig
from src.config.app import AppConfig


class Settings(BaseSettings):
    db: DBConfig
    app: AppConfig = Field(default_factory=AppConfig)
    vpn_panel: VPNPanelConfig
    bot: TgBotConfig
    payment: PaymentConfig
    logs: LoggingConfig
    referral: ReferralProgramConfig
    rmq: RabbitMQConfig
    crypto: CryptoConfig
    game: DailyGameConfig
    api_security: APISecurityConfig
    # api_secret_key: str = "your-super-secret-key-change-it-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

settings = Settings()

