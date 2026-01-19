default:
	@just --list

# Install all dependencies (Python + Rust)
install:
	uv sync --all-groups
	.venv/bin/maturin develop -m crates/threshold-checker/Cargo.toml

# Build everything (Python + Rust)
build:
	cargo build --workspace
	.venv/bin/maturin develop -m crates/threshold-checker/Cargo.toml

# Build everything in release mode
build-release:
	cargo build --workspace --release
	.venv/bin/maturin develop -m crates/threshold-checker/Cargo.toml --release

# Run API server (requires: just install, just migrate, just seed)
run:
	uv run python -m api.main

# Run anomaly-detector HTTP service on port 3001
run-anomaly:
	cargo run -p anomaly-detector

# Stop all running services
stop:
	@pkill -f "anomaly-detector" || echo "No anomaly-detector running"
	@pkill -f "api.main" || echo "No Python API running"

# Run database migrations
migrate:
	uv run python db/migrate.py

# Seed database with test data
seed:
	uv run python db/seeds/generate.py

# Run all tests (Rust + Python)
test:
	cargo test --workspace
	uv run pytest tests/

# Format code (Python + Rust)
fmt:
	cargo fmt
	uv run ruff format .

# Lint code (Python + Rust)
lint:
	cargo clippy -- -D warnings
	uv run ruff check .
	uv run ty check .

# Clean all build artifacts and caches
clean:
	cargo clean
	rm -rf .pytest_cache/ htmlcov/ .ruff_cache/ target/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Update all dependencies
update:
	cargo update
	uv sync --upgrade

