"""Main FastAPI application for the DEI Extractor web app."""

import logging
import os
import shutil
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from models.responses import HealthResponse
from routers.jobs import router as jobs_router
from routers.transform import router as transform_router
from services.extractor_service import ExtractorService
from services.language_service import LanguageService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables for cleanup and limits
RETENTION_HOURS = int(os.getenv("RETENTION_HOURS", "24"))

# Try to infer runs base dir; fallback to /tmp
RUNS_BASE_CANDIDATES = [
    Path("/tmp"),
    Path.cwd(),  # adjust if your storage writes runs here
]


def _detect_runs_base() -> Path:
    """Detect the base directory used for temporary run directories."""
    for base in RUNS_BASE_CANDIDATES:
        if base.exists():
            return base
    return Path("/tmp")


RUNS_DIR = _detect_runs_base()


def _cleanup_old_runs():
    """Clean up old run directories older than RETENTION_HOURS."""
    cutoff = time.time() - RETENTION_HOURS * 3600
    cleaned_count = 0

    try:
        for p in RUNS_DIR.glob("dei_extractor_run_*"):
            try:
                if p.is_dir() and p.stat().st_mtime < cutoff:
                    shutil.rmtree(p, ignore_errors=True)
                    cleaned_count += 1
                    logger.info(f"Cleaned up old run directory: {p}")
            except Exception as e:
                logger.warning(f"Cleanup failed for {p}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup of old runs: {e}")

    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} old run directories")


def _schedule_cleanup_every(hours: int = 1):
    """Schedule cleanup to run every N hours in a background thread."""

    def loop():
        while True:
            _cleanup_old_runs()
            time.sleep(hours * 3600)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    logger.info(f"Started cleanup scheduler (every {hours} hours)")


# Create FastAPI app
app = FastAPI(
    title="DEI Extractor Web API",
    description="Web API για εξαγωγή δεδομένων DEI από αρχεία PDF",
    version="1.0.0",
)

# Add CORS middleware - production ready
# In production, the proxy handles CORS, so we only allow same-origin
cors_origins = (
    os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
)
if not cors_origins:
    # Default to localhost for development
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
app.include_router(transform_router, prefix="/api/transform", tags=["transform"])


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
    logger.info(f"Starting DEI Extractor API; retention={RETENTION_HOURS}h")

    # Start cleanup scheduler
    _schedule_cleanup_every(hours=1)

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
