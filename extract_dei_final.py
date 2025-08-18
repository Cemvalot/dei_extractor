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

Installation:
1. Install Tesseract OCR: brew install tesseract tesseract-lang (macOS)
   or: sudo apt-get install tesseract-ocr tesseract-ocr-ell (Ubuntu)
2. Install Python dependencies: pip install -r requirements.txt

Usage:
    python extract_dei_final.py --input "path_or_glob/*.pdf"

Author: DEI Extractor Team
Version: 3.0 - Enhanced with Edge Cases
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings

import pandas as pd
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from openpyxl import Workbook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('warnings.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Enhanced regex patterns for the 3-row block structure
ROW1_PATTERN = re.compile(
    r"(?P<par>\d{10,11})\s+(?P<log>\d{9,12})\s+(?P<issued>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<period>\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<name>[^0-9]+?)\s{2,}(?P<addr>[^0-9]+?)\s{2,}(?P<city>[^0-9]+)$"
)

# Enhanced ROW2 pattern to handle ΦΟΠ variations and wrap categories
ROW2_PATTERN = re.compile(r"^(?P<code>ΦΟΠ|Φ\.Ο\.Π|Φ\s+Ο\s+Π|Γ\d+)\s+(?P<label>Τιμολόγιο|Επαγγελματικό)\b")

# Enhanced ROW3 pattern with fallback options
ROW3_PATTERN = re.compile(r"^Ημέρα\s+(?P<last>\d+)\s+(?P<prev>\d+)\s+(?P<soxv>\d+)\s+(?P<syn>\d+)\s*$")
ROW3_FALLBACK_PATTERN = re.compile(r"^(?P<last>\d+)\s+(?P<prev>\d+)\s+(?P<soxv>\d+)\s+(?P<syn>\d+)\s*$")

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
    re.compile(r"ΡΥΘΜΙΖΟΜΕΝΕΣ\s+ΧΡΕΩΣΕΙΣ", re.IGNORECASE),
    re.compile(r"ΧΡΕΩΣΕΙΣ\s+ΠΡΟΜΗΘΕΙΑΣ\s+ΔΕΗ", re.IGNORECASE),
    re.compile(r"ΤΡΕΧΩΝ\s+ΜΗΝΑΣ", re.IGNORECASE),
]

# Pattern to exclude summary blocks
SUMMARY_PATTERN = re.compile(r"Σ\s+Υ\s+Ν\s+Ο\s+Λ\s+Α\s+Π\s+Ο\s+Λ\s+Λ\s+Α\s+Π\s+Λ\s+Ο\s+Υ", re.IGNORECASE)


class DEIExtractorEnhanced:
    """Enhanced version of DEI extractor with comprehensive edge case handling."""
    
    def __init__(self):
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
                        filtered_lines = [line for line in text.split('\n') 
                                        if not self.should_ignore_line(line)]
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
            images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
            if not images:
                return []
            
            # Extract text using Tesseract with Greek language
            text = pytesseract.image_to_string(
                images[0], 
                lang='ell+eng',
                config='--psm 6'
            )
            
            return text.split('\n')
            
        except Exception as e:
            logger.error(f"OCR failed for page {page_num + 1}: {e}")
            return []
    
    def normalize_line(self, line: str) -> str:
        """Normalize a text line for parsing."""
        # Strip whitespace and compress multiple spaces to 2 spaces
        line = re.sub(r'\s+', '  ', line.strip())
        return line
    
    def find_wrap_category(self, lines: List[str], current_index: int) -> Optional[str]:
        """Find wrap category (Γ\\d+ followed by 'Επαγγελματικό' in next 1-2 lines)."""
        if current_index + 1 >= len(lines):
            return None
        
        # Check current line for Γ\d+ pattern
        current_line = self.normalize_line(lines[current_index])
        gamma_match = re.match(r"^(Γ\d+)\s+(.+)$", current_line)
        
        if not gamma_match:
            return None
        
        # Check next 1-2 lines for "Επαγγελματικό"
        for i in range(1, 3):
            if current_index + i < len(lines):
                next_line = self.normalize_line(lines[current_index + i])
                if "Επαγγελματικό" in next_line:
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
                    if ROW2_PATTERN.match(line2) or self.find_wrap_category(lines, i + 1):
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
        
        return {
            'ΑρΠαροχής': str(match.group('par')),
            'ΑρΛογαριασμού': str(match.group('log')),
            'ΗμΈκδοσης': match.group('issued'),
            'ΠερίοδοςΚατανάλωσης': match.group('period'),
            'Ονοματεπώνυμο': match.group('name').strip(),
            'Διεύθυνση': match.group('addr').strip(),
            'Πόλη': match.group('city').strip()
        }
    
    def parse_row2(self, line: str) -> Optional[Dict]:
        """Parse ROW2 containing invoice category with ΦΟΠ variations."""
        match = ROW2_PATTERN.match(line)
        if not match:
            return None
        
        code = match.group('code')
        label = match.group('label')
        
        # Normalize ΦΟΠ variations to "ΦΟΠ"
        if code in ['ΦΟΠ', 'Φ.Ο.Π', 'Φ Ο Π']:
            category = 'ΦΟΠ'
        elif code.startswith('Γ') and label == 'Επαγγελματικό':
            category = 'Επαγγελματικό'
        elif label == 'Τιμολόγιο':
            category = 'ΦΟΠ'
        else:
            category = 'Επαγγελματικό'
        
        return {
            'ΚατηγορίαΤιμολογίου': category,
            'raw_code': code,
            'raw_label': label
        }
    
    def parse_row3(self, line: str) -> Optional[Dict]:
        """Parse ROW3 containing meter readings with fallback patterns."""
        # Try primary pattern first
        match = ROW3_PATTERN.match(line)
        if match:
            return {
                'Τελευταία': int(match.group('last')),
                'Προηγούμενη': int(match.group('prev')),
                'ΣΩΧΒ': int(match.group('soxv')),
                'ΣυνΩΧΒ': int(match.group('syn'))
            }
        
        # Try fallback pattern
        match = ROW3_FALLBACK_PATTERN.match(line)
        if match:
            return {
                'Τελευταία': int(match.group('last')),
                'Προηγούμενη': int(match.group('prev')),
                'ΣΩΧΒ': int(match.group('soxv')),
                'ΣυνΩΧΒ': int(match.group('syn'))
            }
        
        return None
    
    def extract_additional_fields(self, lines: List[str]) -> Dict:
        """Extract additional fields from the context."""
        additional_fields = {}
        
        # Join all lines for searching
        all_text = ' '.join(lines)
        
        # Extract store information
        store_match = STORE_PATTERN.search(all_text)
        if store_match:
            additional_fields['ΚατάστημαΕξυπηρέτησης'] = store_match.group(1).strip()
        
        # Extract receipt number
        receipt_match = RECEIPT_PATTERN.search(all_text)
        if receipt_match:
            additional_fields['Παραστατικό'] = receipt_match.group(1)
        
        return additional_fields
    
    def parse_period_dates(self, period_str: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse period string into date_from and date_to (YYYY-MM-DD format)."""
        try:
            # Expected format: DD.MM.YYYY-DD.MM.YYYY
            if '-' in period_str:
                start_part, end_part = period_str.split('-', 1)
                
                # Parse start date
                start_date = datetime.strptime(start_part.strip(), '%d.%m.%Y')
                date_from = start_date.strftime('%Y-%m-%d')
                
                # Parse end date
                end_date = datetime.strptime(end_part.strip(), '%d.%m.%Y')
                date_to = end_date.strftime('%Y-%m-%d')
                
                return date_from, date_to
        except Exception as e:
            logger.warning(f"Failed to parse period dates from '{period_str}': {e}")
        
        return None, None
    
    def infer_subcategory(self, category: str, soxvb: Optional[int], context: Optional[List[str]] = None) -> Optional[str]:
        """Infer subcategory for commercial invoices."""
        if category != 'Επαγγελματικό':
            return None
        
        if soxvb is None:
            return None
        
        # Check for agricultural keywords in context
        if context:
            context_text = ' '.join(context).upper()
            agricultural_keywords = ['ΑΓΡΟΤΙΚ', 'ΑΓΡ', 'ΑΓΡΟΤ', 'ΑΓΡΟΚΤΗΜΑΤΙΚ']
            if any(keyword in context_text for keyword in agricultural_keywords):
                return 'Αγροτικό'
        
        # Determine based on ΣΩΧΒ value
        if soxvb == 1:
            return 'Απλό επαγγελματικό'
        elif soxvb > 1:
            return 'Βιομηχανικό'
        
        return None
    
    def calculate_confidence(self, row1_data: Optional[Dict], row2_data: Optional[Dict], row3_data: Optional[Dict]) -> float:
        """Calculate confidence score for the record."""
        matches = 0
        total = 3
        
        if row1_data and row1_data.get('ΑρΠαροχής'):
            matches += 1
        if row1_data and row1_data.get('ΗμΈκδοσης'):
            matches += 1
        if row2_data and row2_data.get('ΚατηγορίαΤιμολογίου'):
            matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def create_deduplication_key(self, record: Dict) -> str:
        """Create a unique key for deduplication."""
        return f"{record.get('ΑρΠαροχής', '')}_{record.get('ΑρΛογαριασμού', '')}_{record.get('ΗμΈκδοσης', '')}_{record.get('ΠερίοδοςΚατανάλωσης', '')}"
    
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
                'ΚατηγορίαΤιμολογίου': 'Επαγγελματικό',
                'raw_code': 'Γ-wrap',
                'raw_label': 'Επαγγελματικό'
            }
        
        # Calculate confidence
        confidence = self.calculate_confidence(row1_data, row2_data, row3_data)
        
        # Create base record
        record = {
            'ΑρΠαροχής': None,
            'ΑρΛογαριασμού': None,
            'ΗμΈκδοσης': None,
            'ΠερίοδοςΚατανάλωσης': None,
            'Ονοματεπώνυμο': None,
            'Διεύθυνση': None,
            'Πόλη': None,
            'Τελευταία': None,
            'Προηγούμενη': None,
            'ΣΩΧΒ': None,
            'ΣυνΩΧΒ': None,
            'ΚατηγορίαΤιμολογίου': None,
            'Υποκατηγορία': None,
            'Εκαθαριστικός': False,
            'ΚατάστημαΕξυπηρέτησης': None,
            'Παραστατικό': None,
            'date_from': None,
            'date_to': None,
            'needs_review': False,
            'reason': None,
            'confidence': confidence,
            'source_file': source
        }
        
        # Merge data from all rows
        if row1_data:
            record.update(row1_data)
            # Parse period dates
            if row1_data.get('ΠερίοδοςΚατανάλωσης'):
                date_from, date_to = self.parse_period_dates(row1_data['ΠερίοδοςΚατανάλωσης'])
                record['date_from'] = date_from
                record['date_to'] = date_to
        
        if row2_data:
            record.update(row2_data)
        
        if row3_data:
            record.update(row3_data)
            # Set Εκαθαριστικός=True even if Τελευταία == Προηγούμενη
            record['Εκαθαριστικός'] = True
        
        # Extract additional fields
        additional_fields = self.extract_additional_fields(lines)
        record.update(additional_fields)
        
        # Infer subcategory
        if record['ΚατηγορίαΤιμολογίου'] == 'Επαγγελματικό':
            record['Υποκατηγορία'] = self.infer_subcategory(
                record['ΚατηγορίαΤιμολογίου'], 
                record.get('ΣΩΧΒ'), 
                lines
            )
        
        # Check for deduplication
        dedup_key = self.create_deduplication_key(record)
        if dedup_key in self.processed_blocks:
            logger.info(f"Skipping duplicate record: {dedup_key}")
            return None
        
        self.processed_blocks.add(dedup_key)
        
        # Check confidence threshold
        if confidence < 0.90:
            record['needs_review'] = True
            missing_fields = []
            if not row1_data or not row1_data.get('ΑρΠαροχής'):
                missing_fields.append('ΑρΠαροχής')
            if not row1_data or not row1_data.get('ΗμΈκδοσης'):
                missing_fields.append('ΗμΈκδοσης')
            if not row2_data or not row2_data.get('ΚατηγορίαΤιμολογίου'):
                missing_fields.append('ΚατηγορίαΤιμολογίου')
            
            record['reason'] = f"Missing: {', '.join(missing_fields)} (confidence: {confidence:.2f})"
            
            # Print user-friendly message
            print(f"\n⚠️  Δεν είμαι 90% σίγουρος για την εγγραφή στο αρχείο {source}.")
            print(f"   Εμπιστοσύνη: {confidence:.1%}")
            print(f"   Λείπουν: {', '.join(missing_fields)}")
            print("   Πώς θέλεις να προχωρήσω;")
        
        return record
    
    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """Parse a single PDF file and extract invoice records."""
        logger.info(f"Processing {pdf_path}")
        
        text_lines = self.extract_text_from_pdf(pdf_path)
        if not text_lines:
            logger.warning(f"No text extracted from {pdf_path}")
            return []
        
        # Find record blocks
        blocks = self.find_record_blocks(text_lines)
        logger.info(f"Found {len(blocks)} potential record blocks in {pdf_path}")
        
        records = []
        for i, block in enumerate(blocks):
            try:
                record = self.parse_block(block, pdf_path)
                if record:
                    records.append(record)
                    if record['needs_review']:
                        self.needs_review.append(record)
                else:
                    self.warnings.append(f"Block {i+1} in {pdf_path}: Failed to parse")
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
        
        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        
        # Log summary
        logger.info(f"Processed {len(file_paths)} files, extracted {len(df)} records")
        if self.needs_review:
            logger.warning(f"{len(self.needs_review)} records need review")
        if self.warnings:
            logger.warning(f"{len(self.warnings)} parsing warnings")
        
        return df
    
    def write_outputs(self, df: pd.DataFrame):
        """Write output files in CSV and Excel formats."""
        if df.empty:
            logger.warning("No data to write")
            return
        
        # Ensure all text columns are strings
        text_columns = ['ΑρΠαροχής', 'ΑρΛογαριασμού', 'Ονοματεπώνυμο', 'Διεύθυνση', 'Πόλη', 
                       'ΚατηγορίαΤιμολογίου', 'Υποκατηγορία', 'reason', 'source_file',
                       'ΚατάστημαΕξυπηρέτησης', 'Παραστατικό', 'date_from', 'date_to']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        # Ensure IDs are strings to prevent scientific notation
        if 'ΑρΠαροχής' in df.columns:
            df['ΑρΠαροχής'] = df['ΑρΠαροχής'].astype(str)
        if 'ΑρΛογαριασμού' in df.columns:
            df['ΑρΛογαριασμού'] = df['ΑρΛογαριασμού'].astype(str)
        
        # Drop internal/processing columns before writing output files
        drop_cols = ["ΚατάστημαΕξυπηρέτησης", "Παραστατικό", "needs_review", "reason", "confidence"]
        
        # Create copies for output files
        df_output = df.copy()
        fop_df = df[df['ΚατηγορίαΤιμολογίου'] == 'ΦΟΠ'].copy()
        epag_df = df[df['ΚατηγορίαΤιμολογίου'] == 'Επαγγελματικό'].copy()
        
        # Drop columns from all output DataFrames
        for df_out in [df_output, fop_df, epag_df]:
            for col in drop_cols:
                if col in df_out.columns:
                    df_out.drop(columns=col, inplace=True)
        
        # Write all records
        df_output.to_csv('ολα.csv', index=False, encoding='utf-8-sig')
        df_output.to_excel('ολα.xlsx', index=False)
        
        # Write ΦΟΠ records
        if not fop_df.empty:
            fop_df.to_csv('φoπ.csv', index=False, encoding='utf-8-sig')
            fop_df.to_excel('φoπ.xlsx', index=False)
        
        # Write Επαγγελματικό records
        if not epag_df.empty:
            epag_df.to_csv('επαγγελματικα.csv', index=False, encoding='utf-8-sig')
            epag_df.to_excel('επαγγελματικα.xlsx', index=False)
        
        logger.info("Output files written successfully")
        
        # Write warnings to log
        if self.warnings:
            with open('warnings.log', 'a', encoding='utf-8') as f:
                f.write(f"\n--- Processing completed at {datetime.now()} ---\n")
                for warning in self.warnings:
                    f.write(f"WARNING: {warning}\n")


def main():
    """Main function to run the enhanced DEI extractor."""
    parser = argparse.ArgumentParser(description='Enhanced DEI invoice data extractor with comprehensive edge case handling')
    parser.add_argument('--input', required=True, help='PDF file path or glob pattern')
    
    args = parser.parse_args()
    
    # Find PDF files
    input_path = Path(args.input)
    if input_path.is_file():
        pdf_files = [str(input_path)]
    else:
        pdf_files = list(Path('.').glob(args.input))
        pdf_files = [str(f) for f in pdf_files if f.suffix.lower() == '.pdf']
    
    if not pdf_files:
        logger.error(f"No PDF files found matching pattern: {args.input}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    # Process files
    extractor = DEIExtractorEnhanced()
    df = extractor.process_files(pdf_files)
    
    # Write outputs
    extractor.write_outputs(df)
    
    # Print summary
    print("\n" + "="*60)
    print("ENHANCED PROCESSING SUMMARY")
    print("="*60)
    print(f"Total records extracted: {len(df)}")
    print(f"Records needing review: {len(extractor.needs_review)}")
    print(f"Parsing warnings: {len(extractor.warnings)}")
    print(f"Duplicate records filtered: {len(extractor.processed_blocks) - len(df)}")
    
    if extractor.needs_review:
        print(f"\nRecords with confidence < 90%:")
        for record in extractor.needs_review:
            print(f"  - {record['source_file']}: {record['reason']}")
    
    print(f"\nOutput files created:")
    print(f"  - ολα.csv / ολα.xlsx ({len(df)} records)")
    if not df.empty:
        fop_count = len(df[df['ΚατηγορίαΤιμολογίου'] == 'ΦΟΠ'])
        epag_count = len(df[df['ΚατηγορίαΤιμολογίου'] == 'Επαγγελματικό'])
        print(f"  - φoπ.csv / φoπ.xlsx ({fop_count} records)")
        print(f"  - επαγγελματικα.csv / επαγγελματικα.xlsx ({epag_count} records)")
    
    # Show new features
    if not df.empty:
        print(f"\nEnhanced Features Applied:")
        print(f"  - ΦΟΠ variations normalized: {len(df[df['raw_code'].isin(['Φ.Ο.Π', 'Φ Ο Π'])])}")
        print(f"  - Wrap categories detected: {len(df[df['raw_code'] == 'Γ-wrap'])}")
        print(f"  - Additional fields extracted:")
        store_count = len(df[df['ΚατάστημαΕξυπηρέτησης'].notna() & (df['ΚατάστημαΕξυπηρέτησης'] != 'None')])
        receipt_count = len(df[df['Παραστατικό'].notna() & (df['Παραστατικό'] != 'None')])
        print(f"    * ΚατάστημαΕξυπηρέτησης: {store_count}")
        print(f"    * Παραστατικό: {receipt_count}")


if __name__ == "__main__":
    main()
