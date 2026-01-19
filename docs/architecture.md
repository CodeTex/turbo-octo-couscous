# Architecture Documentation

## Overview

This project is a **monolithic multi-package application** designed to explore Robyn's capabilities through a factory monitoring use case. It demonstrates async Python/Rust interop, time-series data handling, and proper SQLite usage in a multi-worker environment.

---

## Design Principles

### 1. Monolith Structure (Single Version)

All three packages (`api`, `worker`, `core`) live in `src/` and share a single version number from `pyproject.toml`. This approach:

- **Simplifies development**: One test suite, one CI pipeline, unified dependencies
- **Matches deployment reality**: API and worker deploy together, share the same database
- **Reduces overhead**: No version coordination between internal packages
- **Enables refactoring**: Easy to move code between packages

**Import hierarchy:**
```
api     → imports from → core
worker  → imports from → core
core    → standalone (no api/worker imports)
```

This keeps `core` as reusable business logic that both services consume.

---

## Package Responsibilities

### `src/api/` - HTTP API Service

**Purpose**: Robyn-based REST API for external clients

**Key modules:**
- `main.py` - Robyn app initialization, startup/shutdown hooks
- `config.py` - Pydantic Settings for environment-based configuration
- `deps.py` - Dependency injection (DB sessions, shared resources)
- `routers/` - Route handlers grouped by domain (machines, sensors, readings, etc.)
- `middleware/` - Request/response interceptors (logging, timing, error handling)

**API Endpoints:**

**Sensors:**
- `GET /api/sensors/` - List all sensors (optional `?machine_id=` filter)
- `GET /api/sensors/:id` - Get sensor by ID
- `POST /api/sensors/` - Create new sensor
- `DELETE /api/sensors/:id` - Delete sensor
- `GET /api/sensors/:id/stats` - Get statistics (min/max/avg/count)
- `GET /api/sensors/:id/latest` - Get latest reading
- `GET /api/sensors/:id/anomalies` - Detect anomalies using **Rust HTTP service** 
  - Query params: `limit` (default: 100), `threshold` (default: 2.0)
  - Calls `anomaly-detector` service on port 3001
- `GET /api/sensors/:id/alerts` - Check threshold violations using **Rust PyO3 module**
  - Query params: `limit` (default: 100)
  - Calls `threshold_checker` native extension

**Responsibilities:**
- HTTP request handling and validation
- Response serialization (using Robyn's Response class)
- Rust service orchestration (HTTP + PyO3)
- Authentication/authorization (future)
- Rate limiting (future)
- WebSocket endpoints (future)

**Does NOT contain:**
- Business logic (that's in `core/services/`)
- Database models (that's in `core/db/models.py`)
- Direct database access (uses services from `core/`)

---

### `src/worker/` - Background Job Runner

**Purpose**: Scheduled tasks and async job processing

**Key modules:**
- `main.py` - Worker process entry point
- `scheduler.py` - Cron-like task scheduling
- `tasks/` - Individual task implementations

**Responsibilities:**
- Periodic anomaly detection
- Alert rule evaluation
- Report generation
- Data retention/archival
- Email notifications (future)

**Shares with API:**
- Database connection pool (via `core/db/engine.py`)
- Business logic (via `core/services/`)
- Data models (via `core/db/models.py`)

**Deployment note**: Runs as a separate process but uses the same Docker image as the API (different CMD).

---

### `src/core/` - Shared Business Logic

**Purpose**: Domain models, database access, and business logic shared by api and worker

**Structure:**
```
core/
├── db/
│   ├── engine.py      # SQLAlchemy async engine + pool config
│   ├── models.py      # SQLModel ORM models (Factory, Machine, Sensor, etc.)
│   └── session.py     # Session factory, context managers
├── services/
│   ├── machine_svc.py    # Machine CRUD + business logic
│   ├── sensor_svc.py     # Sensor CRUD + configuration
│   ├── reading_svc.py    # Time-series ingestion + queries
│   └── analytics_svc.py  # Statistics, anomaly detection
└── schemas/
    ├── machine.py     # Pydantic request/response schemas
    ├── sensor.py      # Separate from ORM models for API contracts
    └── reading.py
```

**Key principle**: `core/` should have **no dependencies** on `api/` or `worker/`. It's the foundation both services build on.

---

## Database Architecture

### SQLite with WAL Mode

**Why SQLite?**
- Zero configuration, embedded database
- Perfect for learning connection pooling strategies
- Demonstrates multi-process concurrency handling
- Easy to containerize (single file)

**Concurrency Strategy:**

```python
# core/db/engine.py
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

engine = create_async_engine(
    "sqlite+aiosqlite:///./data/factory.db",
    poolclass=StaticPool,  # One connection per process
    connect_args={"check_same_thread": False},
)

# Enable WAL mode on startup
async with engine.begin() as conn:
    await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    await conn.exec_driver_sql("PRAGMA busy_timeout=5000")
```

**StaticPool explained:**
- SQLite's single-writer model means only one write at a time
- StaticPool maintains **one connection per process** (not per request)
- Safe for async usage within a single worker
- Multiple Robyn workers each get their own connection via separate processes

**WAL (Write-Ahead Logging) benefits:**
- Readers don't block writers
- Writers don't block readers
- Better throughput for mixed read/write workloads
- Essential for multi-process scenarios (API + worker)

**Alternative for production**: If SQLite becomes a bottleneck, migration path is:
1. Switch to PostgreSQL (same SQLAlchemy code)
2. Use NullPool with proper connection pooling
3. Horizontal scaling becomes possible

---

## Data Model

### Entity-Relationship Design

```
Factory 1────N Machine 1────N Sensor 1────N Reading
                                  │
                                  │ 1
                                  │
                                  N
                             AlertRule 1────N Alert
```

### Schema Details

**factories**
- `id` (INTEGER PRIMARY KEY)
- `name` (VARCHAR, unique)
- `location` (VARCHAR)
- `created_at` (TIMESTAMP)

**machines**
- `id` (INTEGER PRIMARY KEY)
- `factory_id` (INTEGER FK → factories.id)
- `name` (VARCHAR)
- `type` (VARCHAR) - e.g., "CNC_MILL", "ROBOT_ARM"
- `status` (VARCHAR) - "OPERATIONAL", "MAINTENANCE", "OFFLINE"
- `created_at` (TIMESTAMP)

**sensors**
- `id` (INTEGER PRIMARY KEY)
- `machine_id` (INTEGER FK → machines.id)
- `name` (VARCHAR)
- `unit` (VARCHAR) - e.g., "celsius", "bar", "rpm"
- `min_threshold` (FLOAT, nullable)
- `max_threshold` (FLOAT, nullable)
- `created_at` (TIMESTAMP)

**readings** (time-series, large volume)
- `id` (INTEGER PRIMARY KEY)
- `sensor_id` (INTEGER FK → sensors.id, indexed)
- `value` (FLOAT)
- `timestamp` (TIMESTAMP, indexed)

**Indexes:**
```sql
CREATE INDEX idx_readings_sensor_time ON readings(sensor_id, timestamp DESC);
CREATE INDEX idx_readings_timestamp ON readings(timestamp DESC);
```

**alert_rules**
- `id` (INTEGER PRIMARY KEY)
- `sensor_id` (INTEGER FK → sensors.id)
- `condition` (VARCHAR) - "GREATER_THAN", "LESS_THAN", "OUT_OF_RANGE"
- `threshold` (FLOAT)
- `severity` (VARCHAR) - "INFO", "WARNING", "CRITICAL"
- `enabled` (BOOLEAN)
- `created_at` (TIMESTAMP)

**alerts** (triggered events)
- `id` (INTEGER PRIMARY KEY)
- `rule_id` (INTEGER FK → alert_rules.id)
- `reading_id` (INTEGER FK → readings.id)
- `triggered_at` (TIMESTAMP)
- `acknowledged` (BOOLEAN)
- `acknowledged_at` (TIMESTAMP, nullable)

---

## Request Flow

### Example 1: Threshold Alerts (PyO3 Integration)

```
1. Client → GET /api/sensors/14/alerts?limit=100

2. api/routers/sensors.py::get_sensor_alerts()
   - Validates sensor_id from path params
   - Validates limit from query params
   - Fetches sensor from database (check thresholds configured)

3. core/services/sensor_svc.get_sensor_readings()
   - Queries last 100 readings for sensor 14
   - Returns list of Reading objects

4. core/services/threshold.check_threshold_alerts()
   - Converts Reading objects to (id, value) tuples
   - Calls Rust: threshold_checker.check_thresholds()
   
5. Rust PyO3 module (in-process, microsecond latency)
   - Iterates readings, checks min/max thresholds
   - Calculates severity based on violation percentage
   - Returns Vec<Alert> (converted to Python list)

6. Python wrapper
   - Converts Rust Alert objects to dicts
   - Returns to route handler

7. Response → HTTP 200 (via Robyn Response class)
   {
     "sensor_id": 14,
     "sensor_name": "Pressure Sensor A1",
     "thresholds": {"min": 10.0, "max": 100.0},
     "checked_readings": 100,
     "alerts_found": 3,
     "alerts": [
       {"reading_id": 1234, "value": 105.2, "breach_type": "above_maximum", 
        "threshold_value": 100.0, "severity": "critical"},
       ...
     ]
   }
```

**Performance**: ~1-5ms total (PyO3 call is <1ms)

---

### Example 2: Anomaly Detection (HTTP Service Integration)

```
1. Client → GET /api/sensors/14/anomalies?limit=100&threshold=2.0

2. api/routers/sensors.py::get_sensor_anomalies()
   - Validates sensor_id, limit, threshold
   - Fetches sensor from database

3. core/services/sensor_svc.get_sensor_readings()
   - Queries last 100 readings for sensor 14
   - Returns list of Reading objects

4. core/services/anomaly_client.detect_anomalies()
   - Extracts values from Reading objects
   - HTTP POST to http://localhost:3001/detect
   - Sends: {"values": [23.1, 24.5, ...], "threshold": 2.0}

5. Rust HTTP service (separate process, millisecond latency)
   - Calculates mean and standard deviation
   - Computes Z-scores for each value
   - Identifies anomalies where |z-score| > threshold
   - Returns JSON response

6. Python HTTP client
   - Parses JSON response
   - Returns to route handler

7. Response → HTTP 200 (via Robyn Response class)
   {
     "sensor_id": 14,
     "sensor_name": "Temperature Sensor B2",
     "analyzed_readings": 100,
     "anomalies_found": 2,
     "statistics": {"mean": 23.5, "std_dev": 1.2},
     "anomalies": [
       {"index": 42, "value": 28.9, "z_score": 4.5},
       {"index": 67, "value": 18.1, "z_score": -4.5}
     ]
   }
```

**Performance**: ~5-15ms total (includes HTTP roundtrip to Rust service)

---

### Example 3: Bulk Reading Ingestion

```
1. Client → POST /api/readings/bulk
   Body: [{"sensor_id": 1, "value": 23.5, "timestamp": "..."}, ...]

2. api/routers/readings.py
   - Validates request with Pydantic schema
   - Calls core/services/reading_svc.bulk_insert()

3. core/services/reading_svc.py
   - Business logic: Check sensor existence
   - Batch validation
   - Calls core/db/models.py create methods

4. core/db/models.py (SQLModel)
   - ORM inserts via SQLAlchemy
   - Transaction batching (1000 at a time)

5. SQLite (WAL mode)
   - Writes to WAL file
   - Returns success

6. Response → HTTP 201 Created
   {"inserted": 5000, "duration_ms": 42}
```

**Key optimization**: Bulk inserts use `session.add_all()` with batching to avoid per-row overhead.

---

## Time-Series Query Patterns

### Challenge: Efficiently query millions of readings

**Query examples:**

```python
# Get last hour of readings for a sensor
SELECT * FROM readings
WHERE sensor_id = ? AND timestamp >= datetime('now', '-1 hour')
ORDER BY timestamp DESC;

# Rolling average (last 100 readings)
SELECT AVG(value) OVER (
    ORDER BY timestamp
    ROWS BETWEEN 99 PRECEDING AND CURRENT ROW
) as rolling_avg
FROM readings
WHERE sensor_id = ?
ORDER BY timestamp;

# Downsample to 1-minute buckets
SELECT
    datetime((strftime('%s', timestamp) / 60) * 60, 'unixepoch') as bucket,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(*) as count
FROM readings
WHERE sensor_id = ? AND timestamp >= ?
GROUP BY bucket
ORDER BY bucket;
```

**Performance strategy:**
1. **Phase 1**: Pure SQL with SQLAlchemy
2. **Phase 2**: Fetch raw data, process in Python (pandas-like)
3. **Phase 3**: Fetch raw data, process in Rust (PyO3 module)

Benchmark all three to demonstrate Rust's performance gains.

---

## Rust Integration Strategy

This project demonstrates **two production-ready patterns** for Python/Rust interoperability:

### 1. PyO3 Module (`threshold-checker`)

**Status**: ✅ Implemented and working

**Purpose**: Native Python extension module for CPU-intensive threshold checking

**Location**: `crates/threshold-checker/`

**Implementation:**
```rust
// crates/threshold-checker/src/lib.rs
#[pyfunction]
fn check_thresholds(
    readings: Vec<(i64, f64)>,
    min_threshold: Option<f64>,
    max_threshold: Option<f64>,
) -> PyResult<Vec<Alert>> {
    // Rust implementation with performance benefits
}

#[pymodule]
fn threshold_checker(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(check_thresholds, m)?)?;
    m.add_class::<Alert>()?;
    Ok(())
}
```

**Python Integration:**
```python
# src/core/services/threshold.py
import threshold_checker

def check_threshold_alerts(readings: list[Reading], sensor: Sensor) -> list[dict]:
    reading_tuples = [(r.id, r.value) for r in readings]
    rust_alerts = threshold_checker.check_thresholds(
        readings=reading_tuples,
        min_threshold=sensor.min_threshold,
        max_threshold=sensor.max_threshold
    )
    return [alert_to_dict(a) for a in rust_alerts]
```

**API Endpoint:**
```
GET /api/sensors/:id/alerts?limit=100
```

**Features:**
- Threshold violation detection (min/max)
- Severity calculation (critical/high/medium)
- Zero-copy data transfer from Python to Rust
- Compiled as native extension, no runtime overhead

**Why PyO3?**
- Direct in-process function calls (microsecond latency)
- No serialization overhead
- Shares memory space with Python process
- Perfect for hot-path computations

**Testing:**
```bash
cargo test -p threshold-checker  # 11 unit tests
```

---

### 2. HTTP Microservice (`anomaly-detector`)

**Status**: ✅ Implemented and working

**Purpose**: Standalone Rust HTTP service for anomaly detection

**Location**: `crates/anomaly-detector/`

**Implementation:**
```rust
// crates/anomaly-detector/src/main.rs
#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/detect", post(detect_anomalies_handler));
    
    axum::Server::bind(&"127.0.0.1:3001".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn detect_anomalies_handler(
    Json(payload): Json<DetectionRequest>,
) -> Json<DetectionResponse> {
    // Z-score based anomaly detection
}
```

**Python Integration:**
```python
# src/core/services/anomaly_client.py
import httpx

async def detect_anomalies(readings: list[Reading], threshold: float = 2.0) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3001/detect",
            json={
                "values": [r.value for r in readings],
                "threshold": threshold,
            }
        )
        return response.json()
```

**API Endpoint:**
```
GET /api/sensors/:id/anomalies?limit=100&threshold=2.0
```

**Features:**
- Z-score based statistical anomaly detection
- Calculates mean and standard deviation
- Returns anomaly indices and values
- Independent service lifecycle

**Why HTTP Service?**
- Can be deployed/scaled independently
- Language-agnostic communication (JSON over HTTP)
- Easy to replace or version independently
- Natural service boundary
- Can use different resource limits (CPU, memory)

**Running:**
```bash
just run-anomaly  # Starts on port 3001
```

**Testing:**
```bash
cargo test -p anomaly-detector  # 7 unit tests
```

---

### Architecture Comparison

| Feature | PyO3 Module | HTTP Service |
|---------|-------------|--------------|
| **Latency** | Microseconds | Milliseconds |
| **Deployment** | Bundled with Python | Independent service |
| **Scaling** | Scales with Python process | Horizontal scaling |
| **Language** | Must be Rust | Any language |
| **State sharing** | Direct memory access | HTTP/JSON only |
| **Best for** | Hot-path computations | Background processing |

**When to use each:**
- **PyO3**: Tight loops, data processing, called frequently (>100 req/s)
- **HTTP**: Async workflows, microservices, independent scaling needs

---

### Implementation Status

**Completed:**
- ✅ Cargo workspace with 2 crates (`anomaly-detector`, `threshold-checker`)
- ✅ PyO3 module builds and installs via maturin
- ✅ HTTP service with Axum framework
- ✅ Python wrappers in `core/services/`
- ✅ API endpoints exposing both Rust integrations
- ✅ 18 Rust unit tests (all passing)

**API Endpoints using Rust:**
```
GET /api/sensors/:id/anomalies   → Rust HTTP service (port 3001)
GET /api/sensors/:id/alerts       → Rust PyO3 module (in-process)
```

---

---

## Build System & Dependency Management

### uv + maturin Integration

This project uses **uv** for Python dependency management and **maturin** as the build backend for the Rust PyO3 extension.

**Configuration** (`pyproject.toml`):
```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[tool.maturin]
bindings = "pyo3"
manifest-path = "crates/threshold-checker/Cargo.toml"
python-source = "src"
python-packages = ["api", "core"]

[tool.uv]
cache-keys = [
    {file = "pyproject.toml"},
    {file = "crates/threshold-checker/Cargo.toml"},
    {file = "crates/threshold-checker/src/**/*.rs"}
]
```

**How it works:**

1. **uv sync** triggers maturin to build the Rust extension
2. **cache-keys** tell uv when to rebuild (when Rust files change)
3. Maturin compiles `threshold-checker` and installs it as a Python module
4. Python packages `api` and `core` are included from `src/`
5. Everything installed into `.venv` as an editable package

**Benefits:**
- Single `uv sync` command installs everything (Python + Rust)
- Automatic rebuilds when Rust code changes
- No manual `maturin develop` needed
- Consistent with modern Python tooling

**Development workflow:**
```bash
# Install dependencies and build Rust extension
just install  # = uv sync --all-groups

# Run the API (uses uv run)
just run

# Rebuild after Rust changes (uv detects via cache-keys)
uv sync --reinstall-package turbo-octo-couscous
```

**For the HTTP service:**
The `anomaly-detector` service is a standalone Rust binary, managed separately:
```bash
cargo build -p anomaly-detector  # Build
just run-anomaly                 # Run on port 3001
```

---

## Testing Strategy

### Test Structure

```
tests/
├── test_api/
│   ├── test_health.py           # Endpoint tests
│   ├── test_machines.py
│   └── test_readings.py
├── test_core/
│   ├── test_services/
│   │   ├── test_machine_svc.py  # Business logic tests
│   │   └── test_reading_svc.py
│   └── test_db/
│       └── test_models.py       # ORM tests
└── benchmarks/
    ├── test_bulk_insert.py      # Performance benchmarks
    └── test_analytics.py        # Python vs Rust comparison
```

### Test Database Strategy

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@pytest.fixture
async def test_db():
    """In-memory SQLite for each test"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()

@pytest.fixture
async def test_session(test_db):
    """Session for database tests"""
    SessionLocal = async_sessionmaker(test_db)
    async with SessionLocal() as session:
        yield session
```

### Testing Approach

1. **Unit tests**: Test services in isolation with mocked DB
2. **Integration tests**: Test API endpoints with test database
3. **Benchmarks**: Compare performance (Python vs Rust, different query strategies)
4. **Load tests**: Use Rust CLI to stress test the API

---

## Deployment Architecture

### Development (Local)

```bash
# Terminal 1: API server
just dev  # Runs on http://localhost:8080

# Terminal 2: Background worker
just worker

# Terminal 3: Run migrations, seed data
just migrate
just seed
```

### Docker (Future - Phase 8)

**Single multi-stage Dockerfile:**
```dockerfile
# Stage 1: Builder (with Rust for PyO3)
FROM python:3.13-slim as builder
# ... install Rust, build factory_compute, install deps

# Stage 2: Runtime
FROM python:3.13-slim
COPY --from=builder /app/.venv /app/.venv
COPY src/ /app/src/
CMD ["python", "-m", "api.main"]
```

**docker-compose.yml:**
```yaml
services:
  api:
    build: .
    command: python -m api.main
    ports: ["8080:8080"]
    volumes: ["./data:/app/data"]
    
  worker:
    build: .
    command: python -m worker.main
    volumes: ["./data:/app/data"]
```

**Key points:**
- Same image, different commands
- Shared volume for SQLite database
- WAL mode enables concurrent access
- For production at scale → switch to PostgreSQL

---

## Configuration Management

### Environment-Based Config

```python
# src/api/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/factory.db"
    db_echo: bool = False
    
    # API
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 2
    
    # Features
    enable_analytics: bool = True
    use_rust_compute: bool = False  # Toggle for benchmarking
    
    class Config:
        env_file = ".env"
        env_prefix = "FACTORY_"

settings = Settings()
```

**Usage:**
```bash
# .env file
FACTORY_DATABASE_URL=sqlite+aiosqlite:///./data/factory.db
FACTORY_PORT=8080
FACTORY_WORKERS=4
```

---

## Observability (Future - Phase 8)

### Structured Logging

```python
# src/api/middleware/logging.py
import structlog

logger = structlog.get_logger()

async def log_request(request, call_next):
    logger.info("request_start", 
                method=request.method, 
                path=request.url.path)
    
    response = await call_next(request)
    
    logger.info("request_end", 
                status=response.status_code,
                duration_ms=...)
    
    return response
```

### Metrics Endpoint

```python
# Prometheus-compatible metrics
GET /metrics

factory_api_requests_total{method="POST",path="/api/readings/bulk"} 1234
factory_api_request_duration_seconds{path="/api/readings"} 0.042
factory_db_queries_total{operation="insert"} 5678
```

---

## Development Workflow

### Adding a New Feature (Example: Machine Status Updates)

1. **Define schema** (`core/schemas/machine.py`):
   ```python
   class MachineStatusUpdate(BaseModel):
       status: str = Field(..., pattern="^(OPERATIONAL|MAINTENANCE|OFFLINE)$")
   ```

2. **Add service method** (`core/services/machine_svc.py`):
   ```python
   async def update_status(machine_id: int, status: str) -> Machine:
       # Business logic here
       pass
   ```

3. **Add API route** (`api/routers/machines.py`):
   ```python
   @router.patch("/{machine_id}/status")
   async def update_machine_status(
       machine_id: int,
       update: MachineStatusUpdate
   ):
       machine = await machine_svc.update_status(machine_id, update.status)
       return machine
   ```

4. **Write tests** (`tests/test_api/test_machines.py`):
   ```python
   async def test_update_status(client, test_machine):
       response = await client.patch(
           f"/api/machines/{test_machine.id}/status",
           json={"status": "MAINTENANCE"}
       )
       assert response.status_code == 200
   ```

5. **Run tests**: `just test`
6. **Try it**: `just dev` → curl or httpx test

---

## Migration Path to Production

When outgrowing SQLite or single-machine deployment:

1. **PostgreSQL**: Change `DATABASE_URL`, same SQLModel code works
2. **Horizontal scaling**: Multiple API workers behind load balancer
3. **Redis**: Add for session storage, caching, pub/sub
4. **Message queue**: Replace worker scheduler with Celery/RQ
5. **Monitoring**: Add Sentry, DataDog, or Prometheus + Grafana

The monolith structure makes this transition smooth - no package coordination needed.

---

## Key Takeaways

1. **Monolith first**: Simplicity enables faster learning and iteration
2. **src/ layout**: Clean imports, standard Python structure
3. **Single version**: One source of truth, no version coordination overhead
4. **SQLite + WAL**: Production-ready for single-machine deployments
5. **Incremental Rust**: Add Rust after Python baseline for benchmarking
6. **Shared core**: Business logic reused by API and worker
7. **Docker-ready**: Same image, different entrypoints

This architecture balances learning goals (explore Robyn, Rust interop) with real-world patterns (monolith, time-series data, background workers).
