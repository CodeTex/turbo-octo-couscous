from robyn import Robyn

from api.config import settings
from api.routers.health import health_router
from api.routers.factories import factories_router
from api.routers.machines import machines_router
from api.routers.sensors import sensors_router
from api.routers.readings import readings_router
from core.db.engine import init_db

app = Robyn(__file__)
app.include_router(health_router)
app.include_router(factories_router)
app.include_router(machines_router)
app.include_router(sensors_router)
app.include_router(readings_router)


@app.get("/")
async def root():
    return {
        "name": "Factory Monitoring API",
        "version": "0.1.0",
        "environment": settings.env,
    }


@app.startup_handler
async def startup():
    await init_db()
    print(f"Starting API on {settings.host}:{settings.port}")


@app.shutdown_handler
async def shutdown():
    print("Shutting down API")


if __name__ == "__main__":
    app.start(host=settings.host, port=settings.port)
