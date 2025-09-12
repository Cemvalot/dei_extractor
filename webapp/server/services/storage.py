"""Storage service for managing temporary directories and file operations."""

import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing temporary storage and file operations."""

    def __init__(self, base_temp_dir: Optional[str] = None):
        """Initialize storage service.

        Args:
            base_temp_dir: Base directory for temporary files. If None, uses system temp dir.
        """
        self.base_temp_dir = (
            Path(base_temp_dir) if base_temp_dir else Path(tempfile.gettempdir())
        )
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)

    def create_run_directory(self) -> Path:
        """Create a unique temporary directory for a processing run.

        Returns:
            Path to the created directory
        """
        run_id = str(uuid.uuid4())
        run_dir = self.base_temp_dir / f"dei_extractor_run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (run_dir / "input").mkdir(exist_ok=True)
        (run_dir / "output").mkdir(exist_ok=True)

        logger.info(f"Created run directory: {run_dir}")
        return run_dir

    def cleanup_run_directory(self, run_dir: Path) -> bool:
        """Clean up a run directory and all its contents.

        Args:
            run_dir: Path to the run directory to clean up

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if run_dir.exists():
                shutil.rmtree(run_dir)
                logger.info(f"Cleaned up run directory: {run_dir}")
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup run directory {run_dir}: {e}")
            return False
        return False

    def cleanup_old_runs(self, max_age_hours: int = 24) -> int:
        """Clean up old run directories.

        Args:
            max_age_hours: Maximum age in hours for directories to keep

        Returns:
            Number of directories cleaned up
        """
        import time

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0

        try:
            for item in self.base_temp_dir.iterdir():
                if item.is_dir() and item.name.startswith("dei_extractor_run_"):
                    # Check if directory is old enough to delete
                    if current_time - item.stat().st_mtime > max_age_seconds:
                        if self.cleanup_run_directory(item):
                            cleaned_count += 1
        except Exception as e:
            logger.error(f"Error during cleanup of old runs: {e}")

        logger.info(f"Cleaned up {cleaned_count} old run directories")
        return cleaned_count

    def save_uploaded_file(
        self, file_content: bytes, filename: str, run_dir: Path
    ) -> Path:
        """Save an uploaded file to the run directory.

        Args:
            file_content: File content as bytes
            filename: Original filename
            run_dir: Run directory to save to

        Returns:
            Path to the saved file
        """
        input_dir = run_dir / "input"
        file_path = input_dir / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"Saved uploaded file: {file_path}")
        return file_path

    def extract_zip_file(self, zip_path: Path, run_dir: Path) -> List[Path]:
        """Extract a ZIP file to the input directory using safe extraction.

        Args:
            zip_path: Path to the ZIP file
            run_dir: Run directory to extract to

        Returns:
            List of extracted PDF file paths
        """
        from utils.zip_safe import safe_extract

        input_dir = run_dir / "input"
        extracted_files = []

        try:
            # Use safe extraction to prevent zip-slip attacks
            safe_extract(zip_path, input_dir)

            # Find all extracted PDF files
            for file_path in input_dir.rglob("*.pdf"):
                if file_path.is_file():
                    extracted_files.append(file_path)
                    logger.info(f"Extracted PDF: {file_path}")

        except Exception as e:
            logger.error(f"Error extracting ZIP file {zip_path}: {e}")
            raise

        return extracted_files

    def get_output_files(self, run_dir: Path) -> List[Path]:
        """Get all output files from a run directory.

        Args:
            run_dir: Run directory to check

        Returns:
            List of output file paths
        """
        output_dir = run_dir / "output"
        if not output_dir.exists():
            return []

        return list(output_dir.glob("*"))

    def create_run_log(self, run_dir: Path, log_content: str) -> Path:
        """Create a run log file.

        Args:
            run_dir: Run directory to create log in
            log_content: Content to write to the log

        Returns:
            Path to the created log file
        """
        log_path = run_dir / "run_log.txt"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_content)

        logger.info(f"Created run log: {log_path}")
        return log_path
