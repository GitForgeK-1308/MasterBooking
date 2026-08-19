from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.repository import CategoryRepository
from src.categories.service import CategoryService
from src.database.session import get_async_session


def get_category_service(
    session: AsyncSession = Depends(
        get_async_session
    ),
) -> CategoryService:
    repository = CategoryRepository(
        session
    )

    return CategoryService(
        repository=repository
    )