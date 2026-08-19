from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.repository import CategoryRepository
from src.database.session import get_async_session
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.master_offering.service import (
    MasterOfferingService,
)
from src.tags.repository import TagRepository


def get_offering_service(
    session: AsyncSession = Depends(
        get_async_session
    ),
) -> MasterOfferingService:
    repository = MasterOfferingRepository(
        session
    )

    category_repository = CategoryRepository(
        session
    )

    tag_repository = TagRepository(
        session
    )

    return MasterOfferingService(
        repository=repository,
        category_repository=category_repository,
        tag_repository=tag_repository,
    )