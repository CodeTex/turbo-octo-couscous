from datetime import datetime

from pydantic import BaseModel


class ReadingBase(BaseModel):
    value: float


class ReadingCreate(ReadingBase):
    sensor_id: int
    timestamp: datetime | None = None


class ReadingResponse(ReadingBase):
    id: int
    sensor_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
