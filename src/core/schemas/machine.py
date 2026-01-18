from datetime import datetime

from pydantic import BaseModel


class MachineBase(BaseModel):
    name: str
    type: str
    status: str = "OPERATIONAL"


class MachineCreate(MachineBase):
    factory_id: int


class MachineResponse(MachineBase):
    id: int
    factory_id: int
    created_at: datetime

    class Config:
        from_attributes = True
