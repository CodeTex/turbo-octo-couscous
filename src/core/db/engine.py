from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from api.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=settings.db_echo,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.exec_driver_sql("PRAGMA busy_timeout=5000")


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
