"""FastAPI router for job processing endpoints."""

import io
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse

from ..models.requests import ProcessingOptions
from ..models.responses import ErrorResponse, JobStatus
from ..services.extractor_service import ExtractorService
from ..services.storage import StorageService
from ..services.zipping import ZippingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/", response_model=JobStatus)
async def process_files(
    files: List[UploadFile] = File(
        ..., description="PDF files or ZIP archive to process"
    ),
    apply_filter: bool = Form(
        default=False, description="Apply Εκαθαριστικός filtering"
    ),
    verbose: bool = Form(default=False, description="Enable verbose logging"),
    language: str = Form(default="en", description="UI language (en or gr)"),
) -> JobStatus:
    """Process uploaded PDF files or ZIP archive."""

    # Validate files
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Check file types and sizes
    total_size = 0
    max_size_mb = 200  # TODO: Make configurable
    max_size_bytes = max_size_mb * 1024 * 1024

    for file in files:
        if not file.filename:
            continue

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".pdf", ".zip"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file_ext}. Only .pdf and .zip files are allowed.",
            )

        # Read file content to check size
        content = await file.read()
        total_size += len(content)

        if total_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Total file size ({total_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)",
            )

        # Reset file position for later reading
        await file.seek(0)

    # Initialize services
    storage_service = StorageService()
    extractor_service = ExtractorService()
    zipping_service = ZippingService()

    # Create run directory
    run_dir = storage_service.create_run_directory()

    try:
        # Process uploaded files
        pdf_files = []

        for file in files:
            if not file.filename:
                continue

            content = await file.read()
            file_path = storage_service.save_uploaded_file(
                content, file.filename, run_dir
            )

            # If it's a ZIP file, extract PDFs
            if file_path.suffix.lower() == ".zip":
                extracted_pdfs = storage_service.extract_zip_file(file_path, run_dir)
                pdf_files.extend(extracted_pdfs)
            else:
                pdf_files.append(file_path)

        # Validate input directory
        input_dir = run_dir / "input"
        is_valid, validation_msg = extractor_service.validate_input_directory(input_dir)

        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_msg)

        # Run extractor
        output_dir = run_dir / "output"
        success, log_output, warnings = extractor_service.run_extractor(
            input_dir=input_dir,
            output_dir=output_dir,
            apply_filter=apply_filter,
            verbose=verbose,
        )

        # Get output summary
        output_summary = extractor_service.get_output_summary(output_dir)

        # Create run log
        log_content = (
            f"Processing completed\n\nLog output:\n{log_output}\n\nWarnings:\n"
            + "\n".join(warnings)
        )
        storage_service.create_run_log(run_dir, log_content)

        # Get output files
        output_files = storage_service.get_output_files(run_dir)
        output_file_names = [f.name for f in output_files if f.is_file()]

        return JobStatus(
            success=success,
            message="Processing completed successfully"
            if success
            else "Processing failed",
            warnings=warnings,
            output_files=output_file_names,
            output_summary=output_summary,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up run directory
        storage_service.cleanup_run_directory(run_dir)


@router.get("/download/{run_id}")
async def download_results(run_id: str) -> StreamingResponse:
    """Download processing results as ZIP file."""

    # This endpoint would be used if we want to separate processing from download
    # For now, we'll return a simple error since we clean up immediately
    raise HTTPException(
        status_code=404, detail="Results not found (already cleaned up)"
    )


@router.post("/download")
async def process_and_download(
    files: List[UploadFile] = File(
        ..., description="PDF files or ZIP archive to process"
    ),
    apply_filter: bool = Form(
        default=False, description="Apply Εκαθαριστικός filtering"
    ),
    verbose: bool = Form(default=False, description="Enable verbose logging"),
    language: str = Form(default="en", description="UI language (en or gr)"),
) -> StreamingResponse:
    """Process files and return results as ZIP download."""

    # Initialize services
    storage_service = StorageService()
    extractor_service = ExtractorService()
    zipping_service = ZippingService()

    # Create run directory
    run_dir = storage_service.create_run_directory()

    try:
        # Process uploaded files (same logic as process_files)
        pdf_files = []

        for file in files:
            if not file.filename:
                continue

            content = await file.read()
            file_path = storage_service.save_uploaded_file(
                content, file.filename, run_dir
            )

            # If it's a ZIP file, extract PDFs
            if file_path.suffix.lower() == ".zip":
                extracted_pdfs = storage_service.extract_zip_file(file_path, run_dir)
                pdf_files.extend(extracted_pdfs)
            else:
                pdf_files.append(file_path)

        # Validate input directory
        input_dir = run_dir / "input"
        is_valid, validation_msg = extractor_service.validate_input_directory(input_dir)

        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_msg)

        # Run extractor
        output_dir = run_dir / "output"
        success, log_output, warnings = extractor_service.run_extractor(
            input_dir=input_dir,
            output_dir=output_dir,
            apply_filter=apply_filter,
            verbose=verbose,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Processing failed")

        # Create run log
        log_content = (
            f"Processing completed\n\nLog output:\n{log_output}\n\nWarnings:\n"
            + "\n".join(warnings)
        )
        storage_service.create_run_log(run_dir, log_content)

        # Create ZIP file
        zip_content = zipping_service.create_zip_from_directory(
            run_dir, include_log=True
        )
        zip_filename = zipping_service.get_zip_filename()

        # Return ZIP as streaming response
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up run directory
        storage_service.cleanup_run_directory(run_dir)
