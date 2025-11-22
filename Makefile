.PHONY: help format lint type-check test clean install pre-commit

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install development dependencies
	uv sync --all-extras --dev

format:  ## Format code with ruff
	ruff format maize examples tests
	ruff check --fix maize examples tests

format-check:  ## Check if code is formatted correctly
	ruff format --check maize examples tests
	ruff check maize examples tests

lint:  ## Run linters (ruff)
	ruff check maize examples tests

lint-fix:  ## Run linters and fix issues
	ruff check --fix maize examples tests

type-check:  ## Run type checking with mypy
	mypy maize

test:  ## Run tests with pytest
	pytest -s

test-cov:  ## Run tests with coverage
	pytest --cov=maize --cov-report=html --cov-report=term

pre-commit:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install

clean:  ## Clean up generated files
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: format lint type-check test  ## Run all checks
