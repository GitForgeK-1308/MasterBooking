import uuid
from pathlib import Path

import pytest

from src.offering_images.storage import (
    LocalImageStorage,
)


def test_storage_creates_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    storage = LocalImageStorage()

    assert storage.uploads_dir == Path("uploads")

    assert storage.offerings_dir == Path("uploads/offerings")

    assert storage.uploads_dir.exists()
    assert storage.uploads_dir.is_dir()

    assert storage.offerings_dir.exists()
    assert storage.offerings_dir.is_dir()


@pytest.mark.anyio
async def test_save_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    storage = LocalImageStorage()

    content = b"image-content"

    storage_key = await storage.save(
        content=content,
        extension="png",
    )

    assert storage_key.startswith("offerings/")
    assert storage_key.endswith(".png")

    file_name = Path(storage_key).name

    file_id = Path(file_name).stem

    uuid.UUID(file_id)

    file_path = storage.uploads_dir / storage_key

    assert file_path.exists()
    assert file_path.is_file()

    assert file_path.read_bytes() == content


@pytest.mark.anyio
async def test_save_generates_unique_file_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    storage = LocalImageStorage()

    first_key = await storage.save(
        content=b"first",
        extension="jpg",
    )

    second_key = await storage.save(
        content=b"second",
        extension="jpg",
    )

    assert first_key != second_key

    assert (storage.uploads_dir / first_key).exists()

    assert (storage.uploads_dir / second_key).exists()


@pytest.mark.anyio
async def test_delete_existing_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    storage = LocalImageStorage()

    storage_key = await storage.save(
        content=b"image-content",
        extension="webp",
    )

    file_path = storage.uploads_dir / storage_key

    assert file_path.exists()

    await storage.delete(storage_key)

    assert not file_path.exists()


@pytest.mark.anyio
async def test_delete_missing_image_does_not_raise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    storage = LocalImageStorage()

    await storage.delete("offerings/missing.png")

    assert not (storage.uploads_dir / "offerings/missing.png").exists()


def test_get_image_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    storage = LocalImageStorage()

    result = storage.get_url("offerings/image.png")

    assert result == "/uploads/offerings/image.png"
