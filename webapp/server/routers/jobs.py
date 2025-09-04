"""
Clean version of jobs router with working endpoints.
"""

import json
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from ..models.requests import ProcessingOptions
from ..models.responses import ErrorResponse, JobStatus
from ..services.extractor_service import ExtractorService
from ..services.storage import StorageService
from ..services.zipping import ZippingService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "jobs"}


@router.post("/")
async def process_files(
    files: List[UploadFile] = File(
        ..., description="PDF files or ZIP archive to process"
    ),
    options: ProcessingOptions = ProcessingOptions(),
) -> JobStatus:
    """Process uploaded files synchronously."""

    # Initialize services
    storage_service = StorageService()
    extractor_service = ExtractorService()

    # Create temporary run directory
    run_dir = storage_service.create_run_directory()

    try:
        # Read all files first
        file_contents = []
        for file in files:
            if not file.filename:
                continue
            content = await file.read()
            file_contents.append((file.filename, content))

        # Save files
        pdf_files = []
        for filename, content in file_contents:
            file_path = storage_service.save_uploaded_file(content, filename, run_dir)

            if file_path.suffix.lower() == ".zip":
                extracted_pdfs = storage_service.extract_zip_file(file_path, run_dir)
                pdf_files.extend(extracted_pdfs)
            else:
                pdf_files.append(file_path)

        if not pdf_files:
            raise HTTPException(status_code=400, detail="No PDF files found to process")

        # Process files
        input_dir = run_dir / "input"
        output_dir = run_dir / "output"

        success, log_output, warnings = extractor_service.run_extractor(
            input_dir=input_dir,
            output_dir=output_dir,
            apply_filter=options.apply_filter,
            verbose=options.verbose,
        )

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
            output_summary=log_output,
        )

    except HTTPException:
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

    # Validate file types
    for file in files:
        if not file.filename:
            continue
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".pdf", ".zip"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file_ext}. Only .pdf and .zip files are allowed.",
            )

    # Initialize services
    storage_service = StorageService()
    extractor_service = ExtractorService()
    zipping_service = ZippingService()

    # Create run directory
    run_dir = storage_service.create_run_directory()
    run_id = run_dir.name.replace("dei_extractor_run_", "")
    logger.info(f"Created run directory: {run_dir}, run_id: {run_id}")

    # Read all files immediately to avoid I/O issues
    file_contents = []
    total_size = 0
    max_size_mb = 200
    max_size_bytes = max_size_mb * 1024 * 1024

    logger.info(f"Reading {len(files)} files...")
    for file in files:
        if not file.filename:
            continue
        logger.info(f"Reading file: {file.filename}")
        content = await file.read()
        file_contents.append((file.filename, content))
        total_size += len(content)
        logger.info(f"Read {len(content)} bytes from {file.filename}")

        if total_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Total file size ({total_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)",
            )

    logger.info(
        f"Successfully read {len(file_contents)} files, total size: {total_size} bytes"
    )

    async def generate_progress():
        """Generate progress updates."""
        try:
            # Initial progress
            yield f"data: {json.dumps({'percentage': 0, 'message': 'Preparing files...', 'run_id': run_id})}\n\n"

            # Process files
            pdf_files = []
            for i, (filename, content) in enumerate(file_contents):
                logger.info(f"Processing file {i+1}/{len(file_contents)}: {filename}")
                file_path = storage_service.save_uploaded_file(
                    content, filename, run_dir
                )
                logger.info(f"Saved file to: {file_path}")

                if file_path.suffix.lower() == ".zip":
                    extracted_pdfs = storage_service.extract_zip_file(
                        file_path, run_dir
                    )
                    pdf_files.extend(extracted_pdfs)
                    yield f"data: {json.dumps({'percentage': 10 + (i / len(file_contents)) * 10, 'message': f'Extracted {len(extracted_pdfs)} PDFs from {filename}', 'run_id': run_id})}\n\n"
                else:
                    pdf_files.append(file_path)
                    yield f"data: {json.dumps({'percentage': 10 + (i / len(file_contents)) * 10, 'message': f'Processed {filename}', 'run_id': run_id})}\n\n"

            if not pdf_files:
                yield f"data: {json.dumps({'percentage': 100, 'message': 'No PDF files found to process', 'run_id': run_id})}\n\n"
                return

            # Progress: 20-80% - PDF processing
            yield f"data: {json.dumps({'percentage': 20, 'message': f'Processing {len(pdf_files)} PDF files...', 'run_id': run_id})}\n\n"

            # Process PDFs
            input_dir = run_dir / "input"
            output_dir = run_dir / "output"

            logger.info(
                f"Starting extraction with input_dir: {input_dir}, output_dir: {output_dir}"
            )
            success, log_output, warnings = extractor_service.run_extractor(
                input_dir=input_dir,
                output_dir=output_dir,
                apply_filter=apply_filter,
                verbose=verbose,
            )
            logger.info(
                f"Extraction completed. Success: {success}, warnings: {len(warnings)}"
            )

            if success:
                # Progress: 80-90% - Creating ZIP
                yield f"data: {json.dumps({'percentage': 80, 'message': 'Creating download package...', 'run_id': run_id})}\n\n"

                # Create ZIP file
                logger.info(f"Creating ZIP from directory: {run_dir}")
                zip_content = zipping_service.create_zip_from_directory(
                    run_dir, include_log=True
                )
                zip_filename = zipping_service.get_zip_filename(run_id)

                # Save ZIP file to disk
                zip_file_path = run_dir / zip_filename
                with open(zip_file_path, "wb") as f:
                    f.write(zip_content)
                logger.info(f"Saved ZIP file to: {zip_file_path}")

                # Final progress update
                yield f"data: {json.dumps({'percentage': 100, 'message': 'Processing completed successfully', 'download_ready': True, 'filename': zip_filename, 'run_id': run_id})}\n\n"
            else:
                yield f"data: {json.dumps({'percentage': 100, 'message': 'Processing failed', 'run_id': run_id})}\n\n"

        except Exception as e:
            logger.error(f"Error processing files: {e}", exc_info=True)
            yield f"data: {json.dumps({'percentage': 100, 'message': f'Error: {str(e)}', 'run_id': run_id})}\n\n"

    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@router.get("/download/{run_id}")
async def download_results(run_id: str) -> FileResponse:
    """Download processing results as ZIP file."""

    storage_service = StorageService()

    # Find the run directory
    run_dir = storage_service.base_temp_dir / f"dei_extractor_run_{run_id}"

    logger.info(f"Looking for run directory: {run_dir}")

    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Results not found or expired")

    # Find ZIP files in the run directory
    zip_files = list(run_dir.glob("*.zip"))
    all_files = list(run_dir.rglob("*"))

    logger.info(f"Files in run directory: {[str(f) for f in all_files]}")
    logger.info(f"ZIP files found: {[str(f) for f in zip_files]}")

    if not zip_files:
        raise HTTPException(
            status_code=404,
            detail=f"ZIP file not found in {run_dir}. Available files: {[f.name for f in all_files if f.is_file()]}",
        )

    zip_file = zip_files[0]

    return FileResponse(
        path=str(zip_file), filename=zip_file.name, media_type="application/zip"
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

    # Create temporary run directory
    run_dir = storage_service.create_run_directory()

    try:
        # Read all files first
        file_contents = []
        for file in files:
            if not file.filename:
                continue
            content = await file.read()
            file_contents.append((file.filename, content))

        # Save files
        pdf_files = []
        for filename, content in file_contents:
            file_path = storage_service.save_uploaded_file(content, filename, run_dir)

            if file_path.suffix.lower() == ".zip":
                extracted_pdfs = storage_service.extract_zip_file(file_path, run_dir)
                pdf_files.extend(extracted_pdfs)
            else:
                pdf_files.append(file_path)

        if not pdf_files:
            raise HTTPException(status_code=400, detail="No PDF files found to process")

        # Process files
        input_dir = run_dir / "input"
        output_dir = run_dir / "output"

        success, log_output, warnings = extractor_service.run_extractor(
            input_dir=input_dir,
            output_dir=output_dir,
            apply_filter=apply_filter,
            verbose=verbose,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Processing failed")

        # Create ZIP file
        zip_content = zipping_service.create_zip_from_directory(
            run_dir, include_log=True
        )
        zip_filename = zipping_service.get_zip_filename()

        # Return ZIP as streaming response
        import io

        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up run directory
        storage_service.cleanup_run_directory(run_dir)
