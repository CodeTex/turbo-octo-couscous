"""Wrapper for Rust threshold-checker PyO3 module."""

from typing import Any

from core.db.models import Reading, Sensor


try:
    import threshold_checker

    THRESHOLD_CHECKER_AVAILABLE = True
except ImportError:
    THRESHOLD_CHECKER_AVAILABLE = False


class Alert:
    """Python representation of Rust Alert object."""

    def __init__(
        self, reading_id: int, value: float, breach_type: str, threshold_value: float, severity: str
    ):
        self.reading_id = reading_id
        self.value = value
        self.breach_type = breach_type
        self.threshold_value = threshold_value
        self.severity = severity

    def to_dict(self) -> dict:
        return {
            "reading_id": self.reading_id,
            "value": self.value,
            "breach_type": self.breach_type,
            "threshold_value": self.threshold_value,
            "severity": self.severity,
        }


def check_threshold_alerts(readings: list[Reading], sensor: Sensor) -> list[dict[str, Any]]:
    """
    Check readings against sensor thresholds using the Rust threshold-checker module.

    Args:
        readings: List of Reading objects to check
        sensor: Sensor object containing min/max thresholds

    Returns:
        List of alert dictionaries containing:
        - reading_id: ID of the reading that breached
        - value: The value that breached
        - breach_type: "below_minimum" or "above_maximum"
        - threshold_value: The threshold that was breached
        - severity: "critical", "high", or "medium"

    Raises:
        ImportError: If threshold_checker module is not available
    """
    if not THRESHOLD_CHECKER_AVAILABLE:
        raise ImportError(
            "threshold_checker module not available. "
            "Run 'just rust-threshold' to build and install it."
        )

    if not readings:
        return []

    # Use sensor's thresholds or pass None to Rust
    min_threshold = sensor.min_threshold if sensor.min_threshold is not None else None
    max_threshold = sensor.max_threshold if sensor.max_threshold is not None else None

    # If both thresholds are None, return empty list
    if min_threshold is None and max_threshold is None:
        return []

    # Convert readings to (id, value) tuples expected by Rust
    reading_tuples = [(r.id, r.value) for r in readings]

    # Call Rust function
    rust_alerts = threshold_checker.check_thresholds(
        readings=reading_tuples, min_threshold=min_threshold, max_threshold=max_threshold
    )

    # Convert Rust Alert objects to dictionaries
    alerts = []
    for alert in rust_alerts:
        alerts.append(
            {
                "reading_id": alert.reading_id,
                "value": alert.value,
                "breach_type": alert.breach_type,
                "threshold_value": alert.threshold_value,
                "severity": alert.severity,
            }
        )

    return alerts


def is_module_available() -> bool:
    """Check if the threshold_checker module is available."""
    return THRESHOLD_CHECKER_AVAILABLE
