import uuid
from unittest.mock import AsyncMock

import pytest

from src.tags.exceptions import (
    TagAlreadyExistsError,
    TagNotFoundError,
)
from src.tags.models import Tag
from src.tags.repository import TagRepository
from src.tags.schemas import (
    TagCreate,
    TagUpdate,
)
from src.tags.service import TagService


def make_tag(
    *,
    name: str = "Hair",
    slug: str = "hair",
    is_active: bool = True,
) -> Tag:
    return Tag(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        is_active=is_active,
    )


@pytest.fixture
def tag_repository() -> AsyncMock:
    return AsyncMock(spec=TagRepository)


@pytest.fixture
def tag_service(
    tag_repository: AsyncMock,
) -> TagService:
    return TagService(repository=tag_repository)


@pytest.mark.anyio
async def test_get_tags(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tags = [
        make_tag(),
        make_tag(
            name="Nails",
            slug="nails",
        ),
    ]

    tag_repository.get_active.return_value = tags

    result = await tag_service.get_tags()

    assert result == tags

    tag_repository.get_active.assert_awaited_once_with()


@pytest.mark.anyio
async def test_get_all_tags(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tags = [
        make_tag(),
        make_tag(
            name="Massage",
            slug="massage",
            is_active=False,
        ),
    ]

    tag_repository.get_all.return_value = tags

    result = await tag_service.get_all_tags()

    assert result == tags

    tag_repository.get_all.assert_awaited_once_with()


@pytest.mark.anyio
async def test_create_tag(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    data = TagCreate(
        name="  Hair   Styling  ",
        slug=" HAIR-STYLING ",
    )

    tag_repository.get_by_name.return_value = None
    tag_repository.get_by_slug.return_value = None
    tag_repository.create.side_effect = lambda tag: tag

    result = await tag_service.create_tag(data)

    assert result.name == "Hair Styling"
    assert result.slug == "hair-styling"

    tag_repository.get_by_name.assert_awaited_once_with("Hair Styling")

    tag_repository.get_by_slug.assert_awaited_once_with("hair-styling")

    tag_repository.create.assert_awaited_once_with(result)


@pytest.mark.anyio
async def test_create_tag_duplicate_name(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    existing_tag = make_tag()

    tag_repository.get_by_name.return_value = existing_tag

    data = TagCreate(
        name="  Hair ",
        slug="other",
    )

    with pytest.raises(TagAlreadyExistsError):
        await tag_service.create_tag(data)

    tag_repository.get_by_name.assert_awaited_once_with("Hair")

    tag_repository.get_by_slug.assert_not_awaited()
    tag_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_tag_duplicate_slug(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    existing_tag = make_tag()

    tag_repository.get_by_name.return_value = None
    tag_repository.get_by_slug.return_value = existing_tag

    data = TagCreate(
        name="Other",
        slug=" HAIR ",
    )

    with pytest.raises(TagAlreadyExistsError):
        await tag_service.create_tag(data)

    tag_repository.get_by_slug.assert_awaited_once_with("hair")

    tag_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_update_tag_not_found(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tag_id = uuid.uuid4()

    tag_repository.get_by_id.return_value = None

    data = TagUpdate(name="Hair")

    with pytest.raises(TagNotFoundError):
        await tag_service.update_tag(
            tag_id=tag_id,
            data=data,
        )

    tag_repository.get_by_id.assert_awaited_once_with(tag_id)

    tag_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_tag(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tag = make_tag()

    tag_repository.get_by_id.return_value = tag
    tag_repository.get_by_name.return_value = None
    tag_repository.get_by_slug.return_value = None
    tag_repository.update.side_effect = lambda tag: tag

    data = TagUpdate(
        name="  Hair   Design ",
        slug=" HAIR-DESIGN ",
        is_active=False,
    )

    result = await tag_service.update_tag(
        tag_id=tag.id,
        data=data,
    )

    assert result is tag
    assert tag.name == "Hair Design"
    assert tag.slug == "hair-design"
    assert tag.is_active is False

    tag_repository.get_by_name.assert_awaited_once_with("Hair Design")

    tag_repository.get_by_slug.assert_awaited_once_with("hair-design")

    tag_repository.update.assert_awaited_once_with(tag)


@pytest.mark.anyio
async def test_update_tag_duplicate_name(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tag = make_tag()

    existing_tag = make_tag(
        name="Nails",
        slug="nails",
    )

    tag_repository.get_by_id.return_value = tag
    tag_repository.get_by_name.return_value = existing_tag

    data = TagUpdate(name="Nails")

    with pytest.raises(TagAlreadyExistsError):
        await tag_service.update_tag(
            tag_id=tag.id,
            data=data,
        )

    tag_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_tag_duplicate_slug(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tag = make_tag()

    existing_tag = make_tag(
        name="Nails",
        slug="nails",
    )

    tag_repository.get_by_id.return_value = tag
    tag_repository.get_by_slug.return_value = existing_tag

    data = TagUpdate(slug="nails")

    with pytest.raises(TagAlreadyExistsError):
        await tag_service.update_tag(
            tag_id=tag.id,
            data=data,
        )

    tag_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_tag_allows_same_name_and_slug(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tag = make_tag()

    tag_repository.get_by_id.return_value = tag
    tag_repository.get_by_name.return_value = tag
    tag_repository.get_by_slug.return_value = tag
    tag_repository.update.side_effect = lambda tag: tag

    data = TagUpdate(
        name="  Hair ",
        slug=" HAIR ",
    )

    result = await tag_service.update_tag(
        tag_id=tag.id,
        data=data,
    )

    assert result is tag
    assert tag.name == "Hair"
    assert tag.slug == "hair"

    tag_repository.update.assert_awaited_once_with(tag)


@pytest.mark.anyio
async def test_deactivate_tag(
    tag_service: TagService,
    tag_repository: AsyncMock,
):
    tag = make_tag()

    tag_repository.get_by_id.return_value = tag
    tag_repository.update.side_effect = lambda tag: tag

    data = TagUpdate(is_active=False)

    result = await tag_service.update_tag(
        tag_id=tag.id,
        data=data,
    )

    assert result is tag
    assert tag.is_active is False

    tag_repository.get_by_name.assert_not_awaited()
    tag_repository.get_by_slug.assert_not_awaited()

    tag_repository.update.assert_awaited_once_with(tag)
