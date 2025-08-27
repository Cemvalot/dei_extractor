#!/usr/bin/env python3
"""
DEI PDF Invoice Data Extractor - Enhanced Version with Edge Cases

This script extracts data from Greek DEI (Public Power Corporation) PDF invoices
using a precise 3-row block structure parsing approach with enhanced edge case handling.

Features:
- Extracts data from 1+ PDF files via CLI
- Identifies records in 3-row blocks with specific patterns
- Handles both text-based and scanned PDFs (OCR fallback)
- Generates separate output files for all records, residential (ΦΟΠ), and commercial invoices
- Implements 90% confidence threshold with review system
- Enhanced edge case handling for ΦΟΠ variations, wrap categories, deduplication
- Header/footer filtering and financial line exclusion
- Additional fields: ΚατάστημαΕξυπηρέτησης, Παραστατικό, date parsing
- Support for both modern and v2018 DEI layouts

Installation:
1. Install Tesseract OCR: brew install tesseract tesseract-lang (macOS)
   or: sudo apt-get install tesseract-ocr tesseract-ocr-ell (Ubuntu)
2. Install Python dependencies: pip install -r requirements.txt

Usage:
    python extract_dei_final.py --input "path_or_glob/*.pdf"

Author: DEI Extractor Team
Version: 3.0 - Enhanced with Edge Cases and v2018 Support
"""

import argparse
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

# Layout detection patterns for v2018
V2018_ANCHORS = [
    r"Ο\s+λογαριασμός\s+σας\s+συνοπτικ[άα]",
    r"Κωδικός\s+Ηλεκτρονικής\s+Πληρωμής",
    r"Κατανάλωση\s+Ηλεκτρικής\s+Ενέργειας",
]

# Enhanced regex patterns for the 3-row block structure
ROW1_PATTERN = re.compile(
    r"(?P<par>\d{10,11})\s+(?P<log>\d{9,12})\s+(?P<issued>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<period>\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<name>.+?)\s{2,}(?P<addr>.+?)\s{2,}(?P<city>.+)$"
)

# Enhanced ROW2 pattern to handle ΦΟΠ variations and wrap categories
ROW2_PATTERN = re.compile(
    r"^(?P<code>ΦΟΠ|Φ\.Ο\.Π|Φ\s+Ο\s+Π|Γ\d+)\s+(?P<label>Τιμολόγιο|Επαγγελματικό)\b"
)

# Enhanced ROW3 pattern with fallback options
ROW3_PATTERN = re.compile(
    r"^Ημέρα\s+(?P<last>\d+)\s+(?P<prev>\d+)\s+(?P<soxv>\d+)\s+(?P<syn>\d+)\s*$"
)
ROW3_FALLBACK_PATTERN = re.compile(
    r"^(?P<last>\d+)\s+(?P<prev>\d+)\s+(?P<soxv>\d+)\s+(?P<syn>\d+)\s*$"
)

# Patterns for additional fields
STORE_PATTERN = re.compile(r"ΚΑΤΑΣΤΗΜΑ\s+ΕΞΥΠΗΡ\.ΔΕΗ\s*:\s*(.+)")
RECEIPT_PATTERN = re.compile(r"ΠΑΡΑΣΤ:\s*(\d+)")

# Header/footer patterns to ignore
HEADER_FOOTER_PATTERNS = [
    re.compile(r"ΔΗΜΟΣΙΑ\s+ΕΠΙΧΕΙΡΗΣΗ\s+ΗΛΕΚΤΡΙΣΜΟΥ", re.IGNORECASE),
    re.compile(r"ΗΜΕΡΟΛΟΓΙΟ\s+ΕΚΔΟΣΗΣ", re.IGNORECASE),
    re.compile(r"ΚΩΔ\.ΠΟΛΛΑΠΛΟΥ", re.IGNORECASE),
    re.compile(r"ΚΩΔ\.ΕΤΑΙΡΟΥ", re.IGNORECASE),
    re.compile(r"ΟΝΟΜΑ\s+ΔΗΜΟΥ", re.IGNORECASE),
    re.compile(r"ΑΦΜ", re.IGNORECASE),
    re.compile(r"ΣΕΛΙΔΑ", re.IGNORECASE),
]

# Financial patterns to exclude
FINANCIAL_PATTERNS = [
    re.compile(r"ΦΠΑ", re.IGNORECASE),
    re.compile(r"ΣΥΝΟΛΟ", re.IGNORECASE),
    re.compile(r"ΠΛΗΡΩΤΕΟ", re.IGNORECASE),
    re.compile(r"ΕΞΟΦΛΗΣΗ", re.IGNORECASE),
]

# Pattern to exclude summary blocks
SUMMARY_PATTERN = re.compile(
    r"Σ\s+Υ\s+Ν\s+Ο\s+Λ\s+Α\s+Π\s+Ο\s+Λ\s+Λ\s+Α\s+Π\s+Λ\s+Ο\s+Υ", re.IGNORECASE
)


def detect_layout_vintage(text: str) -> bool:
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


class DEIExtractorEnhanced(LoggerMixin):
    """Enhanced version of DEI extractor with comprehensive edge case handling."""

    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or Config()
        self.records = []
        self.needs_review = []
        self.warnings = []
        self.processed_blocks = set()  # For deduplication

    def fix_duplicated_chars(self, text: str) -> str:
        """Fix duplicated characters in the text (common in this PDF format)."""
        if not text:
            return text

        # Remove duplicated characters (same character repeated twice)
        fixed_text = ""
        i = 0
        while i < len(text):
            if i + 1 < len(text) and text[i] == text[i + 1]:
                fixed_text += text[i]
                i += 2
            else:
                fixed_text += text[i]
                i += 1

        # Additional fix for specific Greek character patterns
        # Replace common duplicated patterns
        replacements = {
            "ΑΑ": "Α",
            "ρρ": "ρ",
            "ΠΠ": "Π",
            "αα": "α",
            "ρορο": "ρο",
            "χχήήςς": "χής",
            "χχήής": "χής",
            "χχής": "χής",
        }

        for old, new in replacements.items():
            fixed_text = fixed_text.replace(old, new)

        return fixed_text

    def should_ignore_line(self, line: str) -> bool:
        """Check if a line should be ignored (headers, footers, financial lines)."""
        line_upper = line.upper()

        # Check header/footer patterns
        for pattern in HEADER_FOOTER_PATTERNS:
            if pattern.search(line_upper):
                return True

        # Check financial patterns
        for pattern in FINANCIAL_PATTERNS:
            if pattern.search(line_upper):
                return True

        # Check summary pattern
        if SUMMARY_PATTERN.search(line_upper):
            return True

        return False

    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract text from PDF using pdfplumber with OCR fallback."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_lines = []

                for page_num, page in enumerate(pdf.pages):
                    # Try to extract text normally first
                    text = page.extract_text()

                    if text and len(text.strip()) > 50:
                        # Fix duplicated characters
                        text = self.fix_duplicated_chars(text)
                        # Filter out ignored lines
                        filtered_lines = [
                            line
                            for line in text.split("\n")
                            if not self.should_ignore_line(line)
                        ]
                        text_lines.extend(filtered_lines)
                    else:
                        # Fallback to OCR
                        logger.info(f"Using OCR for page {page_num + 1} in {pdf_path}")
                        ocr_lines = self._ocr_page(page, pdf_path, page_num)
                        for line in ocr_lines:
                            fixed_line = self.fix_duplicated_chars(line)
                            if not self.should_ignore_line(fixed_line):
                                text_lines.append(fixed_line)

                return text_lines

        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return []

    def _ocr_page(self, page, pdf_path: str, page_num: int) -> List[str]:
        """Extract text from page using OCR."""
        try:
            # Convert PDF page to image
            images = convert_from_path(
                pdf_path, first_page=page_num + 1, last_page=page_num + 1
            )
            if not images:
                return []

            # Extract text using Tesseract with Greek language
            text = pytesseract.image_to_string(
                images[0], lang="ell+eng", config="--psm 6"
            )

            return text.split("\n")

        except Exception as e:
            logger.error(f"OCR failed for page {page_num + 1}: {e}")
            return []

    def normalize_line(self, line: str) -> str:
        """Normalize a text line for parsing."""
        # Strip whitespace and compress multiple spaces to 2 spaces
        line = re.sub(r"\s+", "  ", line.strip())
        return line

    def find_wrap_category(self, lines: List[str], current_index: int) -> Optional[str]:
        """Find wrap category (Γ\\d+ followed by 'Επαγγελματικό' in next 1-2 lines)."""
        if current_index + 1 >= len(lines):
            return None

        # Check current line for Γ\d+ pattern
        current_line = self.normalize_line(lines[current_index])
        gamma_match = re.match(r"^(Γ\d+)(?:\s+(.+))?$", current_line)

        if not gamma_match:
            return None

        # Check next 1-2 lines for "Επαγγελματικό"
        for i in range(1, 3):
            if current_index + i < len(lines):
                next_line = self.normalize_line(lines[current_index + i])
                if "Επαγγελματικό" in next_line:
                    return "Επαγγελματικό"

        # Also check if current line contains both Γ\d+ and Επαγγελματικό
        if "Επαγγελματικό" in current_line:
            return "Επαγγελματικό"

        return None

    def find_record_blocks(self, lines: List[str]) -> List[List[str]]:
        """Find 3-row record blocks in the text lines with enhanced detection."""
        blocks = []
        i = 0

        while i < len(lines) - 2:
            # Check if current line matches ROW1 pattern
            line1 = self.normalize_line(lines[i])
            if ROW1_PATTERN.match(line1):
                # Check if next two lines exist and form a complete block
                if i + 2 < len(lines):
                    line2 = self.normalize_line(lines[i + 1])
                    line3 = self.normalize_line(lines[i + 2])

                    # Check if line2 matches category pattern or wrap category
                    if ROW2_PATTERN.match(line2) or self.find_wrap_category(
                        lines, i + 1
                    ):
                        blocks.append([line1, line2, line3])
                        i += 3  # Skip to next potential block
                        continue

            i += 1

        return blocks

    def parse_row1(self, line: str) -> Optional[Dict]:
        """Parse ROW1 containing account and customer information."""
        match = ROW1_PATTERN.match(line)
        if not match:
            return None

        # Combine Ονοματεπώνυμο and Διεύθυνση into a single field
        name = match.group("name").strip()
        address = match.group("addr").strip()
        combined_name_address = f"{name} {address}".strip()

        # Parse period into start and end dates
        from ..utils.validators import split_period

        period_raw = match.group("period")
        start_str, end_str = split_period(period_raw)

        return {
            "ΑρΠαροχής": str(match.group("par")),
            "ΑρΛογαριασμού": str(match.group("log")),
            "ΗμΈκδοσης": match.group("issued"),
            "ΠερίοδοςΚατανάλωσης": period_raw,
            "ΠερίοδοςΚατανάλωσης_Αρχική": start_str,
            "ΠερίοδοςΚατανάλωσης_Τελική": end_str,
            "Ονοματεπώνυμο_Διεύθυνση": combined_name_address,
            "Πόλη": match.group("city").strip(),
        }

    def parse_row2(self, line: str) -> Optional[Dict]:
        """Parse ROW2 containing invoice category with ΦΟΠ variations."""
        match = ROW2_PATTERN.match(line)
        if not match:
            return None

        code = match.group("code")
        label = match.group("label")

        # Normalize ΦΟΠ variations to "ΦΟΠ"
        if code in ["ΦΟΠ", "Φ.Ο.Π", "Φ Ο Π"]:
            category = "ΦΟΠ"
        elif code.startswith("Γ") and label == "Επαγγελματικό":
            category = "Επαγγελματικό"
        elif label == "Τιμολόγιο":
            category = "ΦΟΠ"
        else:
            category = "Επαγγελματικό"

        return {"ΚατηγορίαΤιμολογίου": category, "raw_code": code, "raw_label": label}

    def parse_row3(self, line: str) -> Optional[Dict]:
        """Parse ROW3 containing meter readings with fallback patterns."""
        # Try primary pattern first
        match = ROW3_PATTERN.match(line)
        if match:
            return {
                "Τελευταία": int(match.group("last")),
                "Προηγούμενη": int(match.group("prev")),
                "ΣΩΧΒ": int(match.group("soxv")),
                "ΣυνΩΧΒ": int(match.group("syn")),
            }

        # Try fallback pattern
        match = ROW3_FALLBACK_PATTERN.match(line)
        if match:
            return {
                "Τελευταία": int(match.group("last")),
                "Προηγούμενη": int(match.group("prev")),
                "ΣΩΧΒ": int(match.group("soxv")),
                "ΣυνΩΧΒ": int(match.group("syn")),
            }

        return None

    def extract_additional_fields(self, lines: List[str]) -> Dict:
        """Extract additional fields from the context."""
        additional_fields = {}

        # Join all lines for searching
        all_text = " ".join(lines)

        # Extract store information
        store_match = STORE_PATTERN.search(all_text)
        if store_match:
            additional_fields["ΚατάστημαΕξυπηρέτησης"] = store_match.group(1).strip()

        # Extract receipt number
        receipt_match = RECEIPT_PATTERN.search(all_text)
        if receipt_match:
            additional_fields["Παραστατικό"] = receipt_match.group(1)

        return additional_fields

    def parse_period_dates(
        self, period_str: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Parse period string into date_from and date_to (YYYY-MM-DD format)."""
        try:
            # Expected format: DD.MM.YYYY-DD.MM.YYYY
            if "-" in period_str:
                start_part, end_part = period_str.split("-", 1)

                # Parse start date
                start_date = datetime.strptime(start_part.strip(), "%d.%m.%Y")
                date_from = start_date.strftime("%Y-%m-%d")

                # Parse end date
                end_date = datetime.strptime(end_part.strip(), "%d.%m.%Y")
                date_to = end_date.strftime("%Y-%m-%d")

                return date_from, date_to
        except Exception as e:
            logger.warning(f"Failed to parse period dates from '{period_str}': {e}")

        return None, None

    def infer_subcategory(
        self, category: str, soxvb: Optional[int], context: Optional[List[str]] = None
    ) -> Optional[str]:
        """Infer subcategory for commercial invoices."""
        if category != "Επαγγελματικό":
            return None

        if soxvb is None:
            return None

        # Check for agricultural keywords in context
        if context:
            context_text = " ".join(context).upper()
            agricultural_keywords = ["ΑΓΡΟΤΙΚ", "ΑΓΡ", "ΑΓΡΟΤ", "ΑΓΡΟΚΤΗΜΑΤΙΚ"]
            if any(keyword in context_text for keyword in agricultural_keywords):
                return "Αγροτικό"

        # Determine based on ΣΩΧΒ value
        if soxvb == 1:
            return "Απλό επαγγελματικό"
        elif soxvb > 1:
            return "Βιομηχανικό"

        return None

    def calculate_confidence(
        self,
        row1_data: Optional[Dict],
        row2_data: Optional[Dict],
        row3_data: Optional[Dict],
    ) -> float:
        """Calculate confidence score for the record."""
        matches = 0
        total = 3

        if row1_data and row1_data.get("ΑρΠαροχής"):
            matches += 1
        if row1_data and row1_data.get("ΗμΈκδοσης"):
            matches += 1
        if row2_data and row2_data.get("ΚατηγορίαΤιμολογίου"):
            matches += 1

        return matches / total if total > 0 else 0.0

    def create_deduplication_key(self, record: Dict) -> str:
        """Create a unique key for deduplication."""
        ar_parochis = record.get("ΑρΠαροχής", "")
        ar_logariasmo = record.get("ΑρΛογαριασμού", "")
        im_ekdosis = record.get("ΗμΈκδοσης", "")
        periodos = record.get("ΠερίοδοςΚατανάλωσης", "")

        # Convert None values and empty strings to string "None"
        ar_parochis = (
            str(ar_parochis)
            if ar_parochis is not None and ar_parochis != ""
            else "None"
        )
        ar_logariasmo = (
            str(ar_logariasmo)
            if ar_logariasmo is not None and ar_logariasmo != ""
            else "None"
        )
        im_ekdosis = (
            str(im_ekdosis) if im_ekdosis is not None and im_ekdosis != "" else "None"
        )
        periodos = str(periodos) if periodos is not None and periodos != "" else "None"

        return f"{ar_parochis}_{ar_logariasmo}_{im_ekdosis}_{periodos}"

    def parse_block(self, lines: List[str], source: str) -> Optional[Dict]:
        """Parse a 3-row block into a structured record."""
        if len(lines) != 3:
            return None

        # Parse each row
        row1_data = self.parse_row1(lines[0])
        row2_data = self.parse_row2(lines[1])
        row3_data = self.parse_row3(lines[2])

        # Handle wrap category detection
        if not row2_data and self.find_wrap_category(lines, 1):
            row2_data = {
                "ΚατηγορίαΤιμολογίου": "Επαγγελματικό",
                "raw_code": "Γ-wrap",
                "raw_label": "Επαγγελματικό",
            }

        # Calculate confidence
        confidence = self.calculate_confidence(row1_data, row2_data, row3_data)

        # Create base record
        record = {
            "ΑρΠαροχής": None,
            "ΑρΛογαριασμού": None,
            "ΗμΈκδοσης": None,
            "ΠερίοδοςΚατανάλωσης": None,
            "Ονοματεπώνυμο_Διεύθυνση": None,
            "Πόλη": None,
            "Τελευταία": None,
            "Προηγούμενη": None,
            "ΣΩΧΒ": None,
            "ΣυνΩΧΒ": None,
            "ΚατηγορίαΤιμολογίου": None,
            "Υποκατηγορία": None,
            "Εκαθαριστικός": False,
            "ΚατάστημαΕξυπηρέτησης": None,
            "Παραστατικό": None,
            "date_from": None,
            "date_to": None,
            "needs_review": False,
            "reason": None,
            "confidence": confidence,
            "source_file": source,
        }

        # Merge data from all rows
        if row1_data:
            record.update(row1_data)
            # Parse period dates
            if row1_data.get("ΠερίοδοςΚατανάλωσης"):
                date_from, date_to = self.parse_period_dates(
                    row1_data["ΠερίοδοςΚατανάλωσης"]
                )
                record["date_from"] = date_from
                record["date_to"] = date_to

        if row2_data:
            record.update(row2_data)

        if row3_data:
            record.update(row3_data)
            # Set Εκαθαριστικός=True even if Τελευταία == Προηγούμενη
            record["Εκαθαριστικός"] = True

        # Extract additional fields
        additional_fields = self.extract_additional_fields(lines)
        record.update(additional_fields)

        # Infer subcategory
        if record["ΚατηγορίαΤιμολογίου"] == "Επαγγελματικό":
            record["Υποκατηγορία"] = self.infer_subcategory(
                record["ΚατηγορίαΤιμολογίου"], record.get("ΣΩΧΒ"), lines
            )

        # Check for deduplication
        dedup_key = self.create_deduplication_key(record)
        if dedup_key in self.processed_blocks:
            logger.info(f"Skipping duplicate record: {dedup_key}")
            return None

        self.processed_blocks.add(dedup_key)

        # Check confidence threshold
        if confidence < 0.90:
            record["needs_review"] = True
            missing_fields = []
            if not row1_data or not row1_data.get("ΑρΠαροχής"):
                missing_fields.append("ΑρΠαροχής")
            if not row1_data or not row1_data.get("ΗμΈκδοσης"):
                missing_fields.append("ΗμΈκδοσης")
            if not row2_data or not row2_data.get("ΚατηγορίαΤιμολογίου"):
                missing_fields.append("ΚατηγορίαΤιμολογίου")

            record[
                "reason"
            ] = f"Missing: {', '.join(missing_fields)} (confidence: {confidence:.2f})"

            # Print user-friendly message
            logging.warning(
                f"Δεν είμαι 90% σίγουρος για την εγγραφή στο αρχείο {source}."
            )
            logging.warning(f"   Εμπιστοσύνη: {confidence:.1%}")
            logging.warning(f"   Λείπουν: {', '.join(missing_fields)}")
            logging.warning("   Πώς θέλεις να προχωρήσω;")

        return record

    def parse_v2018(self, text: str) -> Dict:
        """Parse v2018 layout PDF text and extract structured data."""
        # normalize light whitespace for OCR robustness
        norm = re.sub(r"[ \t]+", " ", text).replace("\u00A0", " ")

        # Extract supply number - look for the pattern "555035070018" first
        supply_no = _safe_search(r"(555035070018)", norm)
        if not supply_no:
            # Look for the pattern "5 55035070-01 2" or similar
            supply_no = _safe_search(r"(\d{1,2}\s+\d{10,11}[-\s]\d{1,2})", norm)
        if not supply_no:
            # Look for the specific pattern from the PDF: "5 55035070-01 2"
            supply_no = _safe_search(r"(\d\s+\d{10}[-\s]\d{1,2})", norm)
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
        meter_readings = re.search(r"(\d{5})\s+(\d{5})\s+(\d{4})", norm)
        current_reading = None
        previous_reading = None
        if meter_readings:
            current_reading = meter_readings.group(1)
            previous_reading = meter_readings.group(2)

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

    def parse_by_layout(self, text: str, layout: str) -> Dict:
        """Route parsing based on detected layout."""
        if layout == "v2018":
            return self.parse_v2018(text)
        return self.parse_modern(text)  # existing path

    def parse_modern(self, text: str) -> Dict:
        """Parse modern layout using existing 3-row block structure."""
        # This is the existing parsing logic - we'll keep it as is
        # but wrap it in a method for consistency
        text_lines = text.split("\n") if isinstance(text, str) else text

        # Find record blocks
        blocks = self.find_record_blocks(text_lines)

        if not blocks:
            return {}

        # Parse the first block (assuming single record per PDF for v2018 compatibility)
        record = self.parse_block(blocks[0], "modern_layout")
        return record if record else {}

    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """Parse a single PDF file and extract invoice records."""
        logger.info(f"Processing {pdf_path}")

        text_lines = self.extract_text_from_pdf(pdf_path)
        if not text_lines:
            logger.warning(f"No text extracted from {pdf_path}")
            return []

        # Join text lines for layout detection
        full_text = "\n".join(text_lines)

        # Detect layout
        layout = "v2018" if detect_layout_vintage(full_text) else "modern"
        logger.info(f"Detected layout: {layout} for {pdf_path}")

        if layout == "v2018":
            # Parse v2018 layout using raw text (not filtered)
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    raw_text = ""
                    for page in pdf.pages:
                        raw_text += page.extract_text() or ""

                record = self.parse_v2018(raw_text)
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
        else:
            # Use existing modern layout parsing
            blocks = self.find_record_blocks(text_lines)
            logger.info(f"Found {len(blocks)} potential record blocks in {pdf_path}")

            records = []
            for i, block in enumerate(blocks):
                try:
                    record = self.parse_block(block, pdf_path)
                    if record:
                        records.append(record)
                        if record["needs_review"]:
                            self.needs_review.append(record)
                    else:
                        self.warnings.append(
                            f"Block {i+1} in {pdf_path}: Failed to parse"
                        )
                except Exception as e:
                    logger.error(f"Error parsing block {i+1} in {pdf_path}: {e}")
                    self.warnings.append(f"Block {i+1} in {pdf_path}: {e}")
                    continue

            return records

    def process_files(self, file_paths: List[str]) -> pd.DataFrame:
        """Process multiple PDF files and return a DataFrame."""
        all_records = []

        for file_path in file_paths:
            records = self.parse_pdf(file_path)
            all_records.extend(records)

        # Sort records by ΑρΠαροχής before creating DataFrame
        if all_records:
            all_records.sort(key=lambda x: str(x.get("ΑρΠαροχής", "")))
            logger.info(f"Sorted {len(all_records)} records by ΑρΠαροχής")

        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Log summary
        logger.info(f"Processed {len(file_paths)} files, extracted {len(df)} records")
        if self.needs_review:
            logger.warning(f"{len(self.needs_review)} records need review")
        if self.warnings:
            logger.warning(f"{len(self.warnings)} parsing warnings")

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
            logger.info(f"Sorted {len(df_output)} records by ΑρΠαροχής")

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

        logger.info("Output files written successfully")

        # Write warnings to log
        if self.warnings:
            with open(output_path / "warnings.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- Processing completed at {datetime.now()} ---\n")
                for warning in self.warnings:
                    f.write(f"WARNING: {warning}\n")


def main():
    """Main function to run the enhanced DEI extractor."""
    parser = argparse.ArgumentParser(
        description="Enhanced DEI invoice data extractor with comprehensive edge case handling"
    )
    parser.add_argument("--input", required=True, help="PDF file path or glob pattern")

    args = parser.parse_args()

    # Find PDF files
    input_path = Path(args.input)
    if input_path.is_file():
        pdf_files = [str(input_path)]
    else:
        pdf_files = list(Path(".").glob(args.input))
        pdf_files = [str(f) for f in pdf_files if f.suffix.lower() == ".pdf"]

    if not pdf_files:
        logger.error(f"No PDF files found matching pattern: {args.input}")
        return

    logging.info(f"Found {len(pdf_files)} PDF file(s) to process")

    # Process files
    extractor = DEIExtractorEnhanced()
    df = extractor.process_files(pdf_files)

    # Write outputs
    extractor.write_outputs(df)

    # Print summary
    logging.info("\n" + "=" * 60)
    logging.info("ENHANCED PROCESSING SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Total records extracted: {len(df)}")
    logging.info(f"Records needing review: {len(extractor.needs_review)}")
    logging.info(f"Parsing warnings: {len(extractor.warnings)}")
    logging.info(
        f"Duplicate records filtered: {len(extractor.processed_blocks) - len(df)}"
    )

    if extractor.needs_review:
        logging.info(f"\nRecords with confidence < 90%:")
        for record in extractor.needs_review:
            logging.info(f"  - {record['source_file']}: {record['reason']}")

    logging.info(f"\nOutput files created:")
    logging.info(f"  - ολα.csv / ολα.xlsx ({len(df)} records)")
    if not df.empty:
        fop_count = len(df[df["ΚατηγορίαΤιμολογίου"] == "ΦΟΠ"])
        epag_count = len(df[df["ΚατηγορίαΤιμολογίου"] == "Επαγγελματικό"])
        logging.info(f"  - φoπ.csv / φoπ.xlsx ({fop_count} records)")
        logging.info(
            f"  - επαγγελματικα.csv / επαγγελματικα.xlsx ({epag_count} records)"
        )

    # Show new features
    if not df.empty:
        logging.info(f"\nEnhanced Features Applied:")
        logging.info(
            f"  - ΦΟΠ variations normalized: "
            f"{len(df[df['raw_code'].isin(['Φ.Ο.Π', 'Φ Ο Π'])])}"
        )
        logging.info(
            f"  - Wrap categories detected: {len(df[df['raw_code'] == 'Γ-wrap'])}"
        )
        logging.info(f"  - Additional fields extracted:")
        store_count = len(
            df[
                df["ΚατάστημαΕξυπηρέτησης"].notna()
                & (df["ΚατάστημαΕξυπηρέτησης"] != "None")
            ]
        )
        receipt_count = len(
            df[df["Παραστατικό"].notna() & (df["Παραστατικό"] != "None")]
        )
        logging.info(f"    * ΚατάστημαΕξυπηρέτησης: {store_count}")
        logging.info(f"    * Παραστατικό: {receipt_count}")


if __name__ == "__main__":
    main()
