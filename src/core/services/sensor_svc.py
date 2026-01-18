from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Sensor
from core.schemas.sensor import SensorCreate


async def list_sensors(session: AsyncSession, machine_id: int | None = None) -> list[Sensor]:
    query = select(Sensor)
    if machine_id:
        query = query.where(Sensor.machine_id == machine_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_sensor_by_id(session: AsyncSession, sensor_id: int) -> Sensor | None:
    result = await session.execute(select(Sensor).where(Sensor.id == sensor_id))
    return result.scalar_one_or_none()


async def create_sensor(session: AsyncSession, sensor_data: SensorCreate) -> Sensor:
    sensor = Sensor(**sensor_data.model_dump())
    session.add(sensor)
    await session.commit()
    await session.refresh(sensor)
    return sensor


async def delete_sensor(session: AsyncSession, sensor_id: int) -> bool:
    sensor = await get_sensor_by_id(session, sensor_id)
    if not sensor:
        return False
    await session.delete(sensor)
    await session.commit()
    return True
