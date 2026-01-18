from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Factory
from core.schemas.factory import FactoryCreate


async def list_factories(session: AsyncSession) -> list[Factory]:
    result = await session.execute(select(Factory))
    return list(result.scalars().all())


async def get_factory_by_id(session: AsyncSession, factory_id: int) -> Factory | None:
    result = await session.execute(select(Factory).where(Factory.id == factory_id))
    return result.scalar_one_or_none()


async def create_factory(session: AsyncSession, factory_data: FactoryCreate) -> Factory:
    factory = Factory(**factory_data.model_dump())
    session.add(factory)
    await session.commit()
    await session.refresh(factory)
    return factory


async def delete_factory(session: AsyncSession, factory_id: int) -> bool:
    factory = await get_factory_by_id(session, factory_id)
    if not factory:
        return False
    await session.delete(factory)
    await session.commit()
    return True
