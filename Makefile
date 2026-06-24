.PHONY: install dev-install lint format typecheck test test-cov clean

PACKAGE = setupvault

install:
	pip install .

dev-install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/ tests/

test:
	pytest

test-cov:
	pytest --cov --cov-report=term --cov-report=html

test-all:
	tox

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
