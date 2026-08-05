import uuid
from typing import List
from sqlalchemy import text, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as SQLAUUID


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False
    )
    ref_code: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
        index=True,
    )
    referrer_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=True
    )
    balance: Mapped[float] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )
    clients: Mapped[List["ClientModel"]] = relationship(
        "ClientModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class ClientModel(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
    )
    creation_time: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )
    tg_id: Mapped[int] = mapped_column(
        ForeignKey("users.tg_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    total_gb: Mapped[int] = mapped_column(BigInteger)
    expiry_time: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )
    enable: Mapped[bool] = mapped_column()

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="clients")


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )
    item_id: Mapped[str] = mapped_column(
        nullable=False,
        index=True
    )
    time: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(
        nullable=False
    )


class PromoCodeModel(Base):
    __tablename__ = "promo"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(
        unique=True,
        index=True
    )
    bonus_amount: Mapped[int] = mapped_column(
        nullable=False
    )
    expiry_time: Mapped[int| None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True
    )
    activations_left: Mapped[int] = mapped_column()
    enable: Mapped[bool] = mapped_column(
        nullable=False
    )
    activations: Mapped[List["PromoActivationRecordModel"]] = relationship(
        "PromoActivationRecordModel",
        back_populates="promo",
        cascade="all, delete-orphan"
    )


class PromoActivationRecordModel(Base):
    __tablename__ = "promo_activations"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )
    time: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    promo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("promo.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    promo: Mapped["PromoCodeModel"] = relationship(
        "PromoCodeModel",
        back_populates="activations"
    )


class ReferralModel(Base):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    referrer_tg_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.tg_id")
    )
    referred_tg_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.tg_id")
    )
    referrer: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[referrer_tg_id]
    )
    referred: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[referred_tg_id]
    )

    __table_args__ = (
        UniqueConstraint("referred_tg_id", name="referred_tg_id_unique"),
    )


class LocalCurrenciesModel(Base):
    __tablename__ = "local_currencies"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    currency_cmd_id: Mapped[int] = mapped_column(
        unique=True,
        index=True
    )
    currency_code: Mapped[str] = mapped_column(
        unique=True,
        index=True
    )
    exchange_rate: Mapped[float] = mapped_column(
        nullable=False
    )


class DailyGameStreakModel(Base):
    __tablename__ = "user_streaks"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        nullable=False,
        unique=True
    )
    streak_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    last_checked_in: Mapped[int] = mapped_column(
        nullable=False
    )

