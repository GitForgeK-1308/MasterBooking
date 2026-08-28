import uuid
from pathlib import Path

from anyio import to_thread


class LocalAvatarStorage:
    def __init__(self) -> None:
        self.uploads_dir = Path("uploads")
        self.avatars_dir = self.uploads_dir / "avatars"

        self.avatars_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def save(
        self,
        content: bytes,
        extension: str,
    ) -> str:
        file_name = f"{uuid.uuid4()}.{extension}"
        file_path = self.avatars_dir / file_name

        await to_thread.run_sync(
            file_path.write_bytes,
            content,
        )

        return f"avatars/{file_name}"

    async def delete(
        self,
        storage_key: str,
    ) -> None:
        file_path = self.uploads_dir / storage_key

        if not file_path.exists():
            return

        await to_thread.run_sync(file_path.unlink)

    def get_url(
        self,
        storage_key: str,
    ) -> str:
        return f"/uploads/{storage_key}"
