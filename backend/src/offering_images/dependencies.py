from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_async_session
from src.master_offering.repository import MasterOfferingRepository
from src.offering_images.repository import OfferingImageRepository
from src.offering_images.service import OfferingImageService
from src.offering_images.storage import LocalImageStorage


def get_offering_image_service(
    session: AsyncSession = Depends(
        get_async_session
    ),
) -> OfferingImageService:
    image_repository = OfferingImageRepository(
        session
    )

    offering_repository = MasterOfferingRepository(
        session
    )

    storage = LocalImageStorage()

    return OfferingImageService(
        repository=image_repository,
        offering_repository=offering_repository,
        storage=storage,
    )