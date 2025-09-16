"""Extractor service that interfaces with the dei_extractor package."""

import contextlib
import io
import logging
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

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
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Tuple[bool, str, List[str]]:
        """Run the dei_extractor on the input directory with granular progress tracking.

        Args:
            input_dir: Directory containing PDF files to process
            output_dir: Directory to write output files to
            apply_filter: Whether to apply Εκαθαριστικός filtering
            verbose: Whether to enable verbose logging
            config_file: Optional path to configuration file
            progress_callback: Optional callback function(percentage, message) for progress updates

        Returns:
            Tuple of (success, log_output, warnings)
        """
        # Count total files for progress tracking
        pdf_files = list(input_dir.glob("*.pdf"))
        total_files = len(pdf_files)

        if total_files == 0:
            if progress_callback:
                progress_callback(0, "No PDF files found")
            return (
                False,
                "No PDF files found in input directory",
                ["No PDF files found"],
            )

        if progress_callback:
            progress_callback(0, f"Found {total_files} PDF files to process")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        log_output = ""
        warnings = []
        all_records = []

        try:
            # Progress: 0-5% - Initialization
            if progress_callback:
                progress_callback(5, "Initializing extractors...")

            # Import extractors here to avoid circular imports
            from dei_extractor.core.filter import FilterEkatharistikos
            from dei_extractor.core.unified_extractor import DEIUnifiedExtractor
            from dei_extractor.utils.config import Config

            # Initialize extractor
            config = Config()
            extractor = DEIUnifiedExtractor(config)

            # Progress: 5-10% - Format detection
            if progress_callback:
                progress_callback(10, "Detecting PDF formats...")

            # Categorize PDFs by format
            categorized_pdfs = extractor.categorize_pdfs([str(f) for f in pdf_files])

            total_to_process = (
                len(categorized_pdfs["v2018"])
                + len(categorized_pdfs["modern"])
                + len(categorized_pdfs.get("format_3", []))
            )
            processed_files = 0

            # Progress: 10-80% - Process v2018 PDFs
            if categorized_pdfs["v2018"]:
                if progress_callback:
                    progress_callback(
                        15, f"Processing {len(categorized_pdfs['v2018'])} v2018 PDFs..."
                    )

                for i, pdf_path in enumerate(categorized_pdfs["v2018"]):
                    if progress_callback:
                        progress = 15 + int(
                            35 * (i + 1) / len(categorized_pdfs["v2018"])
                        )
                        filename = Path(pdf_path).name
                        progress_callback(progress, f"Processing v2018 PDF: {filename}")

                    try:
                        # Process individual file
                        df = extractor.v2018_extractor.process_files([pdf_path])
                        if not df.empty:
                            all_records.extend(df.to_dict("records"))
                            log_output += f"Extracted {len(df)} records from {Path(pdf_path).name}\n"
                    except Exception as e:
                        error_msg = f"Error processing {Path(pdf_path).name}: {e}"
                        warnings.append(error_msg)
                        log_output += error_msg + "\n"

                    processed_files += 1

            # Progress: 45-80% - Process modern PDFs
            if categorized_pdfs["modern"]:
                if progress_callback:
                    progress_callback(
                        50,
                        f"Processing {len(categorized_pdfs['modern'])} modern PDFs...",
                    )

                for i, pdf_path in enumerate(categorized_pdfs["modern"]):
                    if progress_callback:
                        progress = 50 + int(
                            30 * (i + 1) / len(categorized_pdfs["modern"])
                        )
                        filename = Path(pdf_path).name
                        progress_callback(
                            progress, f"Processing modern PDF: {filename}"
                        )

                    try:
                        # Process individual file
                        df = extractor.modern_extractor.process_files([pdf_path])
                        if not df.empty:
                            all_records.extend(df.to_dict("records"))
                            log_output += f"Extracted {len(df)} records from {Path(pdf_path).name}\n"
                    except Exception as e:
                        error_msg = f"Error processing {Path(pdf_path).name}: {e}"
                        warnings.append(error_msg)
                        log_output += error_msg + "\n"

                    processed_files += 1

            # Progress: 75-80% - Process format_3 PDFs
            if categorized_pdfs.get("format_3"):
                if progress_callback:
                    progress_callback(
                        75,
                        f"Processing {len(categorized_pdfs['format_3'])} format_3 PDFs...",
                    )

                for i, pdf_path in enumerate(categorized_pdfs["format_3"]):
                    if progress_callback:
                        progress = 75 + int(
                            5 * (i + 1) / len(categorized_pdfs["format_3"])
                        )
                        filename = Path(pdf_path).name
                        progress_callback(
                            progress, f"Processing format_3 PDF: {filename}"
                        )

                    try:
                        # Process individual file using unified extractor
                        records = extractor.process_format_3_files([pdf_path])
                        if records:
                            all_records.extend(records)
                            log_output += f"Extracted {len(records)} records from {Path(pdf_path).name}\n"
                    except Exception as e:
                        error_msg = f"Error processing {Path(pdf_path).name}: {e}"
                        warnings.append(error_msg)
                        log_output += error_msg + "\n"

                    processed_files += 1

            # Progress: 80-85% - Combine results
            if progress_callback:
                progress_callback(80, "Combining extracted data...")

            # Create combined DataFrame
            import pandas as pd

            if all_records:
                df = pd.DataFrame(all_records)

                # Sort by ΑρΠαροχής if available
                if "ΑρΠαροχής" in df.columns:
                    df = df.sort_values(by=["ΑρΠαροχής"])
                    log_output += f"Sorted {len(df)} combined records by ΑρΠαροχής\n"
            else:
                df = pd.DataFrame()

            # Progress: 85-90% - Write outputs
            if progress_callback:
                progress_callback(85, "Writing output files...")

            # Write outputs
            if not df.empty:
                extractor.write_outputs(df, str(output_dir))
                log_output += f"Written {len(df)} records to output files\n"
            else:
                log_output += "No records extracted\n"

            # Progress: 90-95% - Apply filtering if requested
            if apply_filter and not df.empty:
                if progress_callback:
                    progress_callback(90, "Applying Εκαθαριστικός filtering...")

                try:
                    filter_processor = FilterEkatharistikos()
                    filtered_df = filter_processor.process_files(
                        [str(output_dir / "ολα.csv")]
                    )

                    if not filtered_df.empty:
                        filter_processor.write_outputs(
                            filtered_df,
                            str(output_dir / "filtered.csv"),
                            str(output_dir / "filtered.xlsx"),
                        )
                        log_output += f"Filtered to {len(filtered_df)} records\n"
                    else:
                        log_output += "No records found after filtering\n"
                        warnings.append("No records found after filtering")
                except Exception as e:
                    error_msg = f"Error during filtering: {e}"
                    warnings.append(error_msg)
                    log_output += error_msg + "\n"

            # Progress: 95-100% - Finalization
            if progress_callback:
                progress_callback(95, "Finalizing processing...")

            # Log summary
            log_output += f"\n=== PROCESSING SUMMARY ===\n"
            log_output += f"Total files processed: {processed_files}\n"
            log_output += f"v2018 files: {len(categorized_pdfs['v2018'])}\n"
            log_output += f"Modern files: {len(categorized_pdfs['modern'])}\n"
            log_output += f"Unknown format: {len(categorized_pdfs['unknown'])}\n"
            log_output += f"Total records extracted: {len(df)}\n"

            if progress_callback:
                progress_callback(100, "Processing completed successfully")

            return True, log_output, warnings

        except Exception as e:
            error_msg = f"Error during processing: {e}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(100, error_msg)
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
