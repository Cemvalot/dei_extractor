"""FastAPI router for job processing endpoints."""

import io
import json
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


def create_progress_stream():
    """Create a progress stream for Server-Sent Events."""
    progress_queue = []

    def progress_callback(percentage: int, message: str):
        """Progress callback that adds to the queue."""
        progress_data = {
            "percentage": percentage,
            "message": message,
            "timestamp": logging.time.time(),
        }
        progress_queue.append(progress_data)

    def progress_generator():
        """Generate progress events."""
        while True:
            if progress_queue:
                data = progress_queue.pop(0)
                yield f"data: {json.dumps(data)}\n\n"
            else:
                yield f"data: {json.dumps({'percentage': 0, 'message': 'Waiting...'})}\n\n"

    return progress_callback, progress_generator


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


@router.post("/progress")
async def process_files_with_progress(
    files: List[UploadFile] = File(
        ..., description="PDF files or ZIP archive to process"
    ),
    apply_filter: bool = Form(
        default=False, description="Apply Εκαθαριστικός filtering"
    ),
    verbose: bool = Form(default=False, description="Enable verbose logging"),
    language: str = Form(default="en", description="UI language (en or gr)"),
) -> StreamingResponse:
    """Process uploaded files with real-time progress updates via Server-Sent Events."""

    # Validate files
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Check file types and sizes
    total_size = 0
    max_size_mb = 200
    max_size_bytes = max_size_mb * 1024 * 1024

    for file in files:
        if not file.filename:
            continue

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".pdf", ".zip"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file_ext}. Only .pdf and .zip files are allowed.",
            )

        content = await file.read()
        total_size += len(content)

        if total_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Total file size ({total_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)",
            )

        await file.seek(0)

    async def process_with_progress():
        """Process files with progress updates."""
        storage_service = StorageService()
        extractor_service = ExtractorService()
        zipping_service = ZippingService()

        run_dir = storage_service.create_run_directory()

        try:
            # Progress: 0-20% - File preparation
            yield f"data: {json.dumps({'percentage': 0, 'message': 'Preparing files...'})}\n\n"

            pdf_files = []
            for i, file in enumerate(files):
                if not file.filename:
                    continue

                content = await file.read()
                file_path = storage_service.save_uploaded_file(
                    content, file.filename, run_dir
                )

                if file_path.suffix.lower() == ".zip":
                    extracted_pdfs = storage_service.extract_zip_file(
                        file_path, run_dir
                    )
                    pdf_files.extend(extracted_pdfs)
                else:
                    pdf_files.append(file_path)

                # Update progress for file preparation
                progress = int(20 * (i + 1) / len(files))
                yield f"data: {json.dumps({'percentage': progress, 'message': f'Prepared {i+1}/{len(files)} files'})}\n\n"

            # Progress: 20-30% - Validation
            yield f"data: {json.dumps({'percentage': 20, 'message': 'Validating input...'})}\n\n"

            input_dir = run_dir / "input"
            is_valid, validation_msg = extractor_service.validate_input_directory(
                input_dir
            )

            if not is_valid:
                yield f"data: {json.dumps({'percentage': 100, 'message': f'Validation failed: {validation_msg}'})}\n\n"
                return

            yield f"data: {json.dumps({'percentage': 30, 'message': 'Validation complete'})}\n\n"

            # Progress: 30-90% - Processing with granular updates
            progress_queue = []

            def progress_callback(percentage: int, message: str):
                # Scale the percentage from 30-90 range
                scaled_percentage = 30 + int(percentage * 0.6)
                progress_queue.append((scaled_percentage, message))

            output_dir = run_dir / "output"
            success, log_output, warnings = extractor_service.run_extractor(
                input_dir=input_dir,
                output_dir=output_dir,
                apply_filter=apply_filter,
                verbose=verbose,
                progress_callback=progress_callback,
            )

            # Yield all progress updates that were queued
            for percentage, message in progress_queue:
                yield f"data: {json.dumps({'percentage': percentage, 'message': message})}\n\n"

            # Progress: 90-95% - Creating outputs
            yield f"data: {json.dumps({'percentage': 90, 'message': 'Creating output files...'})}\n\n"

            log_content = (
                f"Processing completed\n\nLog output:\n{log_output}\n\nWarnings:\n"
                + "\n".join(warnings)
            )
            storage_service.create_run_log(run_dir, log_content)

            # Progress: 95-100% - Creating ZIP
            yield f"data: {json.dumps({'percentage': 95, 'message': 'Creating ZIP file...'})}\n\n"

            zip_content = zipping_service.create_zip_from_directory(
                run_dir, include_log=True
            )
            zip_filename = zipping_service.get_zip_filename()

            # Final progress update
            if success:
                yield f"data: {json.dumps({'percentage': 100, 'message': 'Processing completed successfully', 'download_ready': True, 'filename': zip_filename})}\n\n"
            else:
                yield f"data: {json.dumps({'percentage': 100, 'message': 'Processing failed'})}\n\n"

        except Exception as e:
            logger.error(f"Error processing files: {e}")
            yield f"data: {json.dumps({'percentage': 100, 'message': f'Error: {str(e)}'})}\n\n"
        finally:
            storage_service.cleanup_run_directory(run_dir)

    return StreamingResponse(
        process_with_progress(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


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
