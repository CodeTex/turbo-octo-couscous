default:
	@just --list

# Install dependencies
install:
	uv sync --all-groups

# Run API server
run:
	uv run python -m api.main

# Run tests
test:
	uv run pytest tests/

# Format code
fmt:
	uv run ruff format .

# Lint code
lint:
	uv run ruff check .
	uv run ty check .

# Clean caches
clean:
	rm -rf .pytest_cache/ htmlcov/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

