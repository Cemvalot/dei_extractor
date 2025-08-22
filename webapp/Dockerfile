# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_MODE=streamlit

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ell \
    poppler-utils \
    libgl1 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Install Python dependencies for the app user
USER app
RUN pip install --user --no-cache-dir streamlit fastapi uvicorn pydantic python-multipart starlette PyYAML tqdm pdfplumber pandas openpyxl pdf2image pytesseract Pillow pytest pytest-cov httpx

# Copy the entire project (including dei_extractor package)
COPY --chown=app:app .. .

# Add user's local bin to PATH
ENV PATH="/home/app/.local/bin:$PATH"

# Expose ports
EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${FASTAPI_PORT:-8000}/healthz || exit 1

# Default command (can be overridden)
CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"fastapi\" ]; then uvicorn webapp.server.main:app --host 0.0.0.0 --port 8000; else /home/app/.local/bin/streamlit run webapp/streamlit_app.py --server.port=8501 --server.address=0.0.0.0; fi"]
