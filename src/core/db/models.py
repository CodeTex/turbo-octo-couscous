from datetime import datetime

from sqlmodel import Field, SQLModel


class Factory(SQLModel, table=True):
    __tablename__ = "factories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    location: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
