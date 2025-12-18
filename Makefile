# Makefile for RiceDB Python Client

# Variables
PYTHON := python
UV := uv

.PHONY: all setup test lint format clean check build install-hooks

all: setup check

setup:
	@echo "🍚 Setting up environment..."
	./setup.sh

test:
	@echo "🧪 Running tests..."
	$(UV) run pytest tests/ -v --cov=src/ricedb --cov-report=term-missing

lint:
	@echo "🔍 Running linters..."
	$(UV) run ruff check src/ricedb tests/
	$(UV) run ty check src/ricedb

format:
	@echo "🎨 Formatting code..."
	$(UV) run ruff format src/ricedb tests/

check: format lint test

clean:
	@echo "🧹 Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .ty_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	@echo "📦 Building package..."
	$(UV) build

install-hooks:
	@echo "🪝 Installing git hooks..."
	$(UV) run pre-commit install