# DEI Extractor Makefile
# Common development tasks and automation

.PHONY: help install install-dev test test-cov lint format clean build docs

# Default target
help:
	@echo "DEI Extractor - Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install package with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test         - Run all tests"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  test-fast    - Run only fast tests (skip slow ones)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  type-check   - Run type checking with mypy"
	@echo ""
	@echo "Documentation:"
	@echo "  docs         - Build documentation"
	@echo "  docs-serve   - Serve documentation locally"
	@echo ""
	@echo "Build & Distribution:"
	@echo "  build        - Build package distribution"
	@echo "  clean        - Clean build artifacts"
	@echo ""
	@echo "Development:"
	@echo "  setup        - Complete development setup"
	@echo "  pre-commit   - Install pre-commit hooks"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,docs,test]"

# Testing
test:
	python -m pytest dei_extractor/tests/ tests/ -v

test-cov:
	python -m pytest dei_extractor/tests/ tests/ --cov=dei_extractor --cov-report=html --cov-report=term-missing

test-fast:
	python -m pytest dei_extractor/tests/ tests/ -m "not slow" -v

# Code Quality
lint:
	flake8 dei_extractor/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	python -m black --check dei_extractor/ tests/
	python -m isort --check-only dei_extractor/ tests/

format:
	black dei_extractor/ tests/
	isort dei_extractor/ tests/

type-check:
	mypy dei_extractor/ --ignore-missing-imports

# Documentation
docs:
	cd docs && make html

docs-serve:
	cd docs && python -m http.server 8000

# Build & Distribution
build:
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development Setup
setup: install-dev pre-commit
	@echo "Development environment setup complete!"

pre-commit:
	pre-commit install

# Run the extractor with sample data
run-extract:
	python -m dei_extractor.cli --input "*.pdf" --log-level INFO

run-filter:
	python -m dei_extractor.cli filter_main --inputs "ολα.csv,φoπ.csv,επαγγελματικα.csv"

# Quick validation
validate:
	@echo "Validating project structure..."
	@python -c "import dei_extractor; print('✅ Package imports successfully')"
	@python -c "from dei_extractor import DEIExtractorEnhanced, FilterEkatharistikos; print('✅ Core classes import successfully')"
	@echo "✅ Project structure validation passed"

# Security checks
security:
	bandit -r dei_extractor/ -f json -o bandit-report.json
	safety check

# Performance profiling
profile:
	python -m cProfile -o profile.stats -m dei_extractor.cli --input "*.pdf"

# Docker commands (if using Docker)
docker-build:
	docker build -t dei-extractor .

docker-run:
	docker run -v $(PWD):/app dei-extractor python -m dei_extractor.cli --input "*.pdf"

# CI/CD helpers
ci-test: lint type-check test-cov
	@echo "✅ All CI checks passed"

ci-build: clean build
	@echo "✅ Build completed successfully"

# Environment management
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

venv-clean:
	rm -rf venv/
	@echo "Virtual environment removed"

# Data processing examples
example-extract:
	@echo "Running extraction example..."
	python -m dei_extractor.cli --input "*.pdf" --output-dir "./output" --confidence 0.95

example-filter:
	@echo "Running filter example..."
	python -m dei_extractor.cli filter_main --inputs "ολα.csv" --out-csv "filtered_output.csv"

# Monitoring and logging
logs:
	tail -f warnings.log

logs-clear:
	> warnings.log
	@echo "Log file cleared"

# Backup and restore
backup:
	tar -czf dei_extractor_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude='*.pyc' \
		--exclude='__pycache__' \
		--exclude='.git' \
		--exclude='venv' \
		--exclude='*.log' \
		.

# Helpers
check-deps:
	@echo "Checking dependencies..."
	python -c "import pandas, openpyxl, pdfplumber, pdf2image, pytesseract, psutil; print('✅ All dependencies available')"

check-ocr:
	@echo "Checking OCR availability..."
	python -c "import pytesseract; print(f'✅ Tesseract version: {pytesseract.get_tesseract_version()}')"

# Development workflow
dev-setup: install-dev pre-commit
	@echo "Development environment ready!"
	@echo "Run 'make test' to verify everything works"

dev-test: format lint type-check test
	@echo "✅ Development tests completed"

# Release helpers
release-check: clean test-cov lint type-check build
	@echo "✅ Release checks completed"

version:
	@python -c "import dei_extractor; print(dei_extractor.__version__)"
