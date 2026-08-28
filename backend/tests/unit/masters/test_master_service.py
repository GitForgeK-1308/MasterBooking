import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.locations.service import LocationService
from src.masters.exceptions import (
    MasterProfileAlreadyExistsError,
)
from src.masters.models import Master
from src.masters.repository import MasterRepository
from src.masters.schemas import (
    MasterCreate,
    MasterProfileCreate,
    MasterUpdate,
)
from src.masters.service import MasterService
from src.users.models import User, UserRole


def make_master(
    *,
    city_id: uuid.UUID | None = None,
    district_id: uuid.UUID | None = None,
    city: str | None = None,
    district: str | None = None,
) -> Master:
    return Master(
        id=uuid.uuid4(),
        first_name="Anna",
        last_name="Petrova",
        description="Professional master.",
        experience=5,
        education="Beauty Academy",
        city_id=city_id,
        district_id=district_id,
        city=city,
        district=district,
        address="Main Street 10",
        is_active=True,
    )


def make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="client@example.com",
        hashed_password="hashed-password",
        first_name="Anna",
        last_name="Petrova",
        is_active=True,
    )


@pytest.fixture
def master_repository() -> AsyncMock:
    return AsyncMock(spec=MasterRepository)


@pytest.fixture
def location_service() -> AsyncMock:
    return AsyncMock(spec=LocationService)


@pytest.fixture
def master_service(
    master_repository: AsyncMock,
    location_service: AsyncMock,
) -> MasterService:
    return MasterService(
        repository=master_repository,
        location_service=location_service,
    )


@pytest.mark.anyio
async def test_get_master_by_id(
    master_service: MasterService,
    master_repository: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = master

    result = await master_service.get_master_by_id(master.id)

    assert result is master

    master_repository.get_by_id.assert_awaited_once_with(master.id)


@pytest.mark.anyio
async def test_get_masters(
    master_service: MasterService,
    master_repository: AsyncMock,
):
    masters = [
        make_master(),
        make_master(),
    ]

    master_repository.get_active.return_value = masters

    result = await master_service.get_masters()

    assert result == masters

    master_repository.get_active.assert_awaited_once_with()


@pytest.mark.anyio
async def test_create_master_without_location(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    data = MasterCreate(
        first_name="Anna",
        last_name="Petrova",
        description="Professional master.",
        experience=5,
        education="Beauty Academy",
        address="Main Street 10",
    )

    master_repository.create.side_effect = lambda master: master

    result = await master_service.create_master(data)

    assert result.first_name == "Anna"
    assert result.last_name == "Petrova"
    assert result.description == "Professional master."
    assert result.experience == 5
    assert result.education == "Beauty Academy"
    assert result.city_id is None
    assert result.district_id is None
    assert result.city is None
    assert result.district is None
    assert result.address == "Main Street 10"

    location_service.validate_location.assert_not_awaited()

    master_repository.create.assert_awaited_once_with(result)


@pytest.mark.anyio
async def test_create_master_with_location(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    city_id = uuid.uuid4()
    district_id = uuid.uuid4()

    city = SimpleNamespace(
        id=city_id,
        name="Riga",
    )

    district = SimpleNamespace(
        id=district_id,
        name="Centrs",
    )

    location_service.validate_location.return_value = (
        city,
        district,
    )

    master_repository.create.side_effect = lambda master: master

    data = MasterCreate(
        first_name="Anna",
        last_name="Petrova",
        description="Professional master.",
        experience=5,
        education="Beauty Academy",
        city_id=city_id,
        district_id=district_id,
        address="Main Street 10",
    )

    result = await master_service.create_master(data)

    assert result.city_id == city_id
    assert result.district_id == district_id
    assert result.city == "Riga"
    assert result.district == "Centrs"

    location_service.validate_location.assert_awaited_once_with(
        city_id=city_id,
        district_id=district_id,
    )

    master_repository.create.assert_awaited_once_with(result)


@pytest.mark.anyio
async def test_create_master_requires_city_and_district(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    city_id = uuid.uuid4()

    data = MasterCreate(
        first_name="Anna",
        last_name="Petrova",
        description="Professional master.",
        experience=5,
        education="Beauty Academy",
        city_id=city_id,
    )

    with pytest.raises(
        ValueError,
        match="Город и район должны быть выбраны вместе.",
    ):
        await master_service.create_master(data)

    location_service.validate_location.assert_not_awaited()
    master_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_update_master_not_found(
    master_service: MasterService,
    master_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = None

    result = await master_service.update_master(
        master_id=master_id,
        data=MasterUpdate(experience=10),
    )

    assert result is None

    master_repository.get_by_id.assert_awaited_once_with(master_id)
    master_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_master(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = master
    master_repository.update.side_effect = lambda master: master

    data = MasterUpdate(
        first_name="Maria",
        description="Updated description.",
        experience=10,
        education="Updated Academy",
        address=None,
    )

    result = await master_service.update_master(
        master_id=master.id,
        data=data,
    )

    assert result is master
    assert master.first_name == "Maria"
    assert master.last_name == "Petrova"
    assert master.description == "Updated description."
    assert master.experience == 10
    assert master.education == "Updated Academy"
    assert master.address is None

    location_service.validate_location.assert_not_awaited()

    master_repository.update.assert_awaited_once_with(master)


@pytest.mark.anyio
async def test_update_master_does_not_clear_required_fields_with_none(
    master_service: MasterService,
    master_repository: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = master
    master_repository.update.side_effect = lambda master: master

    data = MasterUpdate(
        first_name=None,
        last_name=None,
        description=None,
        experience=None,
        education=None,
    )

    result = await master_service.update_master(
        master_id=master.id,
        data=data,
    )

    assert result is master
    assert master.first_name == "Anna"
    assert master.last_name == "Petrova"
    assert master.description == "Professional master."
    assert master.experience == 5
    assert master.education == "Beauty Academy"

    master_repository.update.assert_awaited_once_with(master)


@pytest.mark.anyio
async def test_update_master_location(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    old_city_id = uuid.uuid4()
    old_district_id = uuid.uuid4()

    master = make_master(
        city_id=old_city_id,
        district_id=old_district_id,
        city="Riga",
        district="Centrs",
    )

    new_city_id = uuid.uuid4()
    new_district_id = uuid.uuid4()

    city = SimpleNamespace(
        id=new_city_id,
        name="Jurmala",
    )

    district = SimpleNamespace(
        id=new_district_id,
        name="Majori",
    )

    master_repository.get_by_id.return_value = master
    master_repository.update.side_effect = lambda master: master

    location_service.validate_location.return_value = (
        city,
        district,
    )

    data = MasterUpdate(
        city_id=new_city_id,
        district_id=new_district_id,
    )

    result = await master_service.update_master(
        master_id=master.id,
        data=data,
    )

    assert result is master
    assert master.city_id == new_city_id
    assert master.district_id == new_district_id
    assert master.city == "Jurmala"
    assert master.district == "Majori"

    location_service.validate_location.assert_awaited_once_with(
        city_id=new_city_id,
        district_id=new_district_id,
    )


@pytest.mark.anyio
async def test_update_master_can_clear_location(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    master = make_master(
        city_id=uuid.uuid4(),
        district_id=uuid.uuid4(),
        city="Riga",
        district="Centrs",
    )

    master_repository.get_by_id.return_value = master
    master_repository.update.side_effect = lambda master: master

    data = MasterUpdate(
        city_id=None,
        district_id=None,
    )

    result = await master_service.update_master(
        master_id=master.id,
        data=data,
    )

    assert result is master
    assert master.city_id is None
    assert master.district_id is None
    assert master.city is None
    assert master.district is None

    location_service.validate_location.assert_not_awaited()


@pytest.mark.anyio
async def test_update_master_partial_city_uses_current_district(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    old_city_id = uuid.uuid4()
    district_id = uuid.uuid4()

    master = make_master(
        city_id=old_city_id,
        district_id=district_id,
        city="Riga",
        district="Centrs",
    )

    new_city_id = uuid.uuid4()

    city = SimpleNamespace(
        id=new_city_id,
        name="Jurmala",
    )

    district = SimpleNamespace(
        id=district_id,
        name="Centrs",
    )

    master_repository.get_by_id.return_value = master
    master_repository.update.side_effect = lambda master: master

    location_service.validate_location.return_value = (
        city,
        district,
    )

    result = await master_service.update_master(
        master_id=master.id,
        data=MasterUpdate(city_id=new_city_id),
    )

    assert result is master

    location_service.validate_location.assert_awaited_once_with(
        city_id=new_city_id,
        district_id=district_id,
    )

    assert master.city_id == new_city_id
    assert master.district_id == district_id
    assert master.city == "Jurmala"
    assert master.district == "Centrs"


@pytest.mark.anyio
async def test_update_master_requires_complete_location(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = master

    city_id = uuid.uuid4()

    with pytest.raises(
        ValueError,
        match="Город и район должны быть выбраны вместе.",
    ):
        await master_service.update_master(
            master_id=master.id,
            data=MasterUpdate(city_id=city_id),
        )

    location_service.validate_location.assert_not_awaited()
    master_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_master(
    master_service: MasterService,
    master_repository: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = master

    result = await master_service.delete_master(master.id)

    assert result is True

    master_repository.get_by_id.assert_awaited_once_with(master.id)

    master_repository.delete.assert_awaited_once_with(master)


@pytest.mark.anyio
async def test_delete_master_not_found(
    master_service: MasterService,
    master_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = None

    result = await master_service.delete_master(master_id)

    assert result is None

    master_repository.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_create_master_profile(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    current_user = make_user()

    master_repository.get_by_user_id.return_value = None
    master_repository.create.side_effect = lambda master: master

    data = MasterProfileCreate(
        description=("Professional beauty specialist."),
        experience=5,
        education="Beauty Academy",
        address="Main Street 10",
    )

    result = await master_service.create_master_profile(
        current_user=current_user,
        data=data,
    )

    assert result.user_id == current_user.id
    assert result.first_name == current_user.first_name
    assert result.last_name == current_user.last_name
    assert result.description == data.description
    assert result.experience == 5
    assert result.education == "Beauty Academy"
    assert result.city_id is None
    assert result.district_id is None
    assert result.address == "Main Street 10"

    assert current_user.role == UserRole.MASTER

    location_service.validate_location.assert_not_awaited()

    master_repository.create.assert_awaited_once_with(result)


@pytest.mark.anyio
async def test_create_master_profile_with_location(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    current_user = make_user()

    city_id = uuid.uuid4()
    district_id = uuid.uuid4()

    city = SimpleNamespace(
        id=city_id,
        name="Riga",
    )

    district = SimpleNamespace(
        id=district_id,
        name="Centrs",
    )

    master_repository.get_by_user_id.return_value = None

    location_service.validate_location.return_value = (
        city,
        district,
    )

    master_repository.create.side_effect = lambda master: master

    data = MasterProfileCreate(
        description=("Professional beauty specialist."),
        experience=5,
        education="Beauty Academy",
        city_id=city_id,
        district_id=district_id,
        address="Main Street 10",
    )

    result = await master_service.create_master_profile(
        current_user=current_user,
        data=data,
    )

    assert result.city_id == city_id
    assert result.district_id == district_id
    assert result.city == "Riga"
    assert result.district == "Centrs"
    assert current_user.role == UserRole.MASTER

    location_service.validate_location.assert_awaited_once_with(
        city_id=city_id,
        district_id=district_id,
    )


@pytest.mark.anyio
async def test_create_master_profile_duplicate(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    current_user = make_user()
    existing_master = make_master()

    master_repository.get_by_user_id.return_value = existing_master

    data = MasterProfileCreate(
        description=("Professional beauty specialist."),
        experience=5,
        education="Beauty Academy",
    )

    with pytest.raises(MasterProfileAlreadyExistsError):
        await master_service.create_master_profile(
            current_user=current_user,
            data=data,
        )

    location_service.validate_location.assert_not_awaited()
    master_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_master_profile_requires_city_and_district(
    master_service: MasterService,
    master_repository: AsyncMock,
    location_service: AsyncMock,
):
    current_user = make_user()

    master_repository.get_by_user_id.return_value = None

    data = MasterProfileCreate(
        description=("Professional beauty specialist."),
        experience=5,
        education="Beauty Academy",
        city_id=uuid.uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="Город и район должны быть выбраны вместе.",
    ):
        await master_service.create_master_profile(
            current_user=current_user,
            data=data,
        )

    location_service.validate_location.assert_not_awaited()
    master_repository.create.assert_not_awaited()
