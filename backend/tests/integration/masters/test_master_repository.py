import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.masters.models import Master
from src.masters.repository import MasterRepository
from src.users.models import User


def make_master(
    *,
    first_name: str = "Anna",
    last_name: str = "Petrova",
    user_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> Master:
    return Master(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        description="Professional beauty master.",
        experience=5,
        education="Beauty Academy",
        address="Main Street 10",
        is_active=is_active,
    )


@pytest.mark.anyio
async def test_create_master(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    master = make_master()

    result = await repository.create(
        master
    )

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )
    assert result.first_name == "Anna"
    assert result.last_name == "Petrova"
    assert result.description == (
        "Professional beauty master."
    )
    assert result.experience == 5
    assert result.education == "Beauty Academy"
    assert result.address == "Main Street 10"
    assert result.is_active is True


@pytest.mark.anyio
async def test_get_all_masters_sorted(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    await repository.create(
        make_master(
            first_name="Zane",
            last_name="Andersone",
        )
    )

    await repository.create(
        make_master(
            first_name="Anna",
            last_name="Petrova",
        )
    )

    await repository.create(
        make_master(
            first_name="Anna",
            last_name="Andersone",
            is_active=False,
        )
    )

    result = await repository.get_all()

    assert [
        (
            master.last_name,
            master.first_name,
        )
        for master in result
    ] == [
        (
            "Andersone",
            "Anna",
        ),
        (
            "Andersone",
            "Zane",
        ),
        (
            "Petrova",
            "Anna",
        ),
    ]


@pytest.mark.anyio
async def test_get_active_masters(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    await repository.create(
        make_master(
            first_name="Anna",
            last_name="Petrova",
        )
    )

    await repository.create(
        make_master(
            first_name="Irina",
            last_name="Andersone",
        )
    )

    inactive_master = await repository.create(
        make_master(
            first_name="Maria",
            last_name="Sidorova",
            is_active=False,
        )
    )

    result = await repository.get_active()

    assert [
        (
            master.last_name,
            master.first_name,
        )
        for master in result
    ] == [
        (
            "Andersone",
            "Irina",
        ),
        (
            "Petrova",
            "Anna",
        ),
    ]

    assert all(
        master.is_active
        for master in result
    )

    assert inactive_master.id not in {
        master.id
        for master in result
    }


@pytest.mark.anyio
async def test_get_master_by_id(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    master = await repository.create(
        make_master()
    )

    master_id = master.id

    db_session.expunge(
        master
    )

    result = await repository.get_by_id(
        master_id
    )

    assert result is not None
    assert result.id == master_id
    assert result.first_name == "Anna"
    assert result.last_name == "Petrova"


@pytest.mark.anyio
async def test_get_master_by_id_not_found(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    result = await repository.get_by_id(
        uuid.uuid4()
    )

    assert result is None


@pytest.mark.anyio
async def test_get_master_by_user_id(
    db_session: AsyncSession,
    user: User,
):
    repository = MasterRepository(
        db_session
    )

    master = await repository.create(
        make_master(
            first_name=user.first_name,
            last_name=user.last_name,
            user_id=user.id,
        )
    )

    master_id = master.id

    db_session.expunge(
        master
    )

    result = await repository.get_by_user_id(
        user.id
    )

    assert result is not None
    assert result.id == master_id
    assert result.user_id == user.id

    assert result.user is not None
    assert result.user.id == user.id

    assert result.phone == user.phone

    if user.avatar_storage_key is None:
        assert result.avatar_url is None
    else:
        assert (
            result.avatar_url
            == f"/uploads/{user.avatar_storage_key}"
        )


@pytest.mark.anyio
async def test_get_master_by_user_id_not_found(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    result = await repository.get_by_user_id(
        uuid.uuid4()
    )

    assert result is None


@pytest.mark.anyio
async def test_update_master(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    master = await repository.create(
        make_master()
    )

    master.first_name = "Maria"
    master.description = "Updated description."
    master.experience = 10
    master.education = "Updated Academy"
    master.address = "New Street 20"
    master.is_active = False

    result = await repository.update(
        master
    )

    assert result.first_name == "Maria"
    assert (
        result.description
        == "Updated description."
    )
    assert result.experience == 10
    assert result.education == "Updated Academy"
    assert result.address == "New Street 20"
    assert result.is_active is False

    master_id = result.id

    db_session.expunge(
        result
    )

    master_from_database = (
        await repository.get_by_id(
            master_id
        )
    )

    assert master_from_database is not None
    assert (
        master_from_database.first_name
        == "Maria"
    )
    assert (
        master_from_database.description
        == "Updated description."
    )
    assert (
        master_from_database.experience
        == 10
    )
    assert (
        master_from_database.education
        == "Updated Academy"
    )
    assert (
        master_from_database.address
        == "New Street 20"
    )
    assert (
        master_from_database.is_active
        is False
    )


@pytest.mark.anyio
async def test_delete_master(
    db_session: AsyncSession,
):
    repository = MasterRepository(
        db_session
    )

    master = await repository.create(
        make_master()
    )

    master_id = master.id

    await repository.delete(
        master
    )

    result = await repository.get_by_id(
        master_id
    )

    assert result is None