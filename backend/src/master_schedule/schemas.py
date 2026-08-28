import uuid
from datetime import time

from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)

from src.master_schedule.models import WeekDay


class MasterScheduleBase(BaseModel):
    day_of_week: WeekDay
    start_time: time | None = None
    end_time: time | None = None
    is_working: bool = True


class MasterScheduleCreate(MasterScheduleBase):
    @model_validator(mode="after")
    def validate_schedule(
        self,
    ) -> "MasterScheduleCreate":
        if self.is_working:
            if self.start_time is None or self.end_time is None:
                raise ValueError(
                    "Для рабочего дня необходимо указать время начала и окончания"
                )

            if self.start_time >= self.end_time:
                raise ValueError("Время начала должно быть раньше времени окончания")

        elif self.start_time is not None or self.end_time is not None:
            raise ValueError("Для выходного дня время указывать не нужно")

        return self


class MasterScheduleUpdate(BaseModel):
    day_of_week: WeekDay | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_working: bool | None = None


class MasterScheduleResponse(MasterScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    master_id: uuid.UUID
