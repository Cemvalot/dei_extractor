# DEI Extractor

🔌 **A Python tool for extracting and processing Greek DEI (Public Power Corporation) electricity bill data from PDF files.**

Extract structured data from DEI PDF invoices, categorize by billing type (ΦΟΠ/Επαγγελματικό), and filter for Εκαθαριστικός records with duplicate removal.

## ✨ Features

- 📄 **PDF Data Extraction**: Extract structured data from DEI PDF invoices
- 🏷️ **Smart Categorization**: Automatically categorize records as ΦΟΠ or Επαγγελματικό
- 🔍 **Εκαθαριστικός Filtering**: Filter for final settlement records only
- 🚫 **Duplicate Removal**: Remove duplicate records based on key fields
- 📊 **Multiple Formats**: Export to both CSV and Excel formats
- 🛡️ **Data Validation**: Built-in validation and error handling
- 📝 **Comprehensive Logging**: Detailed processing logs for troubleshooting
- 🔄 **Multi-Layout Support**: Automatic detection and parsing of both modern and v2018 DEI layouts

## 🚀 Quick Start

### Prerequisites

**Tesseract OCR** (for processing scanned PDFs):
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-ell

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Installation

```bash
# 1. Clone and navigate to project
cd dei_extractor

# 2. Activate virtual environment
source dei_env_new/bin/activate

# 3. Install package
pip install -e .

# 4. Verify installation
dei-extract --help
```

## 📖 Usage

### Basic Extraction

Extract data from PDF files in a directory:

```bash
# Extract all PDFs from a directory
dei-extract --input "path/to/pdfs" --output-dir "results"

# With verbose logging
dei-extract --input "path/to/pdfs" --output-dir "results" --verbose

# With verbose logging and filtering
dei-extract --input "dei_extractor/data" --verbose --filter
```

### With Εκαθαριστικός Filtering

Extract and filter for settlement records only:

```bash
# Extract and filter in one command
dei-extract --input "path/to/pdfs" --output-dir "results" --filter --verbose
```

### Command Line Options

```bash
dei-extract [input_dir] [--input INPUT] [--output-dir OUTPUT_DIR]
           [--filter] [--verbose] [--config CONFIG]
```

**Arguments:**
- `input_dir` - Directory containing PDF files (positional argument)
- `--input` - Alternative way to specify input directory
- `--output-dir` - Output directory for extracted data (default: `output`)
- `--filter` - Apply Εκαθαριστικός filtering to extracted data
- `--verbose, -v` - Enable verbose logging
- `--config` - Path to configuration file

### Examples

```bash
# Basic extraction
dei-extract "invoices/" --output-dir "extracted_data"

# Extract with filtering
dei-extract "invoices/" --output-dir "filtered_data" --filter

# Using --input argument
dei-extract --input "invoices/" --output-dir "results" --verbose

# Process and filter
dei-extract "invoices/" --output-dir "results" --filter --verbose
```

## 📊 Output Files

When processing PDFs, the following files are generated in your output directory:

### Standard Output Files
- **`ολα.csv`** / **`ολα.xlsx`** - All extracted records
- **`φoπ.csv`** / **`φoπ.xlsx`** - Residential (ΦΟΠ) records only
- **`επαγγελματικα.csv`** / **`επαγγελματικα.xlsx`** - Commercial records only

### With Filtering (--filter option)
- **`filtered.csv`** / **`filtered.xlsx`** - Εκαθαριστικός records only (no duplicates)

### Sample Output Format

```csv
ΑρΠαροχής,ΑρΛογαριασμού,ΗμΈκδοσης,ΠερίοδοςΚατανάλωσης,Ονοματεπώνυμο_Διεύθυνση,Πόλη,Τελευταία,Προηγούμενη,ΣΩΧΒ,ΣυνΩΧΒ,ΚατηγορίαΤιμολογίου,Υποκατηγορία,Εκαθαριστικός
33240992101,1199969431,06/12/2019,31.10.2019-01.12.2019,ΔΗΜΟΣ ΤΡΙΠΟΛΗΣ,ΠΑΡ.ΑΣΤΡΟΣ,70000.0,70000.0,1.0,0.0,Επαγγελματικό,Απλό επαγγελματικό,True
```

## 🐍 Python API

### Basic Usage

```python
from dei_extractor.core.extractor import DEIExtractorEnhanced
from dei_extractor.core.filter import FilterEkatharistikos
from dei_extractor.utils.config import Config

# Create extractor with default configuration
extractor = DEIExtractorEnhanced()

# Process PDF files
pdf_files = ["invoice1.pdf", "invoice2.pdf", "invoice3.pdf"]
df = extractor.process_files(pdf_files)

# Write outputs to directory
extractor.write_outputs(df, output_dir="my_output")

print(f"Extracted {len(df)} records")
```

### With Filtering

```python
from dei_extractor.core.extractor import DEIExtractorEnhanced
from dei_extractor.core.filter import FilterEkatharistikos

# Extract data
extractor = DEIExtractorEnhanced()
df = extractor.process_files(["invoice.pdf"])
extractor.write_outputs(df, "temp_output")

# Filter for Εκαθαριστικός records
filter_tool = FilterEkatharistikos()
filtered_df = filter_tool.process_files([
    "temp_output/ολα.csv",
    "temp_output/φoπ.csv",
    "temp_output/επαγγελματικα.csv"
])

# Write filtered results
filter_tool.write_outputs(filtered_df, "filtered.csv", "filtered.xlsx")

print(f"Filtered to {len(filtered_df)} Εκαθαριστικός records")
```

### Custom Configuration

```python
from dei_extractor.utils.config import Config
from dei_extractor.core.extractor import DEIExtractorEnhanced

# Create custom configuration
config = Config()  # Uses default settings

# Create extractor with custom config
extractor = DEIExtractorEnhanced(config)

# Process files
df = extractor.process_files(["invoice.pdf"])
print(f"Processed {len(df)} records")
```

## 📋 Data Fields

The extracted data includes the following fields:

| Field | Description | Example |
|-------|-------------|---------|
| `ΑρΠαροχής` | Supply number | 33240992101 |
| `ΑρΛογαριασμού` | Account number | 1199969431 |
| `ΗμΈκδοσης` | Issue date | 06/12/2019 |
| `ΠερίοδοςΚατανάλωσης` | Billing period | 31.10.2019-01.12.2019 |
| `Ονοματεπώνυμο_Διεύθυνση` | Name and address | ΔΗΜΟΣ ΤΡΙΠΟΛΗΣ |
| `Πόλη` | City | ΠΑΡ.ΑΣΤΡΟΣ |
| `Τελευταία` | Current reading | 70000.0 |
| `Προηγούμενη` | Previous reading | 70000.0 |
| `ΣΩΧΒ` | Total consumption | 1.0 |
| `ΣυνΩΧΒ` | Consumption difference | 0.0 |
| `ΚατηγορίαΤιμολογίου` | Billing category | Επαγγελματικό |
| `Υποκατηγορία` | Billing subcategory | Απλό επαγγελματικό |
| `Εκαθαριστικός` | Final settlement flag | True |

## 📋 Supported Layouts

The DEI Extractor supports automatic detection and parsing of two different DEI bill layouts:

### Modern Layout
- **Detection**: Standard DEI bill format with 3-row block structure
- **Features**: Full support for all fields including meter readings, categories, and subcategories
- **Compatibility**: Current DEI bill format

### v2018 Layout (Older Format)
- **Detection**: Identified by anchors like "Ο λογαριασμός σας συνοπτικά", "Κωδικός Ηλεκτρονικής Πληρωμής", "Κατανάλωση Ηλεκτρικής Ενέργειας"
- **Features**: Extracts all available fields including:
  - Supply number, issue date, consumption period
  - kWh consumption, total amount, RF payment code
  - Customer details, address, city
  - Account type and category classification
- **Compatibility**: Older DEI bill format from 2018 and earlier

Both layouts return the same standardized field names, ensuring compatibility with existing filters, exports, and CLI functionality.

## 🔧 Development

### Setup Development Environment

```bash
# 1. Activate virtual environment
source dei_env_new/bin/activate

# 2. Install in development mode
pip install -e .

# 3. Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
python -m pytest dei_extractor/tests/ -v

# Run with verbose output
python -m pytest dei_extractor/tests/ -v -s

# Run specific test file
python -m pytest dei_extractor/tests/test_extract_dei_final_comprehensive.py -v
```

### Code Quality

```bash
# Format code with black
black dei_extractor/

# Sort imports with isort
isort dei_extractor/

# Run pre-commit checks
pre-commit run --all-files
```

## 🆘 Troubleshooting

### Common Issues

#### 1. **"Command not found: dei-extract"**
```bash
# Make sure the virtual environment is activated
source dei_env_new/bin/activate

# Reinstall the package
pip install -e .

# Verify installation
dei-extract --help
```

#### 2. **"No PDF files found"**
```bash
# Check if PDF files exist in the directory
ls -la path/to/pdfs/*.pdf

# Try with absolute path
dei-extract --input "/full/path/to/pdf/directory"

# Check directory permissions
ls -ld path/to/pdfs/
```

#### 3. **OCR Issues (for scanned PDFs)**
```bash
# Check if Tesseract is installed
tesseract --version

# Install Greek language pack
# macOS: brew install tesseract-lang
# Ubuntu: sudo apt install tesseract-ocr-ell

# Test Tesseract manually
tesseract sample.pdf output -l ell+eng
```

#### 4. **Processing Errors**
```bash
# Run with verbose logging to see details
dei-extract --input "pdfs/" --output-dir "results" --verbose

# Check for permission issues
chmod 755 path/to/pdf/directory
chmod 644 path/to/pdf/directory/*.pdf
```

#### 5. **Empty Output Files**
- Verify PDFs contain extractable text (not just images)
- Try with `--verbose` to see processing details
- Check if Tesseract is installed for scanned PDFs
- Ensure PDFs are valid DEI electricity bills

### Performance Tips

- **Large Files**: Process PDFs in smaller batches
- **Memory Issues**: Close other applications while processing
- **Slow Processing**: Disable OCR for text-based PDFs (if possible)

### Getting Help

```bash
# View detailed help
dei-extract --help

# Check installed version
pip show dei-extractor

# View processing logs (if available)
ls -la *.log
```

## 📄 License

This project is licensed under the MIT License.

---

**🎉 DEI Extractor - Ready for processing Greek electricity bills!**
