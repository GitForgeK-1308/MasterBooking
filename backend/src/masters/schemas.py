import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class MasterBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(
        min_length=1,
        max_length=20,
    )
    last_name: str = Field(
        min_length=1,
        max_length=25,
    )
    description: str = Field(
        min_length=1,
    )
    experience: int = Field(
        default=0,
        ge=0,
    )
    education: str = Field(
        min_length=1,
    )


class MasterCreate(MasterBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    city_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None

    address: str | None = Field(
        default=None,
        max_length=255,
    )


class MasterUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=25,
    )
    description: str | None = Field(
        default=None,
        min_length=1,
    )
    experience: int | None = Field(
        default=None,
        ge=0,
    )
    education: str | None = Field(
        default=None,
        min_length=1,
    )

    city_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None

    address: str | None = Field(
        default=None,
        max_length=255,
    )


class MasterResponse(MasterBase):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )

    id: uuid.UUID
    is_active: bool

    city_id: uuid.UUID | None
    district_id: uuid.UUID | None

    city: str | None
    district: str | None
    address: str | None

    phone: str | None
    avatar_url: str | None


class MasterProfileCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    description: str = Field(
        min_length=10,
        max_length=2000,
    )
    experience: int = Field(
        ge=0,
    )
    education: str = Field(
        min_length=2,
        max_length=1000,
    )

    city_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None

    address: str | None = Field(
        default=None,
        max_length=255,
    )
