from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship


class Factory(SQLModel, table=True):
    __tablename__ = "factories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    location: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    machines: list["Machine"] = Relationship(back_populates="factory")


class Machine(SQLModel, table=True):
    __tablename__ = "machines"

    id: int | None = Field(default=None, primary_key=True)
    factory_id: int = Field(foreign_key="factories.id", index=True)
    name: str
    type: str
    status: str = Field(default="OPERATIONAL")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    factory: Factory = Relationship(back_populates="machines")
    sensors: list["Sensor"] = Relationship(back_populates="machine")


class Sensor(SQLModel, table=True):
    __tablename__ = "sensors"

    id: int | None = Field(default=None, primary_key=True)
    machine_id: int = Field(foreign_key="machines.id", index=True)
    name: str
    unit: str
    min_threshold: float | None = None
    max_threshold: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    machine: Machine = Relationship(back_populates="sensors")
    readings: list["Reading"] = Relationship(back_populates="sensor")


class Reading(SQLModel, table=True):
    __tablename__ = "readings"

    id: int | None = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensors.id", index=True)
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    sensor: Sensor = Relationship(back_populates="readings")
