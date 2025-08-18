# DEI PDF Invoice Extractor

A robust Python script for extracting structured data from Greek DEI (electricity company) PDF invoices. The script supports both text-based PDFs and OCR fallback for scanned documents.

## Features

- **Multi-format Support**: Handles both text-based and scanned PDFs
- **OCR Fallback**: Automatic OCR processing for scanned documents using Tesseract
- **Smart Parsing**: Robust regex-based parsing with Greek language support
- **Business Logic**: Implements DEI-specific business rules for invoice categorization
- **Multiple Output Formats**: Generates CSV and Excel files
- **Validation**: Built-in data validation and confidence scoring
- **Logging**: Comprehensive logging for troubleshooting

## Extracted Fields

The script extracts the following fields from DEI invoices:

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
python extract_dei.py --input "invoice.pdf"

# Process multiple PDF files using glob pattern
python extract_dei.py --input "*.pdf"

# Process files from specific directory
python extract_dei.py --input "path/to/invoices/*.pdf"
```

### Output Files

The script generates the following output files:

1. **ολα.csv/ολα.xlsx**: All extracted records
2. **φoπ.csv/φoπ.xlsx**: Only residential (ΦΟΠ) invoices
3. **επαγγελματικα.csv/επαγγελματικα.xlsx**: Only commercial (Επαγγελματικό) invoices
4. **warnings.log**: Log file with warnings and errors

### Testing

Run the test suite to validate functionality:

```bash
python test_extractor.py
```

## Business Rules

### Invoice Categorization

- **ΦΟΠ**: Residential invoices (appears as "ΦΟΠ Τιμολόγιο")
- **Επαγγελματικό**: Commercial invoices (appears as "Γ21 Επαγγελματικό")

### Commercial Subcategories

- **Απλό επαγγελματικό**: When ΣΩΧΒ = 1
- **Βιομηχανικό**: When ΣΩΧΒ > 1
- **Αγροτικό**: When agricultural keywords are detected (optional)

### Εκαθαριστικός Flag

- **True**: When a numeric value exists in the "Τελευτ." column
- **False**: When no numeric value is found

## Technical Details

### OCR Configuration

The script uses Tesseract with the following configuration:
- Language: Greek + English (`ell+eng`)
- Page segmentation mode: 6 (uniform block of text)
- Automatic fallback when text extraction fails

### Text Processing

1. **Normalization**: Removes extra whitespace, normalizes separators
2. **Block Detection**: Identifies invoice blocks using header patterns
3. **Regex Parsing**: Extracts structured data using pattern matching
4. **Validation**: Validates extracted data against business rules

### Error Handling

- **Low Confidence**: Records with <90% confidence are flagged for review
- **OCR Failures**: Logged with detailed error information
- **Missing Data**: Handled gracefully with None values

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

### Performance Tips

- For large batches, process files in smaller groups
- Ensure sufficient disk space for temporary OCR files
- Monitor memory usage with very large PDFs

## Development

### Project Structure

```
dei_extractor/
├── extract_dei.py          # Main extraction script
├── test_extractor.py       # Test suite
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── sample_invoice.txt     # Sample data for testing
```

### Adding New Patterns

To add support for new invoice formats:

1. Update regex patterns in parsing methods
2. Add new test cases in `test_extractor.py`
3. Update business rules if needed
4. Test with sample data

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is provided as-is for educational and business use. Please ensure compliance with DEI's terms of service when using this tool.

## Support

For issues and questions:
1. Check the warnings.log file for detailed error information
2. Review the test output for validation issues
3. Ensure all dependencies are properly installed
4. Verify PDF format matches expected structure
