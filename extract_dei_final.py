#!/usr/bin/env python3
"""
DEI PDF Invoice Data Extractor - Final Version

This script extracts data from Greek DEI (Public Power Corporation) PDF invoices
using a precise 3-row block structure parsing approach.

Features:
- Extracts data from 1+ PDF files via CLI
- Identifies records in 3-row blocks with specific patterns
- Handles both text-based and scanned PDFs (OCR fallback)
- Generates separate output files for all records, residential (ΦΟΠ), and commercial invoices
- Implements 90% confidence threshold with review system

Installation:
1. Install Tesseract OCR: brew install tesseract tesseract-lang (macOS)
   or: sudo apt-get install tesseract-ocr tesseract-ocr-ell (Ubuntu)
2. Install Python dependencies: pip install -r requirements.txt

Usage:
    python extract_dei_final.py --input "path_or_glob/*.pdf"

Author: DEI Extractor Team
Version: 2.0
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

# Compile regex patterns for the 3-row block structure
ROW1_PATTERN = re.compile(
    r"(?P<par>\d{10,11})\s+(?P<log>\d{9,12})\s+(?P<issued>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<period>\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<name>.+?)\s{2,}(?P<addr>.+?)\s{2,}(?P<city>.+)$"
)

ROW2_PATTERN = re.compile(r"^(?P<code>ΦΟΠ|Γ\d+)\s+(?P<label>Τιμολόγιο|Επαγγελματικό)\b")

ROW3_PATTERN = re.compile(r"^Ημέρα\s+(?P<last>\d+)\s+(?P<prev>\d+)\s+(?P<soxv>\d+)\s+(?P<syn>\d+)\s*$")


class DEIExtractorFinal:
    """Final version of DEI extractor with precise 3-row block parsing."""
    
    def __init__(self):
        self.records = []
        self.needs_review = []
        self.warnings = []
        
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
                        text_lines.extend(text.split('\n'))
                    else:
                        # Fallback to OCR
                        logger.info(f"Using OCR for page {page_num + 1} in {pdf_path}")
                        ocr_lines = self._ocr_page(page, pdf_path, page_num)
                        for line in ocr_lines:
                            fixed_line = self.fix_duplicated_chars(line)
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
    
    def find_record_blocks(self, lines: List[str]) -> List[List[str]]:
        """Find 3-row record blocks in the text lines."""
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
                    
                    # Check if line2 matches category pattern
                    if ROW2_PATTERN.match(line2):
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
        """Parse ROW2 containing invoice category."""
        match = ROW2_PATTERN.match(line)
        if not match:
            return None
        
        code = match.group('code')
        label = match.group('label')
        
        # Determine category based on code and label
        if code == 'ΦΟΠ' or label == 'Τιμολόγιο':
            category = 'ΦΟΠ'
        else:
            category = 'Επαγγελματικό'
        
        return {
            'ΚατηγορίαΤιμολογίου': category,
            'raw_code': code,
            'raw_label': label
        }
    
    def parse_row3(self, line: str) -> Optional[Dict]:
        """Parse ROW3 containing meter readings."""
        match = ROW3_PATTERN.match(line)
        if not match:
            return None
        
        return {
            'Τελευταία': int(match.group('last')),
            'Προηγούμενη': int(match.group('prev')),
            'ΣΩΧΒ': int(match.group('soxv')),
            'ΣυνΩΧΒ': int(match.group('syn'))
        }
    
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
    
    def parse_block(self, lines: List[str], source: str) -> Optional[Dict]:
        """Parse a 3-row block into a structured record."""
        if len(lines) != 3:
            return None
        
        # Parse each row
        row1_data = self.parse_row1(lines[0])
        row2_data = self.parse_row2(lines[1])
        row3_data = self.parse_row3(lines[2])
        
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
            'needs_review': False,
            'reason': None,
            'confidence': confidence,
            'source_file': source
        }
        
        # Merge data from all rows
        if row1_data:
            record.update(row1_data)
        
        if row2_data:
            record.update(row2_data)
        
        if row3_data:
            record.update(row3_data)
            record['Εκαθαριστικός'] = True
        
        # Infer subcategory
        if record['ΚατηγορίαΤιμολογίου'] == 'Επαγγελματικό':
            record['Υποκατηγορία'] = self.infer_subcategory(
                record['ΚατηγορίαΤιμολογίου'], 
                record.get('ΣΩΧΒ'), 
                lines
            )
        
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
                       'ΚατηγορίαΤιμολογίου', 'Υποκατηγορία', 'reason', 'source_file']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        # Ensure IDs are strings to prevent scientific notation
        if 'ΑρΠαροχής' in df.columns:
            df['ΑρΠαροχής'] = df['ΑρΠαροχής'].astype(str)
        if 'ΑρΛογαριασμού' in df.columns:
            df['ΑρΛογαριασμού'] = df['ΑρΛογαριασμού'].astype(str)
        
        # Write all records
        df.to_csv('ολα.csv', index=False, encoding='utf-8-sig')
        df.to_excel('ολα.xlsx', index=False)
        
        # Write ΦΟΠ records
        fop_df = df[df['ΚατηγορίαΤιμολογίου'] == 'ΦΟΠ'].copy()
        if not fop_df.empty:
            fop_df.to_csv('φoπ.csv', index=False, encoding='utf-8-sig')
            fop_df.to_excel('φoπ.xlsx', index=False)
        
        # Write Επαγγελματικό records
        epag_df = df[df['ΚατηγορίαΤιμολογίου'] == 'Επαγγελματικό'].copy()
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
    """Main function to run the final DEI extractor."""
    parser = argparse.ArgumentParser(description='Final DEI invoice data extractor with 3-row block parsing')
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
    extractor = DEIExtractorFinal()
    df = extractor.process_files(pdf_files)
    
    # Write outputs
    extractor.write_outputs(df)
    
    # Print summary
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    print(f"Total records extracted: {len(df)}")
    print(f"Records needing review: {len(extractor.needs_review)}")
    print(f"Parsing warnings: {len(extractor.warnings)}")
    
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


if __name__ == "__main__":
    main()
