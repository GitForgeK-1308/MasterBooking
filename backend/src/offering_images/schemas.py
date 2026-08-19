import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OfferingImageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    offering_id: uuid.UUID
    image_url: str
    is_primary: bool
    sort_order: int
    created_at: datetime