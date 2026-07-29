from sqlalchemy.ext.asyncio import AsyncSession

from src.payments.balance import update_balance_outside_payment
from src.config.settings import settings
from src.dtos.schemas import NewUserSchema
from src.repos.database.crud.creation import add_new_user_to_session
from src.exceptions.referrals import UserAlreadyExistsException
from src.repos.database.crud.basic_utils import user_existence_by_tg_id
from src.exceptions.actions import DBActionException
from src.exceptions.db import DBCrudException
from src.repos.database.crud.referral import add_referral_record_to_db
from src.dtos.schemas import ReferralActivationSchema


async def activate_referral(
        referral: ReferralActivationSchema,
        db_session: AsyncSession
) -> None:
    user_exists = await user_existence_by_tg_id(
        tg_id=referral.referred_tg_id,
        session=db_session
    )

    if user_exists:
        raise UserAlreadyExistsException
    else:
        try:
            await add_new_user_to_session(
                new_user=NewUserSchema(
                    tg_id=referral.referred_tg_id,
                    referrer_id=referral.referrer_tg_id,
                    balance=14
                ),
                session=db_session
            )

            await add_referral_record_to_db(
                referral=referral,
                session=db_session
            )
            await update_balance_outside_payment(
                user_tg_id=referral.referrer_tg_id,
                stars_amount=settings.referral.referrer_bonus,
                session=db_session
            )

        except DBCrudException:
            raise DBActionException
