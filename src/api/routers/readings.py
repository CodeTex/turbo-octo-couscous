from robyn import SubRouter

from core.schemas.reading import ReadingCreate, ReadingResponse
from core.services import reading_svc
from core.db.engine import AsyncSessionLocal

readings_router = SubRouter(__name__, prefix="/api/readings")


@readings_router.get("/")
async def list_readings(request):
    sensor_id = request.query_params.get("sensor_id", None)
    sensor_id = int(sensor_id) if sensor_id else None

    async with AsyncSessionLocal() as session:
        readings = await reading_svc.list_readings(session, sensor_id)
        return [ReadingResponse.model_validate(r).model_dump() for r in readings]


@readings_router.get("/:reading_id")
async def get_reading(request):
    reading_id = int(request.path_params["reading_id"])

    async with AsyncSessionLocal() as session:
        reading = await reading_svc.get_reading_by_id(session, reading_id)
        if not reading:
            return {"error": "Reading not found"}
        return ReadingResponse.model_validate(reading).model_dump()


@readings_router.post("/")
async def create_reading(request):
    body = request.body
    reading_data = ReadingCreate(**body)

    async with AsyncSessionLocal() as session:
        reading = await reading_svc.create_reading(session, reading_data)
        return ReadingResponse.model_validate(reading).model_dump()


@readings_router.delete("/:reading_id")
async def delete_reading(request):
    reading_id = int(request.path_params["reading_id"])

    async with AsyncSessionLocal() as session:
        deleted = await reading_svc.delete_reading(session, reading_id)
        if not deleted:
            return {"error": "Reading not found"}
        return {"message": "Reading deleted", "id": reading_id}
