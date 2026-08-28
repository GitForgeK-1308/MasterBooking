import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class CityCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )


class CityUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    is_active: bool | None = None


class CityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_active: bool


class DistrictCreate(BaseModel):
    city_id: uuid.UUID
    name: str = Field(
        min_length=2,
        max_length=100,
    )


class DistrictUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    is_active: bool | None = None


class DistrictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    city_id: uuid.UUID
    name: str
    is_active: bool
