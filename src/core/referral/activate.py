import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.users import get_user_subscriptions
from src.backend_logging import logger
from src.core.clients.update_client import update_vpn_client
from src.payments.balance import update_balance_outside_payment
from src.config.settings import settings
from src.dtos.schemas import NewUserSchema, ClientUpdateSchema
from src.repos.database.crud.creation import add_new_user_to_session
from src.exceptions.referrals import UserAlreadyExistsException
from src.repos.database.crud.basic_utils import user_existence_by_tg_id
from src.exceptions.actions import DBActionException
from src.exceptions.db import DBCrudException
from src.repos.database.crud.referral import add_referral_record_to_db
from src.dtos.schemas import ReferralActivationSchema
from src.repos.database.crud.update import update_db_client
from src.utils.time_utils import calculate_new_unix_expiry_time_days


async def activate_referral(
        referral: ReferralActivationSchema,
        db_session: AsyncSession,
        http_session: aiohttp.ClientSession,
) -> None:
    user_exists = await user_existence_by_tg_id(
        tg_id=referral.referred_tg_id,
        session=db_session
    )

    if user_exists:
        raise UserAlreadyExistsException
    else:
        try:
            logger.info(1)
            await add_new_user_to_session(
                new_user=NewUserSchema(
                    tg_id=referral.referred_tg_id,
                    referrer_id=referral.referrer_tg_id,
                    balance=0
                ),
                session=db_session
            )
            logger.info(2)
            await add_referral_record_to_db(
                referral=referral,
                session=db_session
            )
            # await update_balance_outside_payment(
            #     user_tg_id=referral.referrer_tg_id,
            #     amount=settings.referral.referrer_bonus,
            #     session=db_session
            # )
            logger.info(3)
            referrer_emails = await get_user_subscriptions(
                tg_id=referral.referrer_tg_id,
                db_session=db_session
            )
            logger.info(4)
            if referrer_emails:
                for sub in referrer_emails:
                    current_sub_exp_time = sub.expiry_time
                    new_exp_time = calculate_new_unix_expiry_time_days(
                        first_unix_time=current_sub_exp_time,
                        days_ahead=1
                    )

                    await update_vpn_client(
                        email=sub.email,
                        updated_client=ClientUpdateSchema(
                            email=sub.email,
                            expiry_time=new_exp_time,
                            total_gb=sub.total_gb,
                            enable=True,
                            tg_id=sub.tg_id
                        ).model_dump(by_alias=True),
                        session=http_session
                    )
                    logger.info(5)

                    await update_db_client(
                        ClientUpdateSchema(
                            email=sub.email,
                            expiry_time=new_exp_time,
                            total_gb=0
                        ),
                        session=db_session
                    )
                    logger.info(6)
            logger.info(7)
        except DBCrudException:
            raise DBActionException
