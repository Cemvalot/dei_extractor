# DEI Extractor Installation Guide

This guide provides step-by-step instructions for installing and setting up the DEI PDF Invoice Extractor.

## Prerequisites

### System Requirements
- **Operating System**: macOS, Linux (Ubuntu/Debian), or Windows
- **Python**: Version 3.11 or higher
- **Memory**: At least 4GB RAM (8GB recommended for large PDF processing)
- **Storage**: At least 1GB free space for temporary files

### Required Software

1. **Python 3.11+**
2. **Tesseract OCR** (for scanned PDFs)
3. **pip** (Python package manager)

## Installation Steps

### Step 1: Install Python

#### macOS
```bash
# Using Homebrew (recommended)
brew install python@3.11

# Or download from python.org
# https://www.python.org/downloads/
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

#### Windows
1. Download Python 3.11+ from https://www.python.org/downloads/
2. Run the installer and check "Add Python to PATH"
3. Verify installation: `python --version`

### Step 2: Install Tesseract OCR

#### macOS
```bash
# Install Tesseract and language packs
brew install tesseract tesseract-lang

# Verify installation
tesseract --version
```

#### Ubuntu/Debian
```bash
# Install Tesseract and Greek language pack
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-ell

# Verify installation
tesseract --version
```

#### Windows
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to PATH environment variable
4. Verify installation: `tesseract --version`

### Step 3: Set Up Python Environment

```bash
# Create a virtual environment (recommended)
python3 -m venv dei_extractor_env

# Activate the virtual environment
# On macOS/Linux:
source dei_extractor_env/bin/activate

# On Windows:
# dei_extractor_env\Scripts\activate
```

### Step 4: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### Step 5: Verify Installation

```bash
# Test the core logic (no external dependencies required)
python3 simple_test.py

# Expected output should show all tests passing
```

## Configuration

### Tesseract Configuration

The script automatically detects Tesseract installation. If you encounter issues:

1. **Check Tesseract PATH**:
   ```bash
   which tesseract  # macOS/Linux
   where tesseract  # Windows
   ```

2. **Verify Greek Language Pack**:
   ```bash
   tesseract --list-langs
   # Should include 'ell' (Greek)
   ```

3. **Test OCR with Greek Text**:
   ```bash
   echo "ΔΕΗ Τιμολόγιο" | tesseract stdin stdout -l ell
   ```

### Environment Variables (Optional)

You can set these environment variables for custom configuration:

```bash
# Set Tesseract path (if not in PATH)
export TESSERACT_PATH="/usr/local/bin/tesseract"

# Set OCR language (default: ell+eng)
export OCR_LANGUAGE="ell+eng"

# Set log level (default: INFO)
export LOG_LEVEL="DEBUG"
```

## Testing the Installation

### 1. Run Core Logic Tests

```bash
python3 simple_test.py
```

Expected output:
```
DEI Extractor Core Logic Tests
========================================
Testing text normalization...
✓ Text normalization test passed
Testing invoice header detection...
✓ Invoice header detection test passed
...
ALL TESTS COMPLETED
```

### 2. Create Sample PDF (Optional)

```bash
# Install reportlab for PDF creation
pip install reportlab

# Create sample PDF
python3 create_sample_pdf.py
```

### 3. Test with Sample PDF

```bash
# Process the sample PDF
python3 extract_dei.py --input "sample_dei_invoice.pdf"
```

## Troubleshooting

### Common Issues

#### 1. "tesseract: command not found"
**Solution**: Install Tesseract and ensure it's in your PATH
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt install tesseract-ocr
```

#### 2. "No module named 'pandas'"
**Solution**: Install Python dependencies
```bash
pip install -r requirements.txt
```

#### 3. "Greek language pack not found"
**Solution**: Install Greek language pack
```bash
# macOS
brew install tesseract-lang

# Ubuntu/Debian
sudo apt install tesseract-ocr-ell
```

#### 4. "Permission denied" errors
**Solution**: Check file permissions and use virtual environment
```bash
# Create and activate virtual environment
python3 -m venv dei_env
source dei_env/bin/activate
pip install -r requirements.txt
```

#### 5. OCR quality issues
**Solutions**:
- Ensure PDF pages are properly scanned (300+ DPI)
- Check that Greek language pack is installed
- Try different OCR settings in the code

### Performance Optimization

#### For Large PDF Files
1. **Increase memory allocation**:
   ```bash
   export PYTHONMALLOC=malloc
   ```

2. **Process files in batches**:
   ```bash
   # Process files in smaller groups
   python3 extract_dei.py --input "batch1/*.pdf"
   python3 extract_dei.py --input "batch2/*.pdf"
   ```

3. **Use SSD storage** for temporary files

#### For Better OCR Results
1. **Pre-process PDFs**:
   - Ensure good scan quality
   - Use black and white scanning
   - Avoid compression artifacts

2. **Adjust OCR settings** in the code:
   ```python
   # In extract_dei.py, modify OCR configuration
   text = pytesseract.image_to_string(
       images[0], 
       lang='ell+eng',
       config='--psm 6 --oem 3'  # Try different PSM modes
   )
   ```

## Usage Instructions

### Step 1: Extract Data from PDF Files

```bash
# Activate virtual environment (if using one)
source dei_env_new/bin/activate

# Process PDF files
python3 extract_dei_final.py --input "your_invoices/*.pdf"

# Example with specific file
python3 extract_dei_final.py --input "4J05_2019-12-01-1 1.pdf"
```

### Step 2: Check Generated Output Files

After processing, you'll get these files:
- `ολα.csv` / `ολα.xlsx` - All records
- `φoπ.csv` / `φoπ.xlsx` - Residential invoices (ΦΟΠ)
- `επαγγελματικα.csv` / `επαγγελματικα.xlsx` - Commercial invoices
- `warnings.log` - Log file with issues

### Step 3: Filter by Εκαθαριστικός (Optional)

To filter and keep only records where `Εκαθαριστικός = True`:

```bash
# Make sure virtual environment is activated
source dei_env_new/bin/activate

# Run the filter script
python3 filter_ekatharistikos.py
```

This will create:
- `filtered.csv` - Filtered data in CSV format
- `filtered.xlsx` - Filtered data in Excel format

### Step 4: Review Results

Check the console output for:
- Total records extracted
- Records needing review (confidence < 90%)
- Processing warnings
- Filtering statistics

## Complete Workflow Example

```bash
# 1. Activate environment
source dei_env_new/bin/activate

# 2. Extract data from PDFs
python3 extract_dei_final.py --input "*.pdf"

# 3. Filter by Εκαθαριστικός (optional)
python3 filter_ekatharistikos.py

# 4. Check results
ls -la *.csv *.xlsx
```

## Support

If you encounter issues:

1. Check the `warnings.log` file for detailed error information
2. Run the test suite: `python3 simple_test.py`
3. Verify all dependencies are installed correctly
4. Check that your PDF format matches the expected structure

For additional help, refer to the troubleshooting section in README.md.
