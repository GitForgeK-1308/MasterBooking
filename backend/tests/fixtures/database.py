from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config import settings
from src.database.models import Base

TEST_DATABASE_URL = make_url(
    settings.database_url
).set(
    database="masterbooking_test"
)


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)


@pytest.fixture(
    scope="session",
)
async def prepare_test_database():
    async with test_engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all
        )
        await connection.run_sync(
            Base.metadata.create_all
        )

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all
        )

    await test_engine.dispose()


@pytest.fixture
async def db_session(
    prepare_test_database,
) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()