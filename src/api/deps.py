from sqlalchemy.ext.asyncio import AsyncSession

from core.db.engine import AsyncSessionLocal


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
