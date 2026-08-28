import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.tags.models import Tag
from src.tags.repository import TagRepository


def make_tag(
    *,
    name: str = "Hair",
    slug: str = "hair",
    is_active: bool = True,
) -> Tag:
    return Tag(
        name=name,
        slug=slug,
        is_active=is_active,
    )


@pytest.mark.anyio
async def test_create_tag(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    tag = make_tag()

    result = await repository.create(tag)

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )
    assert result.name == "Hair"
    assert result.slug == "hair"
    assert result.is_active is True


@pytest.mark.anyio
async def test_get_all_tags_sorted(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    await repository.create(
        make_tag(
            name="Nails",
            slug="nails",
        )
    )

    await repository.create(
        make_tag(
            name="Hair",
            slug="hair",
        )
    )

    await repository.create(
        make_tag(
            name="Massage",
            slug="massage",
            is_active=False,
        )
    )

    result = await repository.get_all()

    assert [tag.name for tag in result] == [
        "Hair",
        "Massage",
        "Nails",
    ]


@pytest.mark.anyio
async def test_get_active_tags(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    await repository.create(
        make_tag(
            name="Nails",
            slug="nails",
        )
    )

    await repository.create(
        make_tag(
            name="Hair",
            slug="hair",
        )
    )

    await repository.create(
        make_tag(
            name="Massage",
            slug="massage",
            is_active=False,
        )
    )

    result = await repository.get_active()

    assert [tag.name for tag in result] == [
        "Hair",
        "Nails",
    ]

    assert all(tag.is_active for tag in result)


@pytest.mark.anyio
async def test_get_tag_by_id(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    tag = await repository.create(make_tag())

    result = await repository.get_by_id(tag.id)

    assert result is not None
    assert result.id == tag.id
    assert result.name == "Hair"


@pytest.mark.anyio
async def test_get_tag_by_id_not_found(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    result = await repository.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.anyio
async def test_get_tag_by_name(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    tag = await repository.create(make_tag())

    result = await repository.get_by_name("Hair")

    assert result is not None
    assert result.id == tag.id
    assert result.name == "Hair"


@pytest.mark.anyio
async def test_get_tag_by_name_not_found(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    result = await repository.get_by_name("Missing")

    assert result is None


@pytest.mark.anyio
async def test_get_tag_by_slug(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    tag = await repository.create(make_tag())

    result = await repository.get_by_slug("hair")

    assert result is not None
    assert result.id == tag.id
    assert result.slug == "hair"


@pytest.mark.anyio
async def test_get_tag_by_slug_not_found(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    result = await repository.get_by_slug("missing")

    assert result is None


@pytest.mark.anyio
async def test_get_tags_by_ids(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    hair = await repository.create(
        make_tag(
            name="Hair",
            slug="hair",
        )
    )

    nails = await repository.create(
        make_tag(
            name="Nails",
            slug="nails",
        )
    )

    await repository.create(
        make_tag(
            name="Massage",
            slug="massage",
        )
    )

    result = await repository.get_by_ids(
        [
            hair.id,
            nails.id,
        ]
    )

    assert {tag.id for tag in result} == {
        hair.id,
        nails.id,
    }


@pytest.mark.anyio
async def test_get_tags_by_ids_empty(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    result = await repository.get_by_ids([])

    assert result == []


@pytest.mark.anyio
async def test_update_tag(
    db_session: AsyncSession,
):
    repository = TagRepository(db_session)

    tag = await repository.create(make_tag())

    tag.name = "Hair Design"
    tag.slug = "hair-design"
    tag.is_active = False

    result = await repository.update(tag)

    assert result.name == "Hair Design"
    assert result.slug == "hair-design"
    assert result.is_active is False

    tag_id = result.id

    db_session.expunge(result)

    tag_from_database = await repository.get_by_id(tag_id)

    assert tag_from_database is not None
    assert tag_from_database.id == tag_id
    assert tag_from_database.name == "Hair Design"
    assert tag_from_database.slug == "hair-design"
    assert tag_from_database.is_active is False
