from datetime import datetime

from pydantic import BaseModel


class FactoryBase(BaseModel):
    name: str
    location: str


class FactoryCreate(FactoryBase):
    pass


class FactoryResponse(FactoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
