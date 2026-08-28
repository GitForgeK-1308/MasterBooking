from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_async_session
from src.tags.repository import TagRepository
from src.tags.service import TagService


def get_tag_service(
    session: AsyncSession = Depends(get_async_session),
) -> TagService:
    repository = TagRepository(session)

    return TagService(repository=repository)
