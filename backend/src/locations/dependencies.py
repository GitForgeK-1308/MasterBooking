from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_async_session
from src.locations.repository import LocationRepository
from src.locations.service import LocationService


def get_location_service(
    session: AsyncSession = Depends(get_async_session),
) -> LocationService:
    repository = LocationRepository(session)

    return LocationService(repository=repository)
