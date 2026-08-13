import time
import uuid
from typing import List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

from src.exceptions.db import DBCrudException, NotFoundException
from src.repos.database.models import ClientModel
from src.utils.time_utils import calculate_new_unix_expiry_time_month


async def enable_and_prolong_client_by_user_tg_id(
        client: ClientModel,
        session: AsyncSession
) -> None:
    current_time = int(time.time())

    new_exp_time = calculate_new_unix_expiry_time_month(
        first_unix_time=current_time,
        month_ahead=1
    )

    # try:
    update_query = (
        update(ClientModel)
        .where(ClientModel.id == client.id)
        .values(enable=True, expiry_time=new_exp_time)
    )
    await session.execute(update_query)
    #
    # except SQLAlchemyError:
    #     raise DBCrudException


