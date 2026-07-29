import time
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from src.core.utils import create_referral_code


class ClientDetailSchema(BaseModel):
    email: str  # email - название клиента. использоать tg-id!!!
    creation_time: Optional[int] = Field(default_factory=lambda: int(time.time()))
    total_gb: int = Field(..., validation_alias="total_gb", serialization_alias="totalGB")
    expiry_time: int = Field(..., validation_alias="expiry_time", serialization_alias="expiryTime")
    tg_id: int = Field(0, validation_alias="tg_id", serialization_alias="tgId")
    limit_ip: int = Field(0, validation_alias="limit_ip", serialization_alias="limitIp")
    enable: bool = True

    class Config:
        populate_by_name = True

class NewClientSchema(BaseModel):
    client: ClientDetailSchema
    inbound_ids: List[int] = Field(..., validation_alias="inbound_ids", serialization_alias="inboundIds")

    class Config:
        populate_by_name = True


class ClientUpdateSchema(BaseModel):
    email: Optional[str] = None
    total_gb: Optional[int] = Field(None, validation_alias="total_gb", serialization_alias="totalGB")
    expiry_time: Optional[int] = Field(None, validation_alias="expiry_time", serialization_alias="expiryTime")
    tg_id: Optional[int] = Field(0, validation_alias="tg_id", serialization_alias="tgId")
    enable: Optional[bool] = True


class DisableClientSchema(BaseModel):
    email: str


class NewUserSchema(BaseModel):
    tg_id: int
    referrer_id: Optional[int] = None
    balance: int
    ref_code: Optional[str] = Field(default_factory=lambda: create_referral_code())


class TelegramAuthSchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class PaymentRecordSchema(BaseModel):
    tg_id: int
    item_id: str
    time: int
    amount: int | float


class PromoCodeSchema(BaseModel):
    code: str
    bonus_amount: int
    expiry_time: Optional[int] = Field(default=999999999999999999)
    activations_left: int
    enable: bool = Field(default=True)


class PromoCodeActivationRecordSchema(BaseModel):
    tg_id: int
    promo_id: uuid.UUID
    time: int = Field(default_factory=lambda: int(time.time()))


class ReferralActivationSchema(BaseModel):
    referrer_tg_id: int
    referred_tg_id: int
    referral_code: str
