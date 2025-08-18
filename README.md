# DEI PDF Invoice Extractor - Enhanced Version 3.0

A robust Python script for extracting structured data from Greek DEI (electricity company) PDF invoices with comprehensive edge case handling. The script supports both text-based PDFs and OCR fallback for scanned documents.

## 🚀 Enhanced Features (Version 3.0)

### Edge Case Handling
- **ΦΟΠ Variations**: Recognizes `ΦΟΠ`, `Φ.Ο.Π`, `Φ Ο Π` and normalizes to "ΦΟΠ"
- **Wrap Categories**: Detects Γ\d+ codes with "Επαγγελματικό" in following lines
- **Header/Footer Filtering**: Automatically excludes common headers and footers
- **Financial Line Exclusion**: Filters out ΦΠΑ, charges, and other financial data
- **Summary Block Exclusion**: Ignores "Σ Υ Ν Ο Λ Α Π Ο Λ Λ Α Π Λ Ο Υ" blocks
- **Deduplication**: Removes duplicate records based on key fields

### Enhanced Parsing
- **Improved ROW1 Regex**: Better handling of names, addresses, and cities with numbers
- **ROW3 Fallback Patterns**: Multiple patterns for meter reading extraction
- **Zero Consumption Handling**: Correctly marks Εκαθαριστικός=True even with zero consumption
- **Additional Fields**: Extracts ΚατάστημαΕξυπηρέτησης, Παραστατικό, and parsed dates

### Data Quality
- **90% Confidence Threshold**: Records below threshold flagged for review
- **Comprehensive Validation**: Multiple validation layers for data integrity
- **Detailed Logging**: Extensive logging for troubleshooting and debugging

## Features

- **Multi-format Support**: Handles both text-based and scanned PDFs
- **OCR Fallback**: Automatic OCR processing for scanned documents using Tesseract
- **Smart Parsing**: Robust regex-based parsing with Greek language support
- **Business Logic**: Implements DEI-specific business rules for invoice categorization
- **Multiple Output Formats**: Generates CSV and Excel files
- **Validation**: Built-in data validation and confidence scoring
- **Logging**: Comprehensive logging for troubleshooting
- **Edge Case Handling**: Comprehensive handling of various PDF formats and edge cases

## Extracted Fields

The script extracts the following fields from DEI invoices:

### Core Fields
- **ΑρΠαροχής**: Account number (10-11 digits)
- **ΑρΛογαριασμού**: Account number (if present)
- **ΗμΈκδοσης**: Issue date
- **ΠερίοδοςΚατανάλωσης**: Consumption period
- **Ονοματεπώνυμο**: Customer name
- **Διεύθυνση**: Address
- **Πόλη**: City
- **Τελευταία**: Latest meter reading
- **Προηγούμενη**: Previous meter reading
- **ΣΩΧΒ**: Power factor
- **ΣυνΩΧΒ**: Total power factor
- **ΚατηγορίαΤιμολογίου**: Invoice category (ΦΟΠ or Επαγγελματικό)
- **Υποκατηγορία**: Subcategory for commercial invoices
- **Εκαθαριστικός**: Boolean flag for final readings

### Enhanced Fields (New in v3.0)
- **ΚατάστημαΕξυπηρέτησης**: Service store information
- **Παραστατικό**: Receipt number
- **date_from**: Start date of consumption period (YYYY-MM-DD)
- **date_to**: End date of consumption period (YYYY-MM-DD)
- **raw_code**: Original category code before normalization
- **raw_label**: Original category label
- **confidence**: Confidence score (0.0-1.0)
- **needs_review**: Flag for records requiring manual review
- **reason**: Explanation for low confidence or parsing issues

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Tesseract OCR** (for scanned PDFs)

### Install Tesseract

#### macOS
```bash
brew install tesseract tesseract-lang
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-ell
```

#### Windows
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Process a single PDF file
python extract_dei_final.py --input "invoice.pdf"

# Process multiple PDF files using glob pattern
python extract_dei_final.py --input "*.pdf"

# Process files from specific directory
python extract_dei_final.py --input "path/to/invoices/*.pdf"
```

### Output Files

The script generates the following output files:

1. **ολα.csv/ολα.xlsx**: All extracted records
2. **φoπ.csv/φoπ.xlsx**: Only residential (ΦΟΠ) invoices
3. **επαγγελματικα.csv/επαγγελματικα.xlsx**: Only commercial (Επαγγελματικό) invoices
4. **warnings.log**: Log file with warnings and errors

### Testing

Run the comprehensive test suite to validate all enhanced features:

```bash
python test_final_extractor.py
```

## Business Rules

### Invoice Categorization

- **ΦΟΠ**: Residential invoices (normalized from `ΦΟΠ`, `Φ.Ο.Π`, `Φ Ο Π`)
- **Επαγγελματικό**: Commercial invoices (including wrap categories with Γ\d+)

### Commercial Subcategories

- **Απλό επαγγελματικό**: When ΣΩΧΒ = 1
- **Βιομηχανικό**: When ΣΩΧΒ > 1
- **Αγροτικό**: When agricultural keywords are detected (optional)

### Εκαθαριστικός Flag

- **True**: When ROW3 data is present (even if Τελευταία == Προηγούμενη)
- **False**: When no ROW3 data is found

### Deduplication

Records are considered duplicates if they share the same:
- ΑρΠαροχής
- ΑρΛογαριασμού  
- ΗμΈκδοσης
- ΠερίοδοςΚατανάλωσης

## Enhanced Edge Cases

### ΦΟΠ Variations
The extractor automatically normalizes all ΦΟΠ variations:
- `ΦΟΠ` → "ΦΟΠ"
- `Φ.Ο.Π` → "ΦΟΠ"
- `Φ Ο Π` → "ΦΟΠ"

### Wrap Category Detection
Detects cases where category information spans multiple lines:
```
Γ21
Επαγγελματικό
```
→ Categorized as "Επαγγελματικό"

### Header/Footer Filtering
Automatically excludes common headers and footers:
- ΔΗΜΟΣΙΑ ΕΠΙΧΕΙΡΗΣΗ ΗΛΕΚΤΡΙΣΜΟΥ
- ΗΜΕΡΟΛΟΓΙΟ ΕΚΔΟΣΗΣ
- ΚΩΔ.ΠΟΛΛΑΠΛΟΥ, ΚΩΔ.ΕΤΑΙΡΟΥ
- ΟΝΟΜΑ ΔΗΜΟΥ, ΑΦΜ, ΣΕΛΙΔΑ

### Financial Line Exclusion
Filters out financial information:
- ΦΠΑ
- ΡΥΘΜΙΖΟΜΕΝΕΣ ΧΡΕΩΣΕΙΣ
- ΧΡΕΩΣΕΙΣ ΠΡΟΜΗΘΕΙΑΣ ΔΕΗ
- ΤΡΕΧΩΝ ΜΗΝΑΣ

### Enhanced ROW3 Parsing
Supports multiple meter reading formats:
- Primary: `Ημέρα 1234 1230 1 1234`
- Fallback: `1234 1230 1 1234`

## Technical Details

### OCR Configuration

The script uses Tesseract with the following configuration:
- Language: Greek + English (`ell+eng`)
- Page segmentation mode: 6 (uniform block of text)
- Automatic fallback when text extraction fails

### Text Processing

1. **Line Filtering**: Removes headers, footers, and financial lines
2. **Normalization**: Removes extra whitespace, normalizes separators
3. **Block Detection**: Identifies invoice blocks using enhanced patterns
4. **Regex Parsing**: Extracts structured data using multiple fallback patterns
5. **Validation**: Validates extracted data against business rules
6. **Deduplication**: Removes duplicate records based on composite keys

### Error Handling

- **Low Confidence**: Records with <90% confidence are flagged for review
- **OCR Failures**: Logged with detailed error information
- **Missing Data**: Handled gracefully with None values
- **Edge Cases**: Comprehensive handling of various PDF formats

## Performance Improvements

### Memory Efficiency
- Deduplication using sets for O(1) lookup
- Streaming text processing to avoid loading entire PDFs in memory

### Processing Speed
- Compiled regex patterns for faster matching
- Early exit conditions for invalid blocks
- Efficient line filtering

### Accuracy Improvements
- 90% confidence threshold with detailed reasoning
- Multiple fallback patterns for robust parsing
- Comprehensive edge case handling

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   ```
   Error: tesseract is not installed or not in PATH
   ```
   Solution: Install Tesseract and ensure it's in your system PATH

2. **OCR quality issues**
   - Ensure PDF pages are properly scanned
   - Check that Greek language pack is installed
   - Try adjusting image quality if possible

3. **Parsing errors**
   - Check warnings.log for detailed error information
   - Verify PDF format matches expected structure
   - Review records marked as "needs_review"

4. **Duplicate records**
   - Check deduplication logic in warnings.log
   - Verify key fields are properly extracted

### Performance Tips

- For large batches, process files in smaller groups
- Ensure sufficient disk space for temporary OCR files
- Monitor memory usage with very large PDFs

### Debug Mode

Enable detailed logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Project Structure

```
dei_extractor/
├── extract_dei_final.py     # Enhanced main extraction script
├── test_final_extractor.py  # Comprehensive test suite
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── ENHANCED_FEATURES.md    # Detailed feature documentation
└── sample_invoice.txt      # Sample data for testing
```

### Adding New Patterns

To add support for new invoice formats:

1. Update regex patterns in parsing methods
2. Add new test cases in `test_final_extractor.py`
3. Update business rules if needed
4. Test with sample data

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Version History

### Version 3.0 (Enhanced)
- Added ΦΟΠ variations recognition
- Implemented wrap category detection
- Added header/footer filtering
- Added financial line exclusion
- Implemented deduplication system
- Enhanced ROW1 and ROW3 regex patterns
- Added additional fields extraction
- Improved zero consumption handling
- Added comprehensive test suite

### Version 2.0 (Final)
- Basic 3-row block parsing
- OCR fallback support
- Confidence scoring system
- Multiple output formats

## License

This project is provided as-is for educational and business use. Please ensure compliance with DEI's terms of service when using this tool.

## Support

For issues and questions:
1. Check the `warnings.log` file for detailed error messages
2. Review the test output for specific feature validation
3. Verify PDF format matches expected structure
4. Ensure all dependencies are properly installed
5. Consult `ENHANCED_FEATURES.md` for detailed feature documentation
