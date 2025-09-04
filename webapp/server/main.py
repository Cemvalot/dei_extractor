"""Main FastAPI application for the DEI Extractor web app."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models.responses import HealthResponse
from .routers.jobs import router as jobs_router
from .services.extractor_service import ExtractorService
from .services.language_service import LanguageService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DEI Extractor Web API",
    description="Web API για εξαγωγή δεδομένων DEI από αρχεία PDF",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])


@app.get("/", response_class=FileResponse)
async def root():
    """Serve the main HTML page."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="Static files not found")


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    extractor_service = ExtractorService()
    ocr_available, missing_components = extractor_service.check_ocr_requirements()

    return HealthResponse(status="ok", version="1.0.0", ocr_available=ocr_available)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("DEI Extractor Web API starting up...")

    # Check OCR requirements
    extractor_service = ExtractorService()
    ocr_available, missing_components = extractor_service.check_ocr_requirements()

    if not ocr_available:
        logger.warning(f"OCR requirements missing: {missing_components}")
        logger.warning("PDF processing may fail for files requiring OCR")
    else:
        logger.info("OCR requirements available")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("DEI Extractor Web API shutting down...")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("FASTAPI_PORT", 8000))
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")

    uvicorn.run("webapp.server.main:app", host=host, port=port, reload=True)
