from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dtos.schemas import ClientUpdateSchema
from src.exceptions.db import DBCrudException
from src.repos.database.models import ClientModel, UserModel


async def update_db_client(
        updated_client: ClientUpdateSchema,
        session: AsyncSession
) -> None:
    new_client_data = updated_client.model_dump(exclude={"tg_id", "email"})

    query = (update(ClientModel)
             .where(ClientModel.email == updated_client.email)
             .values(new_client_data)
    )

    try:
        await session.execute(query)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException


async def update_trial_availability(
        user_tg_id: int,
        valid_for_trial: bool,
        trial_used: int,
        session: AsyncSession
):
    query = (update(UserModel)
             .where(UserModel.tg_id == user_tg_id)
             .values(
                valid_for_trial=valid_for_trial,
                trial_used=trial_used
             )
    )

    try:
        await session.execute(query)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException
