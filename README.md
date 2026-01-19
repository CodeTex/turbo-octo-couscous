# Factory Monitoring System - Python/Rust Interop Demo

A factory monitoring system demonstrating Python/Rust interoperability patterns with [Robyn](https://robyn.tech/), featuring both HTTP service integration and native Python extensions via PyO3.

## Overview

Industrial IoT monitoring system showcasing:
- **Two Rust Integration Patterns**:
  - HTTP microservice (anomaly-detector on port 3001)
  - Native Python extension (threshold-checker via PyO3)
- Factories with machines and sensor arrays
- Time-series data ingestion and analytics
- Async Python API with Rust-accelerated computation

## Tech Stack

- **Robyn** - Async Python web framework with Rust runtime
- **SQLite** + **SQLModel** - Embedded database with async ORM
- **Rust** + **axum** - HTTP microservice for anomaly detection
- **PyO3** + **maturin** - Rust native extensions for Python
- **uv** - Fast Python package manager
- **just** - Task runner

## Quick Start

```bash
# Install all dependencies (Python + Rust)
just install

# Setup database
just migrate
just seed

# Terminal 1: Run Python API server (port 8080)
just run

# Terminal 2: Run Rust anomaly service (port 3001)
just run-anomaly

# Test the integration
curl http://localhost:8080/api/sensors/1/anomalies
curl http://localhost:8080/api/sensors/1/alerts
```

## Architecture

The system demonstrates two Python/Rust integration approaches:

**1. HTTP Microservice** (`anomaly-detector`)
- Standalone Rust service using axum framework
- Z-score based anomaly detection algorithm
- Python calls via HTTP using httpx

**2. Native Extension** (`threshold-checker`)
- Rust library compiled to native Python module
- Direct function calls from Python (no HTTP overhead)
- Built with PyO3 and installed via maturin

## Project Structure

```
src/
├── api/
│   ├── main.py              # Robyn application entry
│   └── routers/             # API endpoints
│       ├── sensors.py       # Sensor CRUD + analytics endpoints
│       ├── machines.py      # Machine management
│       └── factories.py     # Factory management
├── core/
│   ├── db/                  # Database models and engine
│   ├── services/            # Business logic
│   │   ├── anomaly_client.py    # HTTP client for Rust service
│   │   └── threshold.py         # Wrapper for PyO3 module
│   └── schemas/             # Pydantic schemas

crates/                      # Rust workspace
├── anomaly-detector/        # HTTP microservice (axum)
│   └── src/main.rs          # Z-score anomaly detection + tests
└── threshold-checker/       # PyO3 native extension
    └── src/lib.rs           # Threshold violation checker + tests

db/
├── migrations/              # SQL migration scripts
└── seeds/                   # Test data generators
```

## API Endpoints

### Core CRUD
- `GET /api/factories` - List factories
- `GET /api/machines?factory_id=1` - List machines
- `GET /api/sensors?machine_id=1` - List sensors
- `GET /api/sensors/:id` - Get sensor details

### Analytics (Rust Integration)
- `GET /api/sensors/:id/anomalies` - Detect anomalies (calls Rust HTTP service)
- `GET /api/sensors/:id/alerts` - Check threshold violations (calls PyO3 module)
- `GET /api/sensors/:id/stats` - Basic statistics
- `GET /api/sensors/:id/latest` - Latest reading

## Data Model

```
Factory → Machine → Sensor → Reading (time-series)
```

Each sensor has configurable thresholds (`min_threshold`, `max_threshold`) used by the Rust threshold-checker module.

## Development Commands

### Common Tasks
```bash
just install       # Install Python + Rust dependencies
just build         # Build all Rust crates + PyO3 module
just test          # Run all tests (Rust + Python)
just fmt           # Format code (both languages)
just lint          # Lint code (both languages)
just clean         # Clean all build artifacts
```

### Database
```bash
just migrate       # Run database migrations
just seed          # Seed test data
```

### Running Services
```bash
just run           # Start Python API (port 8080)
just run-anomaly   # Start Rust anomaly service (port 3001)
```

### Development Workflow
```bash
# First time setup
just install && just migrate && just seed

# Start both services (in separate terminals)
just run-anomaly   # Terminal 1: Rust service
just run           # Terminal 2: Python API

# Test the integration
curl http://localhost:8080/api/sensors/1/anomalies?limit=50
curl http://localhost:8080/api/sensors/1/alerts?limit=50
```

## Rust Modules Details

### anomaly-detector (HTTP Service)
- **Language**: Rust
- **Framework**: axum + tokio
- **Port**: 3001
- **Algorithm**: Z-score based anomaly detection
- **Tests**: 7 unit tests (`cargo test -p anomaly-detector`)
- **Endpoints**:
  - `GET /health` - Health check
  - `POST /analyze` - Analyze readings for anomalies

### threshold-checker (PyO3 Module)
- **Language**: Rust
- **Framework**: PyO3
- **Build Tool**: maturin
- **Algorithm**: Min/max threshold violation detection with severity levels
- **Tests**: 11 unit tests (`cargo test -p threshold-checker`)
- **Python Usage**:
  ```python
  import threshold_checker
  alerts = threshold_checker.check_thresholds(
      readings=[(1, 75.0), (2, 95.0)],
      min_threshold=15.0,
      max_threshold=85.0
  )
  ```

## Testing

```bash
# Run all tests (Rust + Python)
just test

# Run only Rust tests
cargo test --workspace

# Run specific crate tests
cargo test -p anomaly-detector
cargo test -p threshold-checker
```

## Learning Goals

This project demonstrates:
- **HTTP Microservice Pattern**: Standalone Rust service called via HTTP
- **Native Extension Pattern**: Rust code compiled as Python module
- When to use each approach (loose coupling vs. performance)
- Robyn's async request handling
- SQLite with async SQLModel ORM
- PyO3 for Python/Rust interop
- Time-series data modeling

## Implementation Phases

Building incrementally from minimal to complete:

1. ✅ **Minimal API** - Robyn app with health endpoint
2. ✅ **Database** - SQLite + SQLModel with migrations
3. ✅ **CRUD APIs** - Factories, machines, sensors, readings
4. ✅ **Time-Series** - Readings ingestion and queries
5. ✅ **Analytics (Python)** - Statistics endpoints
6. ✅ **Rust HTTP Service** - Anomaly detection microservice
7. ✅ **Rust PyO3 Module** - Threshold checker native extension
8. 🚧 **Integration Tests** - End-to-end Python tests
9. 📋 **Background Worker** - Scheduled analytics tasks
10. 📋 **Production Deploy** - Docker + configuration

## License

MIT - This is a learning project demonstrating Python/Rust interoperability patterns.
