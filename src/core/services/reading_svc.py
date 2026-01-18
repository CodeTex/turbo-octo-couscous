from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Reading
from core.schemas.reading import ReadingCreate


async def list_readings(session: AsyncSession, sensor_id: int | None = None) -> list[Reading]:
    query = select(Reading).order_by(Reading.timestamp.desc())
    if sensor_id:
        query = query.where(Reading.sensor_id == sensor_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_reading_by_id(session: AsyncSession, reading_id: int) -> Reading | None:
    result = await session.execute(select(Reading).where(Reading.id == reading_id))
    return result.scalar_one_or_none()


async def create_reading(session: AsyncSession, reading_data: ReadingCreate) -> Reading:
    reading = Reading(**reading_data.model_dump())
    session.add(reading)
    await session.commit()
    await session.refresh(reading)
    return reading


async def delete_reading(session: AsyncSession, reading_id: int) -> bool:
    reading = await get_reading_by_id(session, reading_id)
    if not reading:
        return False
    await session.delete(reading)
    await session.commit()
    return True
