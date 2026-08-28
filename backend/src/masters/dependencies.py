from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_async_session
from src.locations.repository import LocationRepository
from src.locations.service import LocationService
from src.masters.repository import MasterRepository
from src.masters.service import MasterService


def get_master_service(
    session: AsyncSession = Depends(get_async_session),
) -> MasterService:
    master_repository = MasterRepository(session)

    location_repository = LocationRepository(session)

    location_service = LocationService(repository=location_repository)

    return MasterService(
        repository=master_repository,
        location_service=location_service,
    )
