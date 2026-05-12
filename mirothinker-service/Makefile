.PHONY: help install dev test lint format build docker-clean run

# Default target
help:
	@echo "MiroThinker Service - Available Commands:"
	@echo ""
	@echo "  make install      Install production dependencies"
	@echo "  make dev          Install development dependencies"
	@echo "  make test         Run test suite"
	@echo "  make test-cov     Run tests with coverage report"
	@echo "  make lint         Run linter (ruff)"
	@echo "  make format       Auto-format code (ruff)"
	@echo "  make run          Start development server"
	@echo "  make docker       Build Docker image"
	@echo "  make docker-up    Start Docker containers"
	@echo "  make docker-down  Stop Docker containers"
	@echo "  make docker-clean Remove all Docker containers and images"
	@echo "  make clean        Remove generated files"

# Install dependencies
install:
	pip install -r backend/requirements.txt

dev:
	pip install -e ".[dev,monitoring]"

# Testing
test:
	pytest backend/tests -v

test-cov:
	pytest backend/tests --cov=backend/src --cov-report=term-missing --cov-report=html

# Linting and formatting
lint:
	ruff check backend/src backend/tests

format:
	ruff check --fix backend/src backend/tests
	ruff format backend/src backend/tests

# Development server
run:
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Docker
docker:
	docker build -t mirothinker-service:latest .

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-clean:
	docker compose down -v --rmi all --remove-orphans

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/
