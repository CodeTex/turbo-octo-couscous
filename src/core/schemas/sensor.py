from datetime import datetime

from pydantic import BaseModel


class SensorBase(BaseModel):
    name: str
    unit: str
    min_threshold: float | None = None
    max_threshold: float | None = None


class SensorCreate(SensorBase):
    machine_id: int


class SensorResponse(SensorBase):
    id: int
    machine_id: int
    created_at: datetime

    class Config:
        from_attributes = True
