"""Zipping service for creating downloadable ZIP files."""

import io
import logging
import zipfile
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ZippingService:
    """Service for creating ZIP files from output directories."""

    def __init__(self):
        """Initialize the zipping service."""
        pass

    def create_zip_from_directory(
        self, directory: Path, include_log: bool = True
    ) -> bytes:
        """Create a ZIP file from a directory containing output files.

        Args:
            directory: Directory containing files to zip
            include_log: Whether to include run_log.txt if it exists

        Returns:
            ZIP file content as bytes
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add all files from the directory
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for the ZIP
                    relative_path = file_path.relative_to(directory)

                    # Skip run_log.txt if not requested
                    if not include_log and file_path.name == "run_log.txt":
                        continue

                    # Add file to ZIP
                    zip_file.write(file_path, relative_path)
                    logger.info(f"Added to ZIP: {relative_path}")

        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()
        zip_buffer.close()

        logger.info(f"Created ZIP with {len(zip_content)} bytes")
        return zip_content

    def create_zip_from_files(self, files: List[Path], output_dir: Path) -> bytes:
        """Create a ZIP file from a list of specific files.

        Args:
            files: List of file paths to include in the ZIP
            output_dir: Output directory (used for relative paths)

        Returns:
            ZIP file content as bytes
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files:
                if file_path.exists() and file_path.is_file():
                    # Calculate relative path
                    try:
                        relative_path = file_path.relative_to(output_dir)
                    except ValueError:
                        # If file is not in output_dir, use just the filename
                        relative_path = file_path.name

                    # Add file to ZIP
                    zip_file.write(file_path, relative_path)
                    logger.info(f"Added to ZIP: {relative_path}")

        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()
        zip_buffer.close()

        logger.info(
            f"Created ZIP with {len(zip_content)} bytes from {len(files)} files"
        )
        return zip_content

    def get_zip_filename(self, run_id: Optional[str] = None) -> str:
        """Generate a filename for the ZIP file.

        Args:
            run_id: Optional run ID to include in filename

        Returns:
            ZIP filename
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if run_id:
            return f"dei_extractor_results_{run_id}_{timestamp}.zip"
        else:
            return f"dei_extractor_results_{timestamp}.zip"
