use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pyclass]
#[derive(Clone)]
struct Alert {
    #[pyo3(get)]
    reading_id: i64,
    #[pyo3(get)]
    value: f64,
    #[pyo3(get)]
    breach_type: String,
    #[pyo3(get)]
    threshold_value: f64,
    #[pyo3(get)]
    severity: String,
}

#[pymethods]
impl Alert {
    fn to_dict(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("reading_id", self.reading_id)?;
        dict.set_item("value", self.value)?;
        dict.set_item("breach_type", &self.breach_type)?;
        dict.set_item("threshold_value", self.threshold_value)?;
        dict.set_item("severity", &self.severity)?;
        Ok(dict.into())
    }
}

#[pyfunction]
fn check_thresholds(
    readings: Vec<(i64, f64)>,
    min_threshold: Option<f64>,
    max_threshold: Option<f64>,
) -> Vec<Alert> {
    let mut alerts = Vec::new();

    for (reading_id, value) in readings {
        if let Some(min) = min_threshold {
            if value < min {
                let diff = min - value;
                let severity = if diff > min * 0.2 {
                    "critical"
                } else if diff > min * 0.1 {
                    "high"
                } else {
                    "medium"
                };

                alerts.push(Alert {
                    reading_id,
                    value,
                    breach_type: "below_minimum".to_string(),
                    threshold_value: min,
                    severity: severity.to_string(),
                });
            }
        }

        if let Some(max) = max_threshold {
            if value > max {
                let diff = value - max;
                let severity = if diff > max * 0.2 {
                    "critical"
                } else if diff > max * 0.1 {
                    "high"
                } else {
                    "medium"
                };

                alerts.push(Alert {
                    reading_id,
                    value,
                    breach_type: "above_maximum".to_string(),
                    threshold_value: max,
                    severity: severity.to_string(),
                });
            }
        }
    }

    alerts
}

#[pymodule]
fn threshold_checker(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(check_thresholds, m)?)?;
    m.add_class::<Alert>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_no_breaches() {
        let readings = vec![(1, 50.0), (2, 60.0), (3, 70.0)];
        let alerts = check_thresholds(readings, Some(40.0), Some(80.0));
        assert_eq!(alerts.len(), 0);
    }

    #[test]
    fn test_below_minimum() {
        let readings = vec![(1, 50.0), (2, 10.0), (3, 70.0)];
        let alerts = check_thresholds(readings, Some(40.0), Some(80.0));
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].reading_id, 2);
        assert_eq!(alerts[0].value, 10.0);
        assert_eq!(alerts[0].breach_type, "below_minimum");
        assert_eq!(alerts[0].threshold_value, 40.0);
    }

    #[test]
    fn test_above_maximum() {
        let readings = vec![(1, 50.0), (2, 90.0), (3, 70.0)];
        let alerts = check_thresholds(readings, Some(40.0), Some(80.0));
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].reading_id, 2);
        assert_eq!(alerts[0].value, 90.0);
        assert_eq!(alerts[0].breach_type, "above_maximum");
        assert_eq!(alerts[0].threshold_value, 80.0);
    }

    #[test]
    fn test_multiple_breaches() {
        let readings = vec![
            (1, 10.0), // Below min
            (2, 50.0), // OK
            (3, 95.0), // Above max
            (4, 5.0),  // Below min
        ];
        let alerts = check_thresholds(readings, Some(40.0), Some(80.0));
        assert_eq!(alerts.len(), 3);
    }

    #[test]
    fn test_severity_critical() {
        let readings = vec![(1, 0.0)]; // 50 below threshold of 50 = 100% difference
        let alerts = check_thresholds(readings, Some(50.0), None);
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].severity, "critical");
    }

    #[test]
    fn test_severity_high() {
        let readings = vec![(1, 35.0)]; // 15 below threshold of 50 = 30% difference
        let alerts = check_thresholds(readings, Some(50.0), None);
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].severity, "critical"); // 15/50 = 0.3 > 0.2
    }

    #[test]
    fn test_severity_medium() {
        let readings = vec![(1, 46.0)]; // 4 below threshold of 50 = 8% difference (< 10%)
        let alerts = check_thresholds(readings, Some(50.0), None);
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].severity, "medium"); // 4/50 = 0.08 < 0.1
    }

    #[test]
    fn test_no_thresholds() {
        let readings = vec![(1, 50.0), (2, 100.0)];
        let alerts = check_thresholds(readings, None, None);
        assert_eq!(alerts.len(), 0);
    }

    #[test]
    fn test_only_min_threshold() {
        let readings = vec![(1, 10.0), (2, 100.0)];
        let alerts = check_thresholds(readings, Some(40.0), None);
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].breach_type, "below_minimum");
    }

    #[test]
    fn test_only_max_threshold() {
        let readings = vec![(1, 10.0), (2, 100.0)];
        let alerts = check_thresholds(readings, None, Some(80.0));
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].breach_type, "above_maximum");
    }

    #[test]
    fn test_empty_readings() {
        let readings = vec![];
        let alerts = check_thresholds(readings, Some(40.0), Some(80.0));
        assert_eq!(alerts.len(), 0);
    }
}
