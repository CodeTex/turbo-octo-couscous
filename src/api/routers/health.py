from robyn import SubRouter
from sqlalchemy import text

from core.db.engine import AsyncSessionLocal

health_router = SubRouter(__name__, prefix="/health")


@health_router.get("/")
async def health_check():
    return {"status": "healthy", "service": "factory-monitoring-api"}


@health_router.get("/ready")
async def readiness_check():
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "ready" if db_status == "ok" else "not_ready",
        "checks": {"api": "ok", "database": db_status},
    }
