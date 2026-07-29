from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.dtos.schemas import NewUserSchema
from src.exceptions.db import ClientAlreadyExists
from src.dtos.schemas import NewClientSchema
from src.repos.database.models import ClientModel, UserModel


async def add_new_client_to_db(
        new_client: NewClientSchema,
        session: AsyncSession
) -> ClientModel:
    # client_data = new_client.model_dump()

    fields_to_exclude = {"limit_ip"}

    client_db_data = new_client.client.model_dump(exclude=fields_to_exclude)

    client = ClientModel(**client_db_data)

    session.add(client)

    try:
        await session.commit()
        await session.refresh(client)
    except IntegrityError as e:
        await session.rollback()
        raise ClientAlreadyExists

    return client


async def add_new_user_to_db(
        new_user: NewUserSchema,
        session: AsyncSession
) -> UserModel:
    user = UserModel(**new_user.model_dump())
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException

    return user


async def add_new_user_to_session(
        new_user: NewUserSchema,
        session: AsyncSession
) -> UserModel:
    user = UserModel(**new_user.model_dump())
    session.add(user)
    return user


async def add_new_user_to_db_without_commit(
        new_user: NewUserSchema,
        session: AsyncSession
) -> UserModel:
    user = UserModel(**new_user.model_dump())
    session.add(user)
    try:
        await session.flush()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException

    return user

