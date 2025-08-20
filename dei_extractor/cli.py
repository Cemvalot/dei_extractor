#!/usr/bin/env python3
"""
Command-line interface for DEI Extractor.

This module provides a command-line interface for extracting DEI data from PDF files
and filtering the results.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

from .core.extractor import DEIExtractorEnhanced
from .core.filter import FilterEkatharistikos
from .utils.config import Config, load_config
from .utils.logger import setup_logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract DEI data from PDF files and filter results"
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        help="Directory containing PDF files to process",
    )
    parser.add_argument(
        "--input",
        help="Directory containing PDF files to process (alternative to positional argument)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for extracted data (default: output)",
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        help="Apply Εκαθαριστικός filtering to extracted data",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def setup_environment(args: argparse.Namespace) -> Tuple[Path, Dict[str, Any]]:
    """Set up the processing environment."""
    # Set up logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level=log_level)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load configuration
    config = load_config(args.config) if args.config else {}

    return output_dir, config


def process_pdfs(input_dir: str, output_dir: Path, config: Dict[str, Any]) -> bool:
    """Process PDF files and extract DEI data."""
    # Convert config dict to Config object if needed
    config_obj = Config() if not config else Config(**config)
    extractor = DEIExtractorEnhanced(config_obj)
    input_path = Path(input_dir)

    if not input_path.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        return False

    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        logging.warning(f"No PDF files found in {input_dir}")
        return False

    logging.info(f"Found {len(pdf_files)} PDF files to process")

    # Use the extractor's process_files method
    try:
        df = extractor.process_files([str(pdf_file) for pdf_file in pdf_files])
        if not df.empty:
            # Write outputs to the specified output directory
            extractor.write_outputs(df, str(output_dir))
            logging.info("PDF processing completed successfully")
            return True
        else:
            logging.error("PDF processing failed - no data extracted")
            return False
    except Exception as e:
        logging.error(f"Error during PDF processing: {e}")
        return False


def apply_filtering(output_dir: Path) -> bool:
    """Apply Εκαθαριστικός filtering to extracted data."""
    filter_processor = FilterEkatharistikos()
    csv_files = list(output_dir.glob("*.csv"))

    if not csv_files:
        logging.warning("No CSV files found for filtering")
        return False

    logging.info(f"Applying filtering to {len(csv_files)} CSV files")

    try:
        # Use the filter's process_files method
        df = filter_processor.process_files([str(csv_file) for csv_file in csv_files])
        if not df.empty:
            # Write filtered output to the same directory
            filter_processor.write_outputs(
                df, str(output_dir / "filtered.csv"), str(output_dir / "filtered.xlsx")
            )
            logging.info("Filtering completed successfully")
            return True
        else:
            logging.warning("No records found after filtering")
            return False
    except Exception as e:
        logging.error(f"Error during filtering: {e}")
        return False


def main() -> None:
    """Main function to orchestrate the extraction and filtering process."""
    args = parse_arguments()

    # Determine input directory
    input_dir = args.input or args.input_dir
    if not input_dir:
        logging.error(
            "Input directory is required. Use --input or provide as positional argument."
        )
        sys.exit(1)

    try:
        # Set up environment
        output_dir, config = setup_environment(args)

        # Process PDFs
        success = process_pdfs(input_dir, output_dir, config)
        if not success:
            logging.error("PDF processing failed")
            sys.exit(1)

        # Apply filtering if requested
        if args.filter:
            filter_success = apply_filtering(output_dir)
            if not filter_success:
                logging.warning("Filtering failed, but extraction completed")

        logging.info("Processing completed successfully")

    except Exception as e:
        logging.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
