import asyncio
from contextlib import asynccontextmanager
import aiohttp
from sqlalchemy import update, select, func

from src.backend_logging import logger
from src.repos.database.get_session import get_db_session
from src.dtos.schemas import ClientUpdateSchema
from src.core.clients.update_client import update_vpn_client
from src.repos.database.models import ClientModel, UserModel


async def run_daily_billing(daily_cost: int = 2):
    session_context = asynccontextmanager(get_db_session)

    async with session_context() as session:
        logger.info("[BILLING_SCRIPT] Старт биллинга...")
        active_cnt_subquery = (
            select(func.count(ClientModel.id))
            .where(
                ClientModel.tg_id == UserModel.tg_id,
                ClientModel.enable == True
            )
            .scalar_subquery()
        )

        balance_minimized = await session.execute(
            update(UserModel)
            .where(active_cnt_subquery > 0)
            .values(balance=UserModel.balance - (daily_cost * active_cnt_subquery))
        )
        logger.info(f"[BILLING_SCRIPT] Изменено строк в UserModel: {balance_minimized.rowcount}")

        zero_balance_users = await session.scalars(
            select(UserModel.tg_id).where(UserModel.balance <= 0)
        )
        zero_balance_users_list = zero_balance_users.all()

        if zero_balance_users_list:
            turned_off = await session.execute(
                update(ClientModel)
                .where(
                    ClientModel.tg_id.in_(zero_balance_users_list),
                    ClientModel.enable == True
                )
                .values(enable=False)
                .returning(ClientModel.email)
            )

            disabled_emails = turned_off.scalars().all()
            logger.info(f"[BILLING_SCRIPT] Отключено клиентов в БД: {len(disabled_emails)}")

            if disabled_emails:
                async with aiohttp.ClientSession() as http_session:
                    for email in disabled_emails:
                        logger.info(f"[BILLING_SCRIPT] Отправка запроса на отключение VPN для: {email}")
                        try:
                            await update_vpn_client(
                                session=http_session,
                                email=email,
                                updated_client=ClientUpdateSchema(enable=False)
                            )
                        except Exception as e:
                            logger.info(f"[BILLING_SCRIPT] Ошибка при отключении {email}: {e}")

        await session.commit()
        logger.info("[BILLING_SCRIPT] Транзакция успешно зафиксирована.")


if __name__ == "__main__":
    asyncio.run(run_daily_billing())
