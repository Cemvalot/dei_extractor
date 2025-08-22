# DEI Extractor Web App Makefile

.PHONY: help dev docker-build docker-up docker-down test clean

# Default target
help:
	@echo "DEI Extractor Web App - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run Streamlit app locally (requires local dependencies)"
	@echo "  make dev-fastapi  - Run FastAPI app locally (requires local dependencies)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start container with docker-compose"
	@echo "  make docker-down  - Stop and remove containers"
	@echo "  make docker-logs  - Show container logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean up temporary files"
	@echo "  make setup        - Setup development environment"

# Development targets
dev:
	@echo "Starting Streamlit app..."
	cd .. && python -m streamlit run webapp/streamlit_app.py --server.port=8501 --server.address=0.0.0.0

dev-fastapi:
	@echo "Starting FastAPI app..."
	cd .. && python -m uvicorn webapp.server.main:app --host 0.0.0.0 --port 8000 --reload

# Docker targets
docker-build:
	@echo "Building Docker image..."
	docker-compose build

docker-up:
	@echo "Starting containers..."
	docker-compose up -d
	@echo ""
	@echo "Services available at:"
	@echo "  Streamlit: http://localhost:8501"
	@echo "  FastAPI:   http://localhost:8000"
	@echo "  Health:    http://localhost:8000/healthz"

docker-down:
	@echo "Stopping containers..."
	docker-compose down

docker-logs:
	@echo "Showing container logs..."
	docker-compose logs -f

# Testing targets
test:
	@echo "Running tests..."
	cd .. && python -m pytest webapp/server/tests/ -v

# Utility targets
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf tmp/
	rm -rf .pytest_cache/

setup:
	@echo "Setting up development environment..."
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing local package..."
	cd .. && pip install -e .
	@echo "Setup complete!"

# Environment-specific targets
streamlit-mode:
	@echo "Setting APP_MODE=streamlit..."
	@echo "APP_MODE=streamlit" > .env
	@echo "Run 'make docker-up' to start in Streamlit mode"

fastapi-mode:
	@echo "Setting APP_MODE=fastapi..."
	@echo "APP_MODE=fastapi" > .env
	@echo "Run 'make docker-up' to start in FastAPI mode"

# Quick start
quick-start:
	@echo "Quick start - Streamlit mode..."
	@echo "APP_MODE=streamlit" > .env
	make docker-build
	make docker-up
	@echo ""
	@echo "🎉 DEI Extractor Web App is running!"
	@echo "Open http://localhost:8501 in your browser"
