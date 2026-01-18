from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Sensor, Reading
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


async def get_sensor_stats(session: AsyncSession, sensor_id: int) -> dict | None:
    sensor = await get_sensor_by_id(session, sensor_id)
    if not sensor:
        return None

    result = await session.execute(
        select(
            func.min(Reading.value).label("min"),
            func.max(Reading.value).label("max"),
            func.avg(Reading.value).label("avg"),
            func.count(Reading.id).label("count"),
        ).where(Reading.sensor_id == sensor_id)
    )
    row = result.first()

    return {
        "sensor_id": sensor_id,
        "min": row.min,
        "max": row.max,
        "avg": round(row.avg, 2) if row.avg else None,
        "count": row.count,
    }


async def get_sensor_latest_reading(session: AsyncSession, sensor_id: int) -> Reading | None:
    sensor = await get_sensor_by_id(session, sensor_id)
    if not sensor:
        return None

    result = await session.execute(
        select(Reading)
        .where(Reading.sensor_id == sensor_id)
        .order_by(Reading.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
