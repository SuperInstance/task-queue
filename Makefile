# Makefile for task-queue development

.PHONY: help install install-dev install-go test test-python test-go lint lint-python lint-go format format-python format-go build build-python build-go docker docker-build docker-run clean clean-python clean-go docs docs-python docs-go benchmark benchmark-python benchmark-go

# Default target
help:
	@echo "Available targets:"
	@echo "  install          - Install Python dependencies"
	@echo "  install-dev      - Install Python development dependencies"
	@echo "  install-go       - Install Go dependencies"
	@echo "  test             - Run all tests"
	@echo "  test-python      - Run Python tests"
	@echo "  test-go          - Run Go tests"
	@echo "  lint             - Run all linters"
	@echo "  lint-python      - Run Python linters"
	@echo "  lint-go          - Run Go linters"
	@echo "  format           - Format all code"
	@echo "  format-python    - Format Python code"
	@echo "  format-go        - Format Go code"
	@echo "  build            - Build all packages"
	@echo "  build-python     - Build Python package"
	@echo "  build-go         - Build Go binary"
	@echo "  docker           - Build Docker images"
	@echo "  docker-build     - Build Docker image"
	@echo "  docker-run       - Run Docker containers"
	@echo "  clean            - Clean all build artifacts"
	@echo "  clean-python     - Clean Python build artifacts"
	@echo "  clean-go         - Clean Go build artifacts"
	@echo "  docs             - Generate all documentation"
	@echo "  docs-python      - Generate Python documentation"
	@echo "  docs-go          - Generate Go documentation"
	@echo "  benchmark        - Run all benchmarks"
	@echo "  benchmark-python - Run Python benchmarks"
	@echo "  benchmark-go     - Run Go benchmarks"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"
	pre-commit install

install-go:
	cd go && go mod download
	cd go && go mod tidy

# Testing
test: test-python test-go

test-python:
	pytest python/tests/ -v --cov=python/taskqueue --cov-report=html --cov-report=term

test-go:
	cd go && go test -v -race -coverprofile=coverage.txt ./...
	cd go && go tool cover -html=coverage.txt -o coverage.html

# Linting
lint: lint-python lint-go

lint-python:
	black --check python/
	isort --check-only python/
	pylint python/taskqueue
	mypy python/taskqueue

lint-go:
	cd go && golangci-lint run --timeout 5m

# Formatting
format: format-python format-go

format-python:
	black python/
	isort python/

format-go:
	cd go && go fmt ./...
	cd go && goimports -w .

# Building
build: build-python build-go

build-python:
	python setup.py sdist bdist_wheel

build-go:
	cd go && go build -o bin/tq-worker cmd/worker/main.go
	cd go && go build -o bin/tq-scheduler cmd/scheduler/main.go
	cd go && go build -o bin/tq-api cmd/api/main.go

# Docker
docker: docker-build

docker-build:
	docker build -t task-queue:latest .

docker-run:
	docker-compose up -d
	docker-compose logs -f

# Cleaning
clean: clean-python clean-go

clean-python:
	rm -rf python/build/
	rm -rf python/dist/
	rm -rf python/*.egg-info/
	rm -rf python/.pytest_cache/
	rm -rf python/htmlcov/
	find python/ -type d -name __pycache__ -exec rm -rf {} +
	find python/ -type f -name "*.pyc" -delete

clean-go:
	rm -rf go/bin/
	rm -rf go/coverage.txt
	rm -rf go/coverage.html

# Documentation
docs: docs-python docs-go

docs-python:
	cd python && sphinx-build -b html docs/ docs/_build/html

docs-go:
	cd go && godoc -http=:6060

# Benchmarking
benchmark: benchmark-python benchmark-go

benchmark-python:
	pytest python/tests/ -v --benchmark-only --benchmark-json=benchmark.json

benchmark-go:
	cd go && go test -bench=. -benchmem ./...

# Development helpers
dev-python:
	python -m taskqueue worker --broker=redis://localhost:6379/0 --queues=default --loglevel=DEBUG

dev-go:
	cd go && go run cmd/worker/main.go --broker=redis://localhost:6379/0 --queues=default

redis:
	docker run -d -p 6379:6379 redis:7-alpine

rabbitmq:
	docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management-alpine

# Quick start
quick-start: redis
	sleep 2
	pip install -e .
	@echo "Task queue is ready!"
	@echo "Redis: redis://localhost:6379"
	@echo "Start worker: python -m taskqueue worker"
