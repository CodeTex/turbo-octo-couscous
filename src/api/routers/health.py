from robyn import SubRouter

health_router = SubRouter(__name__, prefix="/health")


@health_router.get("/")
async def health_check():
    return {"status": "healthy", "service": "factory-monitoring-api"}


@health_router.get("/ready")
async def readiness_check():
    return {"status": "ready", "checks": {"api": "ok"}}
