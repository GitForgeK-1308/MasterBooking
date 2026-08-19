import uuid

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50,
    )
    slug: str = Field(
        min_length=2,
        max_length=50,
    )


class TagUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    is_active: bool | None = None


class TagResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    name: str
    slug: str
    is_active: bool