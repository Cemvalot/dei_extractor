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
from ..utils.id_helpers import compute_arparchi_group_id
from ..utils.logger import LoggerMixin
from ..utils.validators import parse_ddmmyyyy
from .exporters.xlsx_exporter import to_format_3_xlsx
from .extractor_modern import DEIModernExtractor
from .extractor_tabular import DEITabularExtractor, detect_tabular_format
from .extractor_v2018 import DEIV2018Extractor, detect_v2018_layout
from .parsers.format_3 import detect as detect_format_3
from .parsers.format_3 import parse as parse_format_3

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
        self.tabular_extractor = DEITabularExtractor(config)
        self.format_stats = {
            "v2018": 0,
            "modern": 0,
            "format_3": 0,
            "tabular": 0,
            "unknown": 0,
        }

    def detect_pdf_format(self, pdf_path: str) -> str:
        """Detect the format of a PDF file."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_lines = []
                ocr_needed = False

                for page in pdf.pages[:2]:  # Check first 2 pages for detection
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        text_lines.extend(text.split("\n"))
                    else:
                        ocr_needed = True
                        break

                # If no text extracted, try OCR for detection
                if ocr_needed or not text_lines:
                    logger.info(f"Using OCR for format detection: {pdf_path}")
                    try:
                        import pytesseract
                        from pdf2image import convert_from_path

                        images = convert_from_path(pdf_path, first_page=1, last_page=1)
                        if images:
                            ocr_text = pytesseract.image_to_string(
                                images[0], lang="ell+eng", config="--psm 6"
                            )
                            text_lines = ocr_text.split("\n")
                    except Exception as e:
                        logger.warning(f"OCR detection failed: {e}")

                # Join text for format detection
                full_text = "\n".join(text_lines)

                # Check for format_3 first
                if detect_format_3(full_text):
                    logger.info(f"Detected format_3 for {pdf_path}")
                    return "format_3"
                # Check for tabular format (bulk invoices)
                elif detect_tabular_format(full_text):
                    logger.info(f"Detected tabular format for {pdf_path}")
                    return "tabular"
                # Check for v2018 format
                elif detect_v2018_layout(full_text):
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
        categorized = {
            "v2018": [],
            "modern": [],
            "format_3": [],
            "tabular": [],
            "unknown": [],
        }

        for pdf_path in pdf_paths:
            format_type = self.detect_pdf_format(pdf_path)
            categorized[format_type].append(pdf_path)
            self.format_stats[format_type] += 1

        logger.info(f"PDF categorization complete:")
        logger.info(f"  v2018: {len(categorized['v2018'])} files")
        logger.info(f"  modern: {len(categorized['modern'])} files")
        logger.info(f"  format_3: {len(categorized['format_3'])} files")
        logger.info(f"  tabular: {len(categorized['tabular'])} files")
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

        # Process format_3 PDFs
        format_3_payloads = []
        format_3_files = []
        if categorized_pdfs["format_3"]:
            logger.info(
                f"Processing {len(categorized_pdfs['format_3'])} format_3 PDFs..."
            )
            format_3_records = self.process_format_3_files(categorized_pdfs["format_3"])
            if format_3_records:
                all_records.extend(format_3_records)
                logger.info(f"Extracted {len(format_3_records)} format_3 records")

            # Also get raw payloads for format_3 specific export
            format_3_payloads, format_3_files = self.process_format_3_files_raw(
                categorized_pdfs["format_3"]
            )

        # Process tabular PDFs (bulk invoice listings)
        if categorized_pdfs["tabular"]:
            logger.info(
                f"Processing {len(categorized_pdfs['tabular'])} tabular PDFs..."
            )
            tabular_df = self.tabular_extractor.process_files(
                categorized_pdfs["tabular"]
            )
            if not tabular_df.empty:
                all_records.extend(tabular_df.to_dict("records"))
                logger.info(f"Extracted {len(tabular_df)} tabular records")

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
            # Add merge fields and sort
            df = self.add_merge_fields(df)
            logger.info(f"Added merge fields to {len(df)} combined records")
        else:
            df = pd.DataFrame()

        # Log summary
        logger.info(f"\n=== UNIFIED PROCESSING SUMMARY ===")
        logger.info(f"Total files processed: {len(file_paths)}")
        logger.info(f"v2018 files: {self.format_stats['v2018']}")
        logger.info(f"Modern files: {self.format_stats['modern']}")
        logger.info(f"Format_3 files: {self.format_stats['format_3']}")
        logger.info(f"Tabular files: {self.format_stats['tabular']}")
        logger.info(f"Unknown format: {self.format_stats['unknown']}")
        logger.info(f"Total records extracted: {len(df)}")

        if not df.empty:
            layout_counts = df["layout"].value_counts()
            logger.info(f"Records by layout:")
            for layout, count in layout_counts.items():
                logger.info(f"  {layout}: {count}")

        # Store format_3 data for later export
        self.format_3_payloads = format_3_payloads
        self.format_3_files = format_3_files

        return df

    def write_format_3_outputs(
        self,
        format_3_payloads: List[Dict],
        format_3_files: List[str],
        output_dir: str = ".",
    ):
        """
        Write format_3 specific output files with simplified columns.

        Args:
            format_3_payloads: List of format_3 parsed payloads
            format_3_files: List of corresponding source file paths
            output_dir: Output directory path
        """
        if not format_3_payloads:
            logger.warning("No format_3 data to write")
            return

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export format_3 data to simplified XLSX
        format_3_xlsx_path = output_path / "format_3_simplified.xlsx"
        try:
            to_format_3_xlsx(format_3_payloads, format_3_files, str(format_3_xlsx_path))
            logger.info(f"Format_3 simplified XLSX written to: {format_3_xlsx_path}")
        except Exception as e:
            logger.error(f"Failed to write format_3 XLSX: {e}")

    def write_outputs(self, df: pd.DataFrame, output_dir: str = "."):
        """Write output files in CSV and Excel formats."""
        if df.empty:
            logger.warning("No data to write")
            return

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Check if we have only format_3 data
        has_format_3_only = (
            hasattr(self, "format_3_payloads")
            and hasattr(self, "format_3_files")
            and self.format_3_payloads
            and self.format_3_files
            and self.format_stats.get("format_3", 0) > 0
            and self.format_stats.get("v2018", 0) == 0
            and self.format_stats.get("modern", 0) == 0
        )

        if has_format_3_only:
            logger.info("Only format_3 data detected - creating simplified output only")
            # Write only format_3 simplified output
            self.write_format_3_outputs(
                self.format_3_payloads, self.format_3_files, output_dir
            )

            # Write format statistics
            with open(output_path / "format_stats.txt", "w", encoding="utf-8") as f:
                f.write(f"DEI PDF Format Processing Statistics\n")
                f.write(f"Generated: {datetime.now()}\n\n")
                f.write(f"Total files processed: {sum(self.format_stats.values())}\n")
                f.write(f"format_3 files: {self.format_stats['format_3']}\n")
                f.write(f"Total records extracted: {len(self.format_3_payloads)}\n")
                f.write(f"Records by layout:\n")
                f.write(f"  format_3: {len(self.format_3_payloads)}\n")

            logger.info("Format_3 simplified output written successfully")
            return

        # Ensure all text columns are strings
        text_columns = [
            "ΑρΠαροχής",
            "ΑρΠαρχ_Ομάδα",
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
            "ΠερίοδοςΚατανάλωσης_Αρχική",
            "ΠερίοδοςΚατανάλωσης_Τελική",
            "merge_key",
            "ΑρΠαρχ_Αρίθμηση",
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
            "_start_date",  # Internal field for sorting
            "merge_key",  # Internal field for deduplication
            "ΑρΠαρχ_Αρίθμηση",  # Internal field for sequencing
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

        # Write format_3 specific simplified output if available
        if hasattr(self, "format_3_payloads") and hasattr(self, "format_3_files"):
            if self.format_3_payloads and self.format_3_files:
                self.write_format_3_outputs(
                    self.format_3_payloads, self.format_3_files, output_dir
                )

        # Write format statistics
        with open(output_path / "format_stats.txt", "w", encoding="utf-8") as f:
            f.write(f"DEI PDF Format Processing Statistics\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            f.write(f"Total files processed: {sum(self.format_stats.values())}\n")
            f.write(f"v2018 format: {self.format_stats['v2018']}\n")
            f.write(f"Modern format: {self.format_stats['modern']}\n")
            f.write(f"Format_3 format: {self.format_stats['format_3']}\n")
            f.write(f"Tabular format: {self.format_stats['tabular']}\n")
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

    def process_format_3_files(self, pdf_paths: List[str]) -> List[Dict]:
        """Process format_3 PDF files and return structured records."""
        records = []

        for pdf_path in pdf_paths:
            try:
                # Read PDF bytes
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                # Parse using format_3 parser
                payload = parse_format_3(pdf_bytes, pdf_path)

                # Convert to standardized record format
                record = self.convert_format_3_to_standard(payload, pdf_path)
                if record:
                    records.append(record)

            except Exception as e:
                logger.error(f"Error processing format_3 PDF {pdf_path}: {e}")
                continue

        return records

    def process_format_3_files_raw(
        self, pdf_paths: List[str]
    ) -> Tuple[List[Dict], List[str]]:
        """Process format_3 PDF files and return raw payloads and file paths."""
        payloads = []
        processed_files = []

        for pdf_path in pdf_paths:
            try:
                # Read PDF bytes
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                # Parse using format_3 parser
                payload = parse_format_3(pdf_bytes, pdf_path)

                if payload and payload.get("supply_number", {}).get("normalized"):
                    payloads.append(payload)
                    processed_files.append(pdf_path)

            except Exception as e:
                logger.error(f"Error processing format_3 PDF {pdf_path}: {e}")
                continue

        return payloads, processed_files

    def convert_format_3_to_standard(
        self, payload: Dict, source_file: str
    ) -> Optional[Dict]:
        """Convert format_3 payload to standard record format."""
        if not payload or not payload.get("supply_number", {}).get("normalized"):
            return None

        # Map format_3 fields to standard format
        record = {
            "ΑρΠαροχής": payload.get("supply_number", {}).get("normalized"),
            "ΑρΛογαριασμού": payload.get("account_number"),
            "ΗμΈκδοσης": payload.get("issue_date"),
            "ΠερίοδοςΚατανάλωσης": f"{payload.get('period_from', '')}-{payload.get('period_to', '')}",
            "Ονοματεπώνυμο_Διεύθυνση": self._get_name_address(payload),
            "Πόλη": self._get_city(payload),
            "Τελευταία": payload.get("reading_last"),
            "Προηγούμενη": payload.get("reading_prev"),
            "ΣΩΧΒ": payload.get("kwh_night"),
            "ΣυνΩΧΒ": payload.get("kwh_total"),
            "ΚατηγορίαΤιμολογίου": payload.get("tariff_category"),
            "Υποκατηγορία": payload.get("tariff_subcategory"),
            "Εκαθαριστικός": payload.get("is_clearing", False),
            "source_file": source_file.replace("\\", "/") if source_file else None,
            "ΠερίοδοςΚατανάλωσης_Αρχική": payload.get("period_from"),
            "ΠερίοδοςΚατανάλωσης_Τελική": payload.get("period_to"),
            "raw_code": payload.get("account_number")
            or payload.get("supply_number", {}).get("pretty"),
            "raw_label": payload.get("format"),
            "layout": "format_3",
            "needs_review": False,
            "reason": None,
            "confidence": 1.0,
        }

        return record

    def _get_name_address(self, payload: Dict) -> str:
        """Get combined name and address from format_3 payload."""
        name = payload.get("recipient_name", "")
        address = payload.get("recipient_address_line1", "")
        parts = [part for part in [name, address] if part]
        return ", ".join(parts)

    def _get_city(self, payload: Dict) -> str:
        """Get city from format_3 payload."""
        city = payload.get("city")
        if city:
            return city

        postcode_city = payload.get("recipient_postcode_city", "")
        if postcode_city:
            parts = postcode_city.split(" ", 1)
            if len(parts) > 1:
                return parts[1]
        return ""

    def get_format_statistics(self) -> Dict[str, int]:
        """Get statistics about processed formats."""
        return self.format_stats.copy()

    def reset_statistics(self):
        """Reset format statistics."""
        self.format_stats = {
            "v2018": 0,
            "modern": 0,
            "format_3": 0,
            "tabular": 0,
            "unknown": 0,
        }

    def add_merge_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add merge_key and ΑρΠαρχ_Αρίθμηση fields to the DataFrame."""
        # Κανονικοποίηση τύπων
        for col in [
            "ΑρΠαροχής",
            "ΠερίοδοςΚατανάλωσης_Αρχική",
            "ΠερίοδοςΚατανάλωσης_Τελική",
        ]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # merge_key
        if set(
            ["ΑρΠαροχής", "ΠερίοδοςΚατανάλωσης_Αρχική", "ΠερίοδοςΚατανάλωσης_Τελική"]
        ).issubset(df.columns):
            df["merge_key"] = (
                df["ΑρΠαροχής"]
                + "__"
                + df["ΠερίοδοςΚατανάλωσης_Αρχική"]
                + "__"
                + df["ΠερίοδοςΚατανάλωσης_Τελική"]
            )
        else:
            df["merge_key"] = pd.NA

        # Parse dates για σωστή ταξινόμηση
        if "ΠερίοδοςΚατανάλωσης_Αρχική" in df.columns:
            df["_start_date"] = df["ΠερίοδοςΚατανάλωσης_Αρχική"].apply(parse_ddmmyyyy)
        else:
            df["_start_date"] = pd.NaT

        # ΑρΠαρχ_Αρίθμηση: ταξινόμηση ανά ΑρΠαροχής, start_date
        if "ΑρΠαροχής" in df.columns:
            df = df.sort_values(by=["ΑρΠαροχής", "_start_date"], kind="mergesort")
            df["ΑρΠαρχ_Αρίθμηση"] = df.groupby("ΑρΠαροχής").cumcount() + 1

        # ΑρΠαρχ_Ομάδα: dense rank ανά μοναδικό ΑρΠαροχής
        if "ΑρΠαροχής" in df.columns:
            df["ΑρΠαρχ_Ομάδα"] = compute_arparchi_group_id(df["ΑρΠαροχής"])
            # Βάλε τη στήλη αμέσως μετά το ΑρΠαροχής για εργονομία
            cols = list(df.columns)
            i = cols.index("ΑρΠαροχής")
            cols.insert(i + 1, cols.pop(cols.index("ΑρΠαρχ_Ομάδα")))
            df = df[cols]

        return df
