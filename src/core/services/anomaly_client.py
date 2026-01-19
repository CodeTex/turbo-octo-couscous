"""HTTP client for Rust anomaly-detector service."""

import httpx
from datetime import datetime

from core.db.models import Reading


ANOMALY_SERVICE_URL = "http://localhost:3001"


async def detect_anomalies(readings: list[Reading], threshold: float = 2.0) -> dict:
    """
    Detect anomalies in sensor readings using the Rust anomaly-detector service.

    Args:
        readings: List of Reading objects to analyze
        threshold: Z-score threshold for anomaly detection (default: 2.0)

    Returns:
        Dictionary containing:
        - anomalies: List of detected anomalies with z_score and severity
        - total_readings: Total number of readings analyzed
        - mean: Mean value of all readings
        - std_dev: Standard deviation of readings

    Raises:
        httpx.HTTPError: If the service is unavailable or returns an error
    """
    if not readings:
        return {"anomalies": [], "total_readings": 0, "mean": 0.0, "std_dev": 0.0}

    # Convert readings to the format expected by Rust service
    reading_data = [
        {"id": r.id, "value": r.value, "timestamp": r.timestamp.isoformat()} for r in readings
    ]

    payload = {"readings": reading_data, "threshold": threshold}

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{ANOMALY_SERVICE_URL}/analyze", json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()


async def is_service_healthy() -> bool:
    """Check if the anomaly-detector service is running and healthy."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ANOMALY_SERVICE_URL}/health", timeout=2.0)
            return response.status_code == 200
    except (httpx.HTTPError, httpx.ConnectError):
        return False
