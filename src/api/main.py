from robyn import Robyn

from api.config import settings
from api.routers.health import health_router

app = Robyn(__file__)
app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "name": "Factory Monitoring API",
        "version": "0.1.0",
        "environment": settings.env,
    }


@app.startup_handler
async def startup():
    print(f"Starting API on {settings.host}:{settings.port}")


@app.shutdown_handler
async def shutdown():
    print("Shutting down API")


if __name__ == "__main__":
    app.start(host=settings.host, port=settings.port)
