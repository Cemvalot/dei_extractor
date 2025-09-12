import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from models.responses import ErrorResponse
from services.storage import StorageService

from dei_extractor.transform.final_2023 import compute_final, load_phase1, write_final

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_XLSX = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",  # some browsers send legacy type
}
ALLOWED_CSV = {"text/csv", "application/csv", "text/plain"}


def _safe_suffix_ok(filename: str, ok: set[str]) -> bool:
    suffix = Path(filename).suffix.lower()
    if suffix == ".xlsx":
        return True
    if suffix == ".csv" and ("csv" in "".join(ok)):
        return True
    return False


@router.post(
    "/",
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def transform_phase1(
    phase1: UploadFile = File(..., description="Phase-1 Excel (.xlsx)"),
    year: int = Form(2023),
    keep_str_ids: bool = Form(False),
    class_map: Optional[UploadFile] = File(
        default=None, description="Optional classification CSV"
    ),
):
    """
    Run the Final transformation for the given year and return the Excel file.
    """
    # Basic validation (content-type & filename)
    if not phase1.filename or not _safe_suffix_ok(phase1.filename, ALLOWED_XLSX):
        raise HTTPException(status_code=400, detail="phase1 must be an .xlsx file")

    if phase1.content_type not in ALLOWED_XLSX:
        logger.warning(f"phase1 content-type {phase1.content_type} not in ALLOWED_XLSX")

    if class_map:
        if (not class_map.filename) or Path(
            class_map.filename
        ).suffix.lower() != ".csv":
            raise HTTPException(status_code=400, detail="class_map must be a .csv file")
        if class_map.content_type not in ALLOWED_CSV:
            logger.warning(
                f"class_map content-type {class_map.content_type} not in ALLOWED_CSV"
            )

    storage = StorageService()
    run_dir = storage.create_run_directory()
    input_dir = run_dir / "input"
    output_dir = run_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Save uploads
        phase1_path = storage.save_uploaded_file(
            await phase1.read(), phase1.filename, run_dir
        )
        class_map_path = None
        if class_map:
            class_map_path = storage.save_uploaded_file(
                await class_map.read(), class_map.filename, run_dir
            )
        else:
            # fallback to default mapping if available
            default_map = (
                Path(__file__).resolve().parents[3] / "scripts" / "class_mapping.csv"
            )
            if default_map.exists():
                class_map_path = default_map

        # Transform
        df = load_phase1(str(phase1_path))
        final_df = compute_final(
            df,
            year=year,
            class_map_path=str(class_map_path) if class_map_path else None,
        )

        if keep_str_ids and "ΠΑΡΟΧΗ" in final_df.columns:
            final_df["ΠΑΡΟΧΗ"] = final_df["ΠΑΡΟΧΗ"].astype(str)

        out_name = f"PAROXES_FINAL_{year}.xlsx"
        out_path = output_dir / out_name
        write_final(final_df, str(out_path))

        # Return file
        return FileResponse(
            path=str(out_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=out_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Transform failed")
        raise HTTPException(status_code=422, detail=f"Transform failed: {e}")
    # NOTE: we rely on background retention cleanup to delete run_dir later
