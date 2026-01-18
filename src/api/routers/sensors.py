from robyn import SubRouter

from core.schemas.sensor import SensorCreate, SensorResponse
from core.services import sensor_svc
from core.db.engine import AsyncSessionLocal

sensors_router = SubRouter(__name__, prefix="/api/sensors")


@sensors_router.get("/")
async def list_sensors(request):
    machine_id = request.query_params.get("machine_id", None)
    machine_id = int(machine_id) if machine_id else None

    async with AsyncSessionLocal() as session:
        sensors = await sensor_svc.list_sensors(session, machine_id)
        return [SensorResponse.model_validate(s).model_dump() for s in sensors]


@sensors_router.get("/:sensor_id")
async def get_sensor(request):
    sensor_id = int(request.path_params["sensor_id"])

    async with AsyncSessionLocal() as session:
        sensor = await sensor_svc.get_sensor_by_id(session, sensor_id)
        if not sensor:
            return {"error": "Sensor not found"}
        return SensorResponse.model_validate(sensor).model_dump()


@sensors_router.post("/")
async def create_sensor(request):
    body = request.body
    sensor_data = SensorCreate(**body)

    async with AsyncSessionLocal() as session:
        sensor = await sensor_svc.create_sensor(session, sensor_data)
        return SensorResponse.model_validate(sensor).model_dump()


@sensors_router.delete("/:sensor_id")
async def delete_sensor(request):
    sensor_id = int(request.path_params["sensor_id"])

    async with AsyncSessionLocal() as session:
        deleted = await sensor_svc.delete_sensor(session, sensor_id)
        if not deleted:
            return {"error": "Sensor not found"}
        return {"message": "Sensor deleted", "id": sensor_id}
