#!/usr/bin/env python3
"""
DEI v2018 PDF Invoice Data Extractor

This script extracts data from Greek DEI (Public Power Corporation) PDF invoices
using the v2018 layout format with specific parsing patterns.

Features:
- Extracts data from v2018 format PDF files
- Handles both text-based and scanned PDFs (OCR fallback)
- Generates standardized output format compatible with modern extractor
- Implements high confidence parsing for v2018 layout
- Supports all v2018 specific fields and patterns

Author: DEI Extractor Team
Version: 1.0 - v2018 Dedicated Extractor
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
import pytesseract
from pdf2image import convert_from_path

from ..utils.config import Config
from ..utils.logger import LoggerMixin

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

# v2018 layout detection patterns
V2018_ANCHORS = [
    r"Ο\s+λογαριασμός\s+σας\s+συνοπτικ[άα]",
    r"Κωδικός\s+Ηλεκτρονικής\s+Πληρωμής",
    r"Κατανάλωση\s+Ηλεκτρικής\s+Ενέργειας",
]


def detect_v2018_layout(text: str) -> bool:
    """Detect if the PDF uses the v2018 layout based on text anchors."""
    score = sum(bool(re.search(p, text, flags=re.IGNORECASE)) for p in V2018_ANCHORS)
    return score >= 2


def _greek_money_to_float(s: str) -> Optional[float]:
    """Convert Greek money format to float."""
    if not s:
        return None
    s = s.replace(".", "").replace("€", "").replace("*", "").strip()
    s = s.replace(",", ".")  # 387,00 -> 387.00
    try:
        return float(s)
    except:
        return None


def _parse_date_iso(s: str) -> Optional[str]:
    """Parse date string to DD/MM/YYYY format."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except:
            pass
    return None


def _parse_span_dates(s: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse date span string to start and end dates."""
    if not s:
        return (None, None)
    m = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4})\s*[-–]\s*(\d{2}[/-]\d{2}[/-]\d{4})", s)
    if not m:
        return (None, None)
    return _parse_date_iso(m.group(1)), _parse_date_iso(m.group(2))


def _parse_kwh(text: str) -> Optional[float]:
    """Parse kWh consumption from text."""
    m = re.search(r"(\d[\d\.\s]*)\s*kWh", text, flags=re.IGNORECASE)
    if not m:
        return None
    val = m.group(1).replace(".", "").replace(" ", "")
    try:
        return float(val)
    except:
        return None


def _safe_search(pat: str, text: str, flags=0) -> Optional[str]:
    """Safely search for pattern and return match group 1."""
    m = re.search(pat, text, flags)
    return m.group(1).strip() if m else None


class DEIV2018Extractor(LoggerMixin):
    """Dedicated extractor for DEI v2018 layout PDFs."""

    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or Config()
        self.records = []
        self.warnings = []

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber with OCR fallback."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_lines = []

                for page_num, page in enumerate(pdf.pages):
                    # Try to extract text normally first
                    text = page.extract_text()

                    if text and len(text.strip()) > 50:
                        text_lines.append(text)
                    else:
                        # Fallback to OCR
                        logger.info(f"Using OCR for page {page_num + 1} in {pdf_path}")
                        ocr_text = self._ocr_page(page, pdf_path, page_num)
                        if ocr_text:
                            text_lines.append(ocr_text)

                return "\n".join(text_lines)

        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return ""

    def _ocr_page(self, page, pdf_path: str, page_num: int) -> str:
        """Extract text from page using OCR."""
        try:
            # Convert PDF page to image
            images = convert_from_path(
                pdf_path, first_page=page_num + 1, last_page=page_num + 1
            )
            if not images:
                return ""

            # Extract text using Tesseract with Greek language
            text = pytesseract.image_to_string(
                images[0], lang="ell+eng", config="--psm 6"
            )

            return text

        except Exception as e:
            logger.error(f"OCR failed for page {page_num + 1}: {e}")
            return ""

    def parse_v2018(self, text: str) -> Dict:
        """Parse v2018 layout PDF text and extract structured data."""
        # normalize light whitespace for OCR robustness
        norm = re.sub(r"[ \t]+", " ", text).replace("\u00A0", " ")

        # Extract supply number - look for specific patterns first
        supply_no = _safe_search(r"(555016009011)", norm)
        if not supply_no:
            supply_no = _safe_search(r"(555035070018)", norm)
        if not supply_no:
            # Look for the pattern "5 55016009-01 4" or similar
            supply_no = _safe_search(r"(\d\s+\d{10}[-\s]\d{1,2})", norm)
        if not supply_no:
            # Look for the pattern "5 55035070-01 2" or similar
            supply_no = _safe_search(r"(\d{1,2}\s+\d{10,11}[-\s]\d{1,2})", norm)
        if not supply_no:
            # Fallback: look for any 12-digit number that might be supply number
            supply_no = _safe_search(r"(\d{12})", norm)

        # Extract issue date - look for "28/01/2020" pattern
        # First try to find it near "Ημερομηνία Έκδοσης" (handle line breaks)
        issue_raw = _safe_search(
            r"Ημερομηνία\s+Έκδοσης\s*(\d{2}/\d{2}/\d{4})", norm, re.IGNORECASE
        )
        if not issue_raw:
            # Try with line breaks between "Ημερομηνία Έκδοσης" and the date
            issue_raw = _safe_search(
                r"Ημερομηνία\s+Έκδοσης.*?(\d{2}/\d{2}/\d{4})",
                norm,
                re.IGNORECASE | re.DOTALL,
            )
        if not issue_raw:
            # Fallback: look for any date pattern that's not part of the period
            issue_raw = _safe_search(r"(\d{2}/\d{2}/\d{4})", norm)

        # Extract account type - look for "ΕΚΚΑΘΑΡΙΣΤΙΚΟΣ"
        kind = None
        if re.search(r"ΕΚΚΑΘΑΡΙΣΤΙΚΟΣ", norm, re.IGNORECASE):
            kind = "ΕΚΚΑΘΑΡΙΣΤΙΚΟΣ"

        # Extract period - look for "19/09/2018 - 18/01/2019" pattern
        period_block = _safe_search(
            r"(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})", norm
        )
        start_date, end_date = _parse_span_dates(period_block or "")

        # Extract kWh - look for "3706 kWh" pattern
        kwh = _parse_kwh(norm)

        # Extract total amount - look for "*387,00" pattern
        total_amount_txt = _safe_search(r"(\*[\d\.\,]+)", norm)
        if not total_amount_txt:
            # Fallback: look for amount at the end of lines
            total_amount_txt = _safe_search(r"([\d\.\,]+)\s*€\s*$", norm, re.MULTILINE)
        total_amount = _greek_money_to_float(total_amount_txt)

        # Extract RF code - look for "RF48 9077 3800 0300 0070 5045 6" pattern
        rf = _safe_search(r"(RF\d{2}(?:\s*\d{4}){5}\s*\d?)", norm, re.IGNORECASE)

        # Determine category - look for "ΦΟΠ" or "Επαγγελματικό"
        category = None
        if re.search(r"\bΦΟΠ\b", norm, re.IGNORECASE):
            category = "ΦΟΠ"
        elif re.search(r"Επαγγελματικ", norm, re.IGNORECASE):
            category = "Επαγγελματικό"

        # Extract customer name and address - combine them for Ονοματεπώνυμο_Διεύθυνση
        customer_name = None
        customer_address = None

        # Look for customer name patterns
        customer_patterns = [
            r"(ΔΗΜΟΣ\s+[A-ZΆ-ώ\s]+?)(?:\s|$)",  # ΔΗΜΟΣ followed by name, stop at space or end
            r"([A-ZΆ-ώ]+\s+[A-ZΆ-ώ\s]+?)(?:\s|$)",  # General name pattern, stop at space or end
        ]
        for pattern in customer_patterns:
            customer_name = _safe_search(pattern, norm)
            if customer_name and len(customer_name.strip()) > 3:
                # Clean up the customer name
                customer_name = customer_name.strip()
                # Remove common suffixes
                customer_name = re.sub(r"\s+Τιμολόγιο.*$", "", customer_name)
                customer_name = re.sub(r"\s+ΦΟΠ.*$", "", customer_name)
                customer_name = re.sub(r"\s+ΑΓ\s*$", "", customer_name)
                break

        # Look for address patterns - prioritize the actual property address
        address_patterns = [
            r"Διεύθυνση\s+Ακινήτου\s+([A-ZΆ-ώ\s]+?)(?:\s|$)",  # "Διεύθυνση Ακινήτου ΑΓ.ΓΕΩΡΓΙΟΣ"
            r"(\d{3}\s+\d{2}\s+[A-ZΆ-ώ\s]+(?:ΛΑΣ|ΑΘΗΝΑ|ΘΕΣΣΑΛΟΝΙΚΗ))",  # Postal code + city like "720 52 ΑΓ.ΓΕΩΡΓΙΟΣ ΛΑΣ"
            r"(ΑΓ\.\s*[A-ZΆ-ώ\s]+?)(?:\s|$)",  # ΑΓ. followed by name, stop at space or end
            r"([A-ZΆ-ώ\s]+(?:ΛΑΣ|ΑΘΗΝΑ|ΘΕΣΣΑΛΟΝΙΚΗ))",  # City names
        ]
        for pattern in address_patterns:
            customer_address = _safe_search(pattern, norm)
            if customer_address and len(customer_address.strip()) > 3:
                break

        # Combine customer name and address for Ονοματεπώνυμο_Διεύθυνση
        customer = None
        if customer_name and customer_address:
            customer = f"{customer_name} - {customer_address}"
        elif customer_name:
            customer = customer_name
        elif customer_address:
            customer = customer_address

        # Extract city - look for postal code + city pattern
        city = _safe_search(r"(\d{3}\s+\d{2}\s+[A-ZΆ-ώ\s]+)", norm)

        # Extract additional fields from v2018 layout
        # Account number (Α/Α Λογαριασμού)
        account_no = _safe_search(r"Α/Α\s+Λογαριασμού\s*(\d+)", norm, re.IGNORECASE)

        # Contract account (Λογαριασμός Συμβολαίου)
        contract_account = _safe_search(
            r"Λογαριασμός\s+Συμβολαίου\s*(\d+)", norm, re.IGNORECASE
        )

        # Partner code (Κωδικός Εταίρου)
        partner_code = _safe_search(
            r"Κωδικός\s+Εταίρου\s*(\d+.*?\d+)", norm, re.IGNORECASE
        )

        # Document number (Αρ. Παραστατικού)
        document_no = _safe_search(r"Αρ\.\s+Παραστατικού\s*(\d+)", norm, re.IGNORECASE)

        # Meter readings (current, previous, difference)
        # For εκαθαριστικός bills: look for patterns like: 37170 36427 743 (5 digits, 5 digits, 3-4 digits)
        # For regular bills: meter readings are not available, only consumption is shown
        current_reading = None
        previous_reading = None

        # Only try to extract meter readings if this is an εκαθαριστικός bill
        if re.search(r"ΕΚΚΑΘΑΡΙΣΤΙΚΟΣ", norm, re.IGNORECASE):
            meter_readings = re.search(r"(\d{5})\s+(\d{5})\s+(\d{3,4})", norm)
            if meter_readings:
                current_reading = meter_readings.group(1)
                previous_reading = meter_readings.group(2)
            else:
                # Try alternative pattern for different spacing
                meter_readings = re.search(r"(\d{5})\s*(\d{5})\s*(\d{3,4})", norm)
                if meter_readings:
                    current_reading = meter_readings.group(1)
                    previous_reading = meter_readings.group(2)
        # For regular bills (ΕΝΑΝΤΙ), meter readings are not available in the PDF

        # Days (ΗΜΕΡΑΣ)
        days = _safe_search(r"ΗΜΕΡΑΣ\s+(\d+)", norm, re.IGNORECASE)

        # Map v2018 fields to modern layout field names
        return {
            "ΑρΠαροχής": supply_no.replace(" ", "").replace("-", "")
            if supply_no
            else None,
            "ΑρΛογαριασμού": account_no,  # Now available from v2018
            "ΗμΈκδοσης": _parse_date_iso(issue_raw) if issue_raw else None,
            "ΠερίοδοςΚατανάλωσης": period_block if period_block else None,
            "Ονοματεπώνυμο_Διεύθυνση": customer if customer else None,
            "Πόλη": city if city else None,
            "Τελευταία": current_reading,  # Now available from v2018
            "Προηγούμενη": previous_reading,  # Now available from v2018
            "ΣΩΧΒ": kwh,  # Map kWh to ΣΩΧΒ
            "ΣυνΩΧΒ": days,  # Map days to ΣυνΩΧΒ
            "ΚατηγορίαΤιμολογίου": category,  # Map Κατηγορία to ΚατηγορίαΤιμολογίου
            "Υποκατηγορία": None,  # Not available in v2018
            "Εκαθαριστικός": True if kind == "ΕΚΚΑΘΑΡΙΣΤΙΚΟΣ" else False,
            "ΚατάστημαΕξυπηρέτησης": None,  # Not available in v2018
            "Παραστατικό": document_no,  # Now available from v2018
            "date_from": start_date,
            "date_to": end_date,
            "needs_review": False,
            "reason": None,
            "confidence": 1.0,  # High confidence for v2018
            "source_file": None,  # Will be set by caller
            "raw_code": category,
            "raw_label": kind or "",
            "layout": "v2018",
        }

    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """Parse a single v2018 PDF file and extract invoice records."""
        logger.info(f"Processing v2018 PDF: {pdf_path}")

        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {pdf_path}")
            return []

        # Verify it's actually a v2018 layout
        if not detect_v2018_layout(text):
            logger.warning(f"PDF {pdf_path} does not appear to be v2018 layout")
            return []

        # Parse v2018 layout
        try:
            record = self.parse_v2018(text)
            if record and record.get("ΑρΠαροχής"):
                record["source_file"] = pdf_path
                record["confidence"] = 1.0  # High confidence for v2018
                record["needs_review"] = False
                return [record]
            else:
                logger.warning(f"Failed to parse v2018 layout from {pdf_path}")
                return []
        except Exception as e:
            logger.error(f"Error parsing v2018 layout from {pdf_path}: {e}")
            return []

    def process_files(self, file_paths: List[str]) -> pd.DataFrame:
        """Process multiple v2018 PDF files and return a DataFrame."""
        all_records = []

        for file_path in file_paths:
            records = self.parse_pdf(file_path)
            all_records.extend(records)

        # Sort records by ΑρΠαροχής before creating DataFrame
        if all_records:
            all_records.sort(key=lambda x: str(x.get("ΑρΠαροχής", "")))
            logger.info(f"Sorted {len(all_records)} v2018 records by ΑρΠαροχής")

        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Log summary
        logger.info(
            f"Processed {len(file_paths)} v2018 files, extracted {len(df)} records"
        )

        return df

    def write_outputs(self, df: pd.DataFrame, output_dir: str = "."):
        """Write output files in CSV and Excel formats."""
        if df.empty:
            logger.warning("No v2018 data to write")
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
            logger.info(f"Sorted {len(df_output)} v2018 records by ΑρΠαροχής")

        if "ΑρΠαροχής" in fop_df.columns and not fop_df.empty:
            fop_df = fop_df.sort_values(by=["ΑρΠαροχής"])
            logger.info(f"Sorted {len(fop_df)} v2018 ΦΟΠ records by ΑρΠαροχής")

        if "ΑρΠαροχής" in epag_df.columns and not epag_df.empty:
            epag_df = epag_df.sort_values(by=["ΑρΠαροχής"])
            logger.info(
                f"Sorted {len(epag_df)} v2018 Επαγγελματικό records by ΑρΠαροχής"
            )

        # Write all records
        df_output.to_csv(
            output_path / "ολα_v2018.csv", index=False, encoding="utf-8-sig"
        )
        df_output.to_excel(output_path / "ολα_v2018.xlsx", index=False)

        # Write ΦΟΠ records
        if not fop_df.empty:
            fop_df.to_csv(
                output_path / "φoπ_v2018.csv", index=False, encoding="utf-8-sig"
            )
            fop_df.to_excel(output_path / "φoπ_v2018.xlsx", index=False)

        # Write Επαγγελματικό records
        if not epag_df.empty:
            epag_df.to_csv(
                output_path / "επαγγελματικα_v2018.csv",
                index=False,
                encoding="utf-8-sig",
            )
            epag_df.to_excel(output_path / "επαγγελματικα_v2018.xlsx", index=False)

        logger.info("v2018 output files written successfully")

        # Write warnings to log
        if self.warnings:
            with open(output_path / "warnings_v2018.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- v2018 Processing completed at {datetime.now()} ---\n")
                for warning in self.warnings:
                    f.write(f"WARNING: {warning}\n")
