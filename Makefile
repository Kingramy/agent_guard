VENV := .venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
UV := uv

.PHONY: help install up down ps test lint format run-api run-worker benchmark live-audit clean

help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies via uv"
	@echo "  up          - Start PostgreSQL and Redis containers"
	@echo "  down        - Stop containers"
	@echo "  ps          - Check container health"
	@echo "  test        - Run full test suite"
	@echo "  lint        - Run ruff linter"
	@echo "  format      - Format source files with ruff"
	@echo "  benchmark   - Run offline evaluation benchmark harness"
	@echo "  live-audit  - Run live target agent security audit"
	@echo "  run-api     - Launch FastAPI backend on port 8000"
	@echo "  run-worker  - Launch Celery background evaluation worker"
	@echo "  clean       - Remove build cache and artifacts"

install:
	$(UV) sync

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

test:
	$(PYTEST) -v tests/

lint:
	$(RUFF) check src/ tests/ benchmarks/

format:
	$(RUFF) format src/ tests/ benchmarks/

run-api:
	$(UV) run uvicorn agentguard.api.app:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	$(UV) run celery -A agentguard.workers.celery_app worker --loglevel=info

benchmark:
	$(UV) run python benchmarks/run_eval.py

live-audit:
	$(UV) run python benchmarks/run_live_audit.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
