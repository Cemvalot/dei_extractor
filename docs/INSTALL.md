# DEI Extractor Installation Guide

Complete installation guide for the DEI PDF Invoice Extractor - a tool for extracting and processing Greek DEI electricity bill data from PDF files.

## Prerequisites

### System Requirements
- **Operating System**: macOS, Linux (Ubuntu/Debian), or Windows
- **Python**: Version 3.8 or higher (tested with 3.11+)
- **Memory**: At least 4GB RAM (8GB recommended for large PDF processing)
- **Storage**: At least 1GB free space for temporary files

### Required Software

1. **Python 3.8+** with pip
2. **Tesseract OCR** (for processing scanned PDFs)
3. **Git** (for cloning the repository)

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

### Step 3: Clone and Set Up the Project

```bash
# Clone the repository (or navigate to existing project)
cd dei_extractor

# Activate the existing virtual environment
source dei_env_new/bin/activate

# Or create a new virtual environment if needed
# python3 -m venv dei_env_new
# source dei_env_new/bin/activate  # On macOS/Linux
# dei_env_new\Scripts\activate     # On Windows
```

### Step 4: Install the Package

```bash
# Install the package in development mode
pip install -e .

# This will install all required dependencies automatically
```

### Step 5: Verify Installation

```bash
# Test the CLI command
dei-extract --help

# Expected output: usage instructions for the CLI
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

### 1. Test CLI Installation

```bash
# Verify the CLI is working
dei-extract --help

# Expected output: Help text with all command options
```

### 2. Test with Sample Data (Optional)

```bash
# If you have sample PDF files, test the extraction
dei-extract --input "dei_extractor/data" --output-dir "test_output" --verbose

# This will process any PDFs in the test data directory
```

### 3. Run Project Tests (For Developers)

```bash
# Run the test suite
python -m pytest dei_extractor/tests/ -v

# Expected output: All tests should pass
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
# Activate virtual environment
source dei_env_new/bin/activate

# Basic extraction - process all PDFs in a directory
dei-extract --input "path/to/invoices" --output-dir "results"

# Using positional argument
dei-extract "path/to/invoices" --output-dir "results"

# With verbose logging
dei-extract --input "path/to/invoices" --output-dir "results" --verbose
```

### Step 2: Extract and Filter in One Step

```bash
# Extract and filter for Εκαθαριστικός records
dei-extract --input "path/to/invoices" --output-dir "results" --filter --verbose
```

### Step 3: Check Generated Output Files

After processing, you'll find these files in your output directory:

**Standard Output:**
- `ολα.csv` / `ολα.xlsx` - All extracted records
- `φoπ.csv` / `φoπ.xlsx` - Residential invoices (ΦΟΠ)
- `επαγγελματικα.csv` / `επαγγελματικα.xlsx` - Commercial invoices

**With Filtering (--filter option):**
- `filtered.csv` / `filtered.xlsx` - Εκαθαριστικός records only (no duplicates)

### Step 4: Review Results

The CLI provides detailed output including:
- Total records extracted
- Records by category (ΦΟΠ/Επαγγελματικό)
- Filtering statistics (if using --filter)
- Processing warnings and errors

## Complete Workflow Examples

### Basic Extraction
```bash
# 1. Activate environment
source dei_env_new/bin/activate

# 2. Extract data from PDFs
dei-extract "invoices/" --output-dir "extracted_data" --verbose

# 3. Check results
ls -la extracted_data/
```

### Extract and Filter
```bash
# 1. Activate environment
source dei_env_new/bin/activate

# 2. Extract and filter in one command
dei-extract "invoices/" --output-dir "filtered_data" --filter --verbose

# 3. Check results
ls -la filtered_data/
head -5 filtered_data/filtered.csv
```

## Support

If you encounter issues:

1. Check the `warnings.log` file for detailed error information
2. Run the test suite: `python3 simple_test.py`
3. Verify all dependencies are installed correctly
4. Check that your PDF format matches the expected structure

For additional help, refer to the troubleshooting section in README.md.
