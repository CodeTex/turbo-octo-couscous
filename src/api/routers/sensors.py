from robyn import SubRouter, Response
import httpx
import json

from core.schemas.sensor import SensorCreate, SensorResponse
from core.schemas.reading import ReadingResponse
from core.services import sensor_svc
from core.services import anomaly_client
from core.services import threshold
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


@sensors_router.get("/:sensor_id/stats")
async def get_sensor_stats(request):
    sensor_id = int(request.path_params["sensor_id"])

    async with AsyncSessionLocal() as session:
        stats = await sensor_svc.get_sensor_stats(session, sensor_id)
        if not stats:
            return {"error": "Sensor not found"}
        return stats


@sensors_router.get("/:sensor_id/latest")
async def get_sensor_latest(request):
    sensor_id = int(request.path_params["sensor_id"])

    async with AsyncSessionLocal() as session:
        reading = await sensor_svc.get_sensor_latest_reading(session, sensor_id)
        if not reading:
            return {"error": "Sensor not found or no readings available"}
        return ReadingResponse.model_validate(reading).model_dump()


@sensors_router.get("/:sensor_id/anomalies")
async def get_sensor_anomalies(request):
    """
    Detect anomalies in sensor readings using Rust HTTP service.

    Query params:
    - limit: Number of recent readings to analyze (default: 100)
    - threshold: Z-score threshold for anomaly detection (default: 2.0)
    """
    sensor_id = int(request.path_params["sensor_id"])
    limit = int(request.query_params.get("limit", "100"))
    threshold_val = float(request.query_params.get("threshold", "2.0"))

    async with AsyncSessionLocal() as session:
        # Check if sensor exists
        sensor = await sensor_svc.get_sensor_by_id(session, sensor_id)
        if not sensor:
            return Response(
                status_code=404,
                headers={"Content-Type": "application/json"},
                description=json.dumps({"error": "Sensor not found"}),
            )

        # Get readings for analysis
        readings = await sensor_svc.get_sensor_readings(session, sensor_id, limit)
        if not readings:
            return Response(
                status_code=404,
                headers={"Content-Type": "application/json"},
                description=json.dumps({"error": "No readings available for analysis"}),
            )

        # Call Rust anomaly detection service
        try:
            result = await anomaly_client.detect_anomalies(readings, threshold_val)
            return Response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                description=json.dumps(
                    {
                        "sensor_id": sensor_id,
                        "sensor_name": sensor.name,
                        "analyzed_readings": result["total_readings"],
                        "anomalies_found": len(result["anomalies"]),
                        "statistics": {"mean": result["mean"], "std_dev": result["std_dev"]},
                        "anomalies": result["anomalies"],
                    }
                ),
            )
        except httpx.HTTPError as e:
            return Response(
                status_code=503,
                headers={"Content-Type": "application/json"},
                description=json.dumps(
                    {
                        "error": "Anomaly detection service unavailable",
                        "details": str(e),
                        "hint": "Make sure to run 'just rust-anomaly' to start the service",
                    }
                ),
            )


@sensors_router.get("/:sensor_id/alerts")
async def get_sensor_alerts(request):
    """
    Check sensor readings against thresholds using Rust PyO3 module.

    Query params:
    - limit: Number of recent readings to check (default: 100)
    """
    sensor_id = int(request.path_params["sensor_id"])
    limit = int(request.query_params.get("limit", "100"))

    async with AsyncSessionLocal() as session:
        # Check if sensor exists
        sensor = await sensor_svc.get_sensor_by_id(session, sensor_id)
        if not sensor:
            return Response(
                status_code=404,
                headers={"Content-Type": "application/json"},
                description=json.dumps({"error": "Sensor not found"}),
            )

        # Check if thresholds are configured
        if sensor.min_threshold is None and sensor.max_threshold is None:
            return Response(
                status_code=400,
                headers={"Content-Type": "application/json"},
                description=json.dumps(
                    {
                        "error": "No thresholds configured for this sensor",
                        "hint": "Set min_threshold or max_threshold on the sensor",
                    }
                ),
            )

        # Get readings for checking
        readings = await sensor_svc.get_sensor_readings(session, sensor_id, limit)
        if not readings:
            return Response(
                status_code=404,
                headers={"Content-Type": "application/json"},
                description=json.dumps({"error": "No readings available to check"}),
            )

        # Call Rust threshold checker
        try:
            alerts = threshold.check_threshold_alerts(readings, sensor)
            return Response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                description=json.dumps(
                    {
                        "sensor_id": sensor_id,
                        "sensor_name": sensor.name,
                        "thresholds": {"min": sensor.min_threshold, "max": sensor.max_threshold},
                        "checked_readings": len(readings),
                        "alerts_found": len(alerts),
                        "alerts": alerts,
                    }
                ),
            )
        except ImportError as e:
            return Response(
                status_code=503,
                headers={"Content-Type": "application/json"},
                description=json.dumps(
                    {
                        "error": "Threshold checker module not available",
                        "details": str(e),
                        "hint": "Run 'just rust-threshold' to build and install the module",
                    }
                ),
            )
