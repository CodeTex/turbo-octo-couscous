# Factory Monitoring System - Robyn Playground

A factory monitoring system built with [Robyn](https://robyn.tech/) to explore async Python/Rust patterns, time-series data handling, and SQLite connection pooling.

## Overview

Industrial IoT monitoring playground featuring:
- Factories with machines and sensor arrays
- Time-series data ingestion and querying
- Rust-accelerated analytics (PyO3 module)
- Background workers for scheduled tasks
- Standalone Rust CLI for load testing

## Tech Stack

- **Robyn** - Async Python web framework with Rust runtime
- **SQLite** + **SQLModel** - Embedded database with async ORM
- **PyO3** - Python/Rust interop for compute-heavy operations
- **uv** - Fast Python package manager
- **just** - Task runner

## Quick Start

```bash
# Install dependencies
just install

# Run the API server
just run

# Run tests
just test
```

See [`docs/architecture.md`](docs/architecture.md) for detailed design docs.

## Structure

```
src/
├── api/          # Robyn HTTP API
├── worker/       # Background job runner
└── core/         # Shared logic (db, services, schemas)

crates/           # Rust packages (added in later phases)
├── factory_compute/  # PyO3 module for analytics
└── factory_cli/      # Standalone CLI tool

db/
├── migrations/   # SQL migration scripts
└── seeds/        # Test data generators

tests/
├── test_api/     # API integration tests
├── test_core/    # Unit tests
└── benchmarks/   # Performance tests
```

## Data Model

Factory → Machine → Sensor → Reading (time-series)
                      ↓
                  AlertRule → Alert

See [`docs/architecture.md`](docs/architecture.md) for full schema details.

## Implementation Phases

Building incrementally from minimal to complete:

1. **Minimal API** - Robyn app with health endpoint
2. **Database** - SQLite + SQLModel with connection pool
3. **CRUD APIs** - Factories, machines, sensors
4. **Time-Series** - Readings ingestion and queries
5. **Analytics (Python)** - Statistics and anomaly detection
6. **Rust PyO3** - Accelerate analytics with Rust module
7. **Worker** - Background jobs and alerts
8. **Rust CLI** - Load testing and operations tool

## Commands

```bash
just install   # Install dependencies
just run       # Start API server
just test      # Run tests
just fmt       # Format code
just lint      # Lint code
just clean     # Clean caches
```

## Learning Goals

- Robyn's async request handling and multi-worker model
- SQLite connection pooling with StaticPool + WAL mode
- PyO3 for Python/Rust interop and performance gains
- Time-series data modeling and query optimization

## License

MIT - This is a playground project for learning and experimentation.
