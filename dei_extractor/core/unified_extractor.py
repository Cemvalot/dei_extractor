#!/usr/bin/env python3
"""
DEI Unified PDF Invoice Data Extractor

This script provides a unified interface for extracting data from Greek DEI (Public Power Corporation)
PDF invoices by intelligently detecting the format and routing to the appropriate dedicated extractor.

Features:
- Automatic format detection (v2018 vs modern)
- Routes to dedicated extractors for optimal results
- Combines results from both formats
- Maintains consistent output format
- Supports both individual and batch processing

Author: DEI Extractor Team
Version: 1.0 - Unified Extractor
"""

import logging
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pdfplumber

from ..utils.config import Config
from ..utils.logger import LoggerMixin
from .extractor_modern import DEIModernExtractor
from .extractor_v2018 import DEIV2018Extractor, detect_v2018_layout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("warnings.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")


class DEIUnifiedExtractor(LoggerMixin):
    """Unified extractor that routes to appropriate dedicated extractors."""

    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or Config()
        self.v2018_extractor = DEIV2018Extractor(config)
        self.modern_extractor = DEIModernExtractor(config)
        self.format_stats = {"v2018": 0, "modern": 0, "unknown": 0}

    def detect_pdf_format(self, pdf_path: str) -> str:
        """Detect the format of a PDF file."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_lines = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_lines.extend(text.split("\n"))

                # Join text for format detection
                full_text = "\n".join(text_lines)

                # Check for v2018 format
                if detect_v2018_layout(full_text):
                    logger.info(f"Detected v2018 format for {pdf_path}")
                    return "v2018"
                else:
                    logger.info(f"Detected modern format for {pdf_path}")
                    return "modern"

        except Exception as e:
            logger.error(f"Error detecting format for {pdf_path}: {e}")
            return "unknown"

    def categorize_pdfs(self, pdf_paths: List[str]) -> Dict[str, List[str]]:
        """Categorize PDF files by their format."""
        categorized = {"v2018": [], "modern": [], "unknown": []}

        for pdf_path in pdf_paths:
            format_type = self.detect_pdf_format(pdf_path)
            categorized[format_type].append(pdf_path)
            self.format_stats[format_type] += 1

        logger.info(f"PDF categorization complete:")
        logger.info(f"  v2018: {len(categorized['v2018'])} files")
        logger.info(f"  modern: {len(categorized['modern'])} files")
        logger.info(f"  unknown: {len(categorized['unknown'])} files")

        return categorized

    def process_files(self, file_paths: List[str]) -> pd.DataFrame:
        """Process multiple PDF files using appropriate extractors."""
        if not file_paths:
            logger.warning("No files provided for processing")
            return pd.DataFrame()

        # Categorize PDFs by format
        categorized_pdfs = self.categorize_pdfs(file_paths)

        all_records = []

        # Process v2018 PDFs
        if categorized_pdfs["v2018"]:
            logger.info(f"Processing {len(categorized_pdfs['v2018'])} v2018 PDFs...")
            v2018_df = self.v2018_extractor.process_files(categorized_pdfs["v2018"])
            if not v2018_df.empty:
                all_records.extend(v2018_df.to_dict("records"))
                logger.info(f"Extracted {len(v2018_df)} v2018 records")

        # Process modern PDFs
        if categorized_pdfs["modern"]:
            logger.info(f"Processing {len(categorized_pdfs['modern'])} modern PDFs...")
            modern_df = self.modern_extractor.process_files(categorized_pdfs["modern"])
            if not modern_df.empty:
                all_records.extend(modern_df.to_dict("records"))
                logger.info(f"Extracted {len(modern_df)} modern records")

        # Handle unknown format PDFs
        if categorized_pdfs["unknown"]:
            logger.warning(
                f"Skipping {len(categorized_pdfs['unknown'])} PDFs with unknown format"
            )
            for pdf_path in categorized_pdfs["unknown"]:
                logger.warning(f"  - {pdf_path}")

        # Create combined DataFrame
        if all_records:
            df = pd.DataFrame(all_records)
            # Sort by ΑρΠαροχής
            if "ΑρΠαροχής" in df.columns:
                df = df.sort_values(by=["ΑρΠαροχής"])
                logger.info(f"Sorted {len(df)} combined records by ΑρΠαροχής")
        else:
            df = pd.DataFrame()

        # Log summary
        logger.info(f"\n=== UNIFIED PROCESSING SUMMARY ===")
        logger.info(f"Total files processed: {len(file_paths)}")
        logger.info(f"v2018 files: {self.format_stats['v2018']}")
        logger.info(f"Modern files: {self.format_stats['modern']}")
        logger.info(f"Unknown format: {self.format_stats['unknown']}")
        logger.info(f"Total records extracted: {len(df)}")

        if not df.empty:
            layout_counts = df["layout"].value_counts()
            logger.info(f"Records by layout:")
            for layout, count in layout_counts.items():
                logger.info(f"  {layout}: {count}")

        return df

    def write_outputs(self, df: pd.DataFrame, output_dir: str = "."):
        """Write output files in CSV and Excel formats."""
        if df.empty:
            logger.warning("No data to write")
            return

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Ensure all text columns are strings
        text_columns = [
            "ΑρΠαροχής",
            "ΑρΛογαριασμού",
            "Ονοματεπώνυμο_Διεύθυνση",
            "Πόλη",
            "ΚατηγορίαΤιμολογίου",
            "Υποκατηγορία",
            "reason",
            "source_file",
            "ΚατάστημαΕξυπηρέτησης",
            "Παραστατικό",
            "date_from",
            "date_to",
            "layout",
        ]
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # Ensure IDs are strings to prevent scientific notation
        if "ΑρΠαροχής" in df.columns:
            df["ΑρΠαροχής"] = df["ΑρΠαροχής"].astype(str)
        if "ΑρΛογαριασμού" in df.columns:
            df["ΑρΛογαριασμού"] = df["ΑρΛογαριασμού"].astype(str)

        # Drop internal/processing columns before writing output files
        drop_cols = [
            "ΚατάστημαΕξυπηρέτησης",
            "Παραστατικό",
            "needs_review",
            "reason",
            "confidence",
            "date_from",
            "date_to",
            "layout",  # Internal field for layout detection
        ]

        # Create copies for output files
        df_output = df.copy()

        # Check if ΚατηγορίαΤιμολογίου column exists before filtering
        if "ΚατηγορίαΤιμολογίου" in df.columns:
            fop_df = df[df["ΚατηγορίαΤιμολογίου"] == "ΦΟΠ"].copy()
            epag_df = df[df["ΚατηγορίαΤιμολογίου"] == "Επαγγελματικό"].copy()
        else:
            # If column doesn't exist, create empty DataFrames
            fop_df = pd.DataFrame()
            epag_df = pd.DataFrame()

        # Drop columns from all output DataFrames
        for df_out in [df_output, fop_df, epag_df]:
            for col in drop_cols:
                if col in df_out.columns:
                    df_out.drop(columns=col, inplace=True)

        # Sort and group by ΑρΠαροχής for all DataFrames
        if "ΑρΠαροχής" in df_output.columns:
            df_output = df_output.sort_values(by=["ΑρΠαροχής"])
            logger.info(f"Sorted {len(df_output)} combined records by ΑρΠαροχής")

        if "ΑρΠαροχής" in fop_df.columns and not fop_df.empty:
            fop_df = fop_df.sort_values(by=["ΑρΠαροχής"])
            logger.info(f"Sorted {len(fop_df)} ΦΟΠ records by ΑρΠαροχής")

        if "ΑρΠαροχής" in epag_df.columns and not epag_df.empty:
            epag_df = epag_df.sort_values(by=["ΑρΠαροχής"])
            logger.info(f"Sorted {len(epag_df)} Επαγγελματικό records by ΑρΠαροχής")

        # Write all records
        df_output.to_csv(output_path / "ολα.csv", index=False, encoding="utf-8-sig")
        df_output.to_excel(output_path / "ολα.xlsx", index=False)

        # Write ΦΟΠ records
        if not fop_df.empty:
            fop_df.to_csv(output_path / "φoπ.csv", index=False, encoding="utf-8-sig")
            fop_df.to_excel(output_path / "φoπ.xlsx", index=False)

        # Write Επαγγελματικό records
        if not epag_df.empty:
            epag_df.to_csv(
                output_path / "επαγγελματικα.csv", index=False, encoding="utf-8-sig"
            )
            epag_df.to_excel(output_path / "επαγγελματικα.xlsx", index=False)

        logger.info("Unified output files written successfully")

        # Write format statistics
        with open(output_path / "format_stats.txt", "w", encoding="utf-8") as f:
            f.write(f"DEI PDF Format Processing Statistics\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            f.write(f"Total files processed: {sum(self.format_stats.values())}\n")
            f.write(f"v2018 format: {self.format_stats['v2018']}\n")
            f.write(f"Modern format: {self.format_stats['modern']}\n")
            f.write(f"Unknown format: {self.format_stats['unknown']}\n\n")
            f.write(f"Total records extracted: {len(df)}\n")
            if not df.empty and "layout" in df.columns:
                layout_counts = df["layout"].value_counts()
                f.write(f"Records by layout:\n")
                for layout, count in layout_counts.items():
                    f.write(f"  {layout}: {count}\n")

        # Write warnings to log
        all_warnings = []
        if hasattr(self.v2018_extractor, "warnings"):
            all_warnings.extend([f"v2018: {w}" for w in self.v2018_extractor.warnings])
        if hasattr(self.modern_extractor, "warnings"):
            all_warnings.extend(
                [f"modern: {w}" for w in self.modern_extractor.warnings]
            )

        if all_warnings:
            with open(output_path / "warnings_unified.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- Unified Processing completed at {datetime.now()} ---\n")
                for warning in all_warnings:
                    f.write(f"WARNING: {warning}\n")

    def get_format_statistics(self) -> Dict[str, int]:
        """Get statistics about processed formats."""
        return self.format_stats.copy()

    def reset_statistics(self):
        """Reset format statistics."""
        self.format_stats = {"v2018": 0, "modern": 0, "unknown": 0}
