use axum::{
    Json, Router,
    routing::{get, post},
};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct Reading {
    id: i64,
    value: f64,
    timestamp: String,
}

#[derive(Deserialize)]
struct AnalyzeRequest {
    readings: Vec<Reading>,
    #[serde(default = "default_threshold")]
    threshold: f64,
}

fn default_threshold() -> f64 {
    2.0
}

#[derive(Serialize)]
struct Anomaly {
    id: i64,
    value: f64,
    timestamp: String,
    z_score: f64,
    severity: String,
}

#[derive(Serialize)]
struct AnalyzeResponse {
    anomalies: Vec<Anomaly>,
    total_readings: usize,
    mean: f64,
    std_dev: f64,
}

async fn health_check() -> &'static str {
    "Anomaly Detector Service is running"
}

fn calculate_mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    values.iter().sum::<f64>() / values.len() as f64
}

fn calculate_std_dev(values: &[f64], mean: f64) -> f64 {
    if values.len() <= 1 {
        return 0.0;
    }
    let variance =
        values.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / (values.len() - 1) as f64;
    variance.sqrt()
}

async fn analyze(Json(payload): Json<AnalyzeRequest>) -> Json<AnalyzeResponse> {
    let values: Vec<f64> = payload.readings.iter().map(|r| r.value).collect();
    let mean = calculate_mean(&values);
    let std_dev = calculate_std_dev(&values, mean);

    let mut anomalies = Vec::new();

    for reading in payload.readings {
        if std_dev > 0.0 {
            let z_score = (reading.value - mean) / std_dev;
            let abs_z = z_score.abs();

            if abs_z > payload.threshold {
                let severity = if abs_z > 3.0 {
                    "critical"
                } else if abs_z > 2.5 {
                    "high"
                } else {
                    "medium"
                };

                anomalies.push(Anomaly {
                    id: reading.id,
                    value: reading.value,
                    timestamp: reading.timestamp,
                    z_score,
                    severity: severity.to_string(),
                });
            }
        }
    }

    Json(AnalyzeResponse {
        anomalies,
        total_readings: values.len(),
        mean,
        std_dev,
    })
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/analyze", post(analyze));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3001").await.unwrap();

    println!("Anomaly detector listening on http://0.0.0.0:3001");
    axum::serve(listener, app).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_mean() {
        let values = vec![10.0, 20.0, 30.0, 40.0, 50.0];
        let mean = calculate_mean(&values);
        assert_eq!(mean, 30.0);
    }

    #[test]
    fn test_calculate_mean_empty() {
        let values = vec![];
        let mean = calculate_mean(&values);
        assert_eq!(mean, 0.0);
    }

    #[test]
    fn test_calculate_std_dev() {
        let values = vec![2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0];
        let mean = calculate_mean(&values);
        let std_dev = calculate_std_dev(&values, mean);
        assert!((std_dev - 2.138).abs() < 0.01);
    }

    #[test]
    fn test_calculate_std_dev_single_value() {
        let values = vec![42.0];
        let mean = calculate_mean(&values);
        let std_dev = calculate_std_dev(&values, mean);
        assert_eq!(std_dev, 0.0);
    }

    #[tokio::test]
    async fn test_analyze_no_anomalies() {
        let request = AnalyzeRequest {
            readings: vec![
                Reading {
                    id: 1,
                    value: 70.0,
                    timestamp: "2026-01-19T10:00:00".to_string(),
                },
                Reading {
                    id: 2,
                    value: 72.0,
                    timestamp: "2026-01-19T10:01:00".to_string(),
                },
                Reading {
                    id: 3,
                    value: 71.0,
                    timestamp: "2026-01-19T10:02:00".to_string(),
                },
            ],
            threshold: 2.0,
        };

        let Json(response) = analyze(Json(request)).await;

        assert_eq!(response.total_readings, 3);
        assert_eq!(response.anomalies.len(), 0);
        assert!((response.mean - 71.0).abs() < 0.01);
    }

    #[tokio::test]
    async fn test_analyze_with_anomalies() {
        // Create a dataset where one value is clearly an outlier
        let request = AnalyzeRequest {
            readings: vec![
                Reading {
                    id: 1,
                    value: 10.0,
                    timestamp: "2026-01-19T10:00:00".to_string(),
                },
                Reading {
                    id: 2,
                    value: 12.0,
                    timestamp: "2026-01-19T10:01:00".to_string(),
                },
                Reading {
                    id: 3,
                    value: 11.0,
                    timestamp: "2026-01-19T10:02:00".to_string(),
                },
                Reading {
                    id: 4,
                    value: 11.5,
                    timestamp: "2026-01-19T10:03:00".to_string(),
                },
                Reading {
                    id: 5,
                    value: 10.5,
                    timestamp: "2026-01-19T10:04:00".to_string(),
                },
                Reading {
                    id: 6,
                    value: 11.0,
                    timestamp: "2026-01-19T10:05:00".to_string(),
                },
                Reading {
                    id: 7,
                    value: 10.8,
                    timestamp: "2026-01-19T10:06:00".to_string(),
                },
                Reading {
                    id: 8,
                    value: 11.2,
                    timestamp: "2026-01-19T10:07:00".to_string(),
                },
                Reading {
                    id: 9,
                    value: 200.0,
                    timestamp: "2026-01-19T10:08:00".to_string(),
                }, // Extreme outlier
            ],
            threshold: 2.0,
        };

        let Json(response) = analyze(Json(request)).await;

        assert_eq!(response.total_readings, 9);
        assert!(
            response.anomalies.len() > 0,
            "Should detect at least one anomaly"
        );

        // The anomaly should be reading id 9 with value 200.0
        let anomaly = response.anomalies.iter().find(|a| a.id == 9);
        assert!(anomaly.is_some(), "Reading 9 should be detected as anomaly");
        assert_eq!(anomaly.unwrap().value, 200.0);
    }

    #[tokio::test]
    async fn test_analyze_severity_critical() {
        // Create a dataset with many consistent values and one extreme outlier
        let mut readings = vec![];
        for i in 1..=20 {
            readings.push(Reading {
                id: i,
                value: 50.0,
                timestamp: format!("2026-01-19T10:{:02}:00", i),
            });
        }
        // Add extreme outlier
        readings.push(Reading {
            id: 21,
            value: 500.0,
            timestamp: "2026-01-19T10:21:00".to_string(),
        });

        let request = AnalyzeRequest {
            readings,
            threshold: 2.0,
        };

        let Json(response) = analyze(Json(request)).await;

        assert!(response.anomalies.len() > 0);

        // The extreme outlier should be marked as critical
        let critical_anomaly = response.anomalies.iter().find(|a| a.id == 21);
        assert!(critical_anomaly.is_some());
        assert_eq!(critical_anomaly.unwrap().severity, "critical");
    }
}
