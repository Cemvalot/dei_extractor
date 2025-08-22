"""Extractor service that interfaces with the dei_extractor package."""

import contextlib
import io
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ExtractorService:
    """Service for running the dei_extractor package."""

    def __init__(self, dei_extractor_path: Optional[str] = None):
        """Initialize the extractor service.

        Args:
            dei_extractor_path: Path to the dei_extractor package. If None, assumes it's installed.
        """
        self.dei_extractor_path = dei_extractor_path

    def run_extractor(
        self,
        input_dir: Path,
        output_dir: Path,
        apply_filter: bool = False,
        verbose: bool = False,
        config_file: Optional[str] = None,
    ) -> Tuple[bool, str, List[str]]:
        """Run the dei_extractor on the input directory.

        Args:
            input_dir: Directory containing PDF files to process
            output_dir: Directory to write output files to
            apply_filter: Whether to apply Εκαθαριστικός filtering
            verbose: Whether to enable verbose logging
            config_file: Optional path to configuration file

        Returns:
            Tuple of (success, log_output, warnings)
        """
        # Build command arguments
        cmd = [
            sys.executable,
            "-m",
            "dei_extractor.cli",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ]

        if apply_filter:
            cmd.append("--filter")

        if verbose:
            cmd.append("--verbose")

        if config_file:
            cmd.extend(["--config", config_file])

        logger.info(f"Running extractor command: {' '.join(cmd)}")

        # Capture output
        log_output = ""
        warnings = []

        try:
            # Run the command and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=300,  # 5 minute timeout
            )

            # Collect log output
            if result.stdout:
                log_output += result.stdout
            if result.stderr:
                log_output += result.stderr

            # Check for warnings in the output
            for line in log_output.split("\n"):
                if "WARNING" in line.upper() or "WARN" in line.upper():
                    warnings.append(line.strip())

            # Check if the command was successful
            success = result.returncode == 0

            if success:
                logger.info("Extractor completed successfully")
            else:
                logger.error(f"Extractor failed with return code {result.returncode}")

            return success, log_output, warnings

        except subprocess.TimeoutExpired:
            error_msg = "Extractor timed out after 5 minutes"
            logger.error(error_msg)
            return False, error_msg, [error_msg]

        except Exception as e:
            error_msg = f"Error running extractor: {e}"
            logger.error(error_msg)
            return False, error_msg, [error_msg]

    def validate_input_directory(self, input_dir: Path) -> Tuple[bool, str]:
        """Validate that the input directory contains PDF files.

        Args:
            input_dir: Directory to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not input_dir.exists():
            return False, f"Input directory does not exist: {input_dir}"

        if not input_dir.is_dir():
            return False, f"Input path is not a directory: {input_dir}"

        pdf_files = list(input_dir.glob("*.pdf"))
        if not pdf_files:
            return False, f"No PDF files found in {input_dir}"

        return True, f"Found {len(pdf_files)} PDF files"

    def get_output_summary(self, output_dir: Path) -> Dict[str, any]:
        """Get a summary of the output files.

        Args:
            output_dir: Output directory to analyze

        Returns:
            Dictionary with output summary
        """
        if not output_dir.exists():
            return {"files": [], "count": 0, "types": {}}

        files = list(output_dir.glob("*"))
        file_types = {}

        for file_path in files:
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1

        return {
            "files": [f.name for f in files if f.is_file()],
            "count": len([f for f in files if f.is_file()]),
            "types": file_types,
        }

    def check_ocr_requirements(self) -> Tuple[bool, List[str]]:
        """Check if OCR requirements are available.

        Returns:
            Tuple of (is_available, missing_components)
        """
        missing = []

        # Check for tesseract
        try:
            result = subprocess.run(
                ["tesseract", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                missing.append("tesseract")
        except FileNotFoundError:
            missing.append("tesseract")

        # Check for poppler-utils (pdftoppm)
        try:
            result = subprocess.run(["pdftoppm", "-h"], capture_output=True, text=True)
            if result.returncode != 0:
                missing.append("poppler-utils")
        except FileNotFoundError:
            missing.append("poppler-utils")

        return len(missing) == 0, missing
