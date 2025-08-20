# DEI Extractor

A comprehensive Python package for extracting and processing DEI (Public Power Corporation) PDF invoice data with advanced parsing, filtering, and data validation capabilities.

## 🚀 Quick Start

### Prerequisites

1. **Install Tesseract OCR** (for scanned PDFs):
   ```bash
   # macOS
   brew install tesseract tesseract-lang

   # Ubuntu/Debian
   sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-ell

   # Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Verify Tesseract**:
   ```bash
   tesseract --version
   ```

### Installation

```bash
# 1. Navigate to project directory
cd /Users/cemvalot/Desktop/dei_extractor

# 2. Activate virtual environment
source dei_env_new/bin/activate

# 3. Install package
pip install -e .

# 4. Verify installation
dei-extract --help
```

### Quick Start Commands

#### Extract Data from PDFs:
```bash
# Basic extraction
dei-extract --input "dei_extractor/data/*.pdf"

# With custom options
dei-extract --input "dei_extractor/data/*.pdf" \
           --confidence 0.95 \
           --log-level INFO

# Process specific files
dei-extract --input "path/to/invoices/*.pdf"
```

#### Filter Extracted Data:
```bash
# Basic filtering
dei-filter --inputs ολα.csv,φoπ.csv,επαγγελματικα.csv

# Custom output files
dei-filter --inputs "*.csv" \
          --out-csv filtered_data.csv \
          --out-xlsx filtered_data.xlsx
```

#### Complete Workflow:
```bash
# 1. Extract data
dei-extract --input "dei_extractor/data/*.pdf" --log-level INFO

# 2. Check output files
ls -la *.csv *.xlsx

# 3. Filter data
dei-filter --inputs "ολα.csv,φoπ.csv,επαγγελματικα.csv"

# 4. View results
head -5 filtered.csv
```

## 📊 API Usage

### Basic API Usage

```python
from dei_extractor import DEIExtractorEnhanced, FilterEkatharistikos, Config

# Configure extraction
config = Config(
    confidence_threshold=0.90,
    enable_ocr=True,
    sort_by_αρ_παροχής=True
)

# Extract data from PDFs
extractor = DEIExtractorEnhanced(config)
df = extractor.process_files(["dei_extractor/data/*.pdf"])

print(f"Extracted {len(df)} records")

# Filter data
filter_tool = FilterEkatharistikos()
filtered_df = filter_tool.process_files(["ολα.csv", "φoπ.csv"])

print(f"Filtered to {len(filtered_df)} records")
```

### Advanced API Usage

```python
from dei_extractor import DEIExtractorEnhanced, FilterEkatharistikos, Config
from pathlib import Path

# Custom configuration
config = Config(
    input_pattern="*.pdf",
    output_dir=Path("./output"),
    confidence_threshold=0.95,
    enable_ocr=True,
    enable_deduplication=True,
    log_level="DEBUG"
)

# Create extractor with custom config
extractor = DEIExtractorEnhanced(config)

# Process files with detailed logging
pdf_files = ["file1.pdf", "file2.pdf", "file3.pdf"]
df = extractor.process_files(pdf_files)

# Access individual processing methods
if not df.empty:
    # Write outputs
    extractor.write_outputs(df)

    # Get specific categories
    fop_df = df[df['ΚατηγορίαΤιμολογίου'] == 'ΦΟΠ']
    epag_df = df[df['ΚατηγορίαΤιμολογίου'] == 'Επαγγελματικό']

    print(f"ΦΟΠ records: {len(fop_df)}")
    print(f"Επαγγελματικό records: {len(epag_df)}")

# Advanced filtering
filter_tool = FilterEkatharistikos(config)

# Process multiple input files
input_files = ["ολα.csv", "φoπ.csv", "επαγγελματικα.csv"]
filtered_df = filter_tool.process_files(input_files)

# Apply custom transformations
if not filtered_df.empty:
    # Remove duplicates
    filtered_df = filter_tool.remove_duplicates(filtered_df)

    # Parse dates
    filtered_df = filter_tool.parse_dates(filtered_df)

    # Drop sensitive columns
    filtered_df = filter_tool.drop_afm_column(filtered_df)

    # Write custom outputs
    filter_tool.write_outputs(filtered_df, "custom_filtered.csv", "custom_filtered.xlsx")
```

### Configuration Management

```python
from dei_extractor import Config
import os

# Environment-based configuration
os.environ['DEI_CONFIDENCE_THRESHOLD'] = '0.95'
os.environ['DEI_ENABLE_OCR'] = 'true'
os.environ['DEI_LOG_LEVEL'] = 'DEBUG'

# Load configuration
config = Config()

print(f"Confidence threshold: {config.confidence_threshold}")
print(f"OCR enabled: {config.enable_ocr}")
print(f"Log level: {config.log_level}")

# Custom configuration
custom_config = Config(
    confidence_threshold=0.98,
    enable_ocr=False,
    max_file_size_mb=50,
    output_formats=["csv"],
    encoding="utf-8"
)
```

### Error Handling

```python
from dei_extractor import DEIExtractorEnhanced, ValidationError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

try:
    extractor = DEIExtractorEnhanced()
    df = extractor.process_files(["nonexistent.pdf"])
except ValidationError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Processing error: {e}")
    logging.error(f"Error details: {e}", exc_info=True)
```

## 🛠️ Development

### Development Setup

```bash
# 1. Clone and setup
cd /Users/cemvalot/Desktop/dei_extractor
source dei_env_new/bin/activate

# 2. Install with development dependencies
pip install -e ".[dev,docs,test]"

# 3. Install pre-commit hooks
make pre-commit

# 4. Verify setup
make validate
```

### Development Commands

#### Code Quality:
```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# All quality checks
make dev-test
```

#### Testing:
```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run only fast tests
make test-fast

# Run specific test categories
pytest dei_extractor/tests/ -m "unit"
pytest dei_extractor/tests/ -m "integration"
```

#### Building and Distribution:
```bash
# Build package
make build

# Clean build artifacts
make clean

# Release checks
make release-check
```

### Development Workflow

```bash
# 1. Complete development setup
make setup

# 2. Run development tests
make dev-test

# 3. Make changes to code...

# 4. Format and check code
make format
make lint
make type-check

# 5. Run tests
make test

# 6. Build and test
make build
make validate
```

### Testing Examples

#### Unit Testing:
```python
import pytest
from dei_extractor import DEIExtractorEnhanced, Config

def test_extractor_initialization():
    config = Config(confidence_threshold=0.90)
    extractor = DEIExtractorEnhanced(config)
    assert extractor.config.confidence_threshold == 0.90

def test_filter_processing():
    from dei_extractor import FilterEkatharistikos
    import pandas as pd

    # Create test data
    test_data = pd.DataFrame({
        'ΑρΠαροχής': ['1234567890', '1234567891'],
        'Εκαθαριστικός': ['True', 'False']
    })

    filter_tool = FilterEkatharistikos()
    result = filter_tool.filter_ekatharistikos(test_data)

    assert len(result) == 1  # Only True values should remain
```

#### Integration Testing:
```python
import pytest
from dei_extractor import DEIExtractorEnhanced, FilterEkatharistikos

def test_full_workflow():
    # Test complete extraction and filtering workflow
    extractor = DEIExtractorEnhanced()
    filter_tool = FilterEkatharistikos()

    # Process test files
    df = extractor.process_files(["test_data/sample.pdf"])
    assert not df.empty

    # Filter results
    filtered_df = filter_tool.process_files(["ολα.csv"])
    assert len(filtered_df) <= len(df)
```

### Debugging

#### Enable Debug Logging:
```bash
# Command line
dei-extract --input "*.pdf" --log-level DEBUG

# Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Performance Profiling:
```bash
# Profile execution
make profile

# Memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

#### Common Debug Commands:
```bash
# Check dependencies
make check-deps

# Check OCR
make check-ocr

# Validate project structure
make validate

# View logs
tail -f warnings.log

# Clear logs
make logs-clear
```

### Contributing

#### Code Style:
- Follow PEP 8 guidelines
- Use Black for code formatting
- Use isort for import sorting
- Add type hints to all functions

#### Testing:
- Write tests for new features
- Maintain 100% test coverage
- Include edge case testing
- Add integration tests for workflows

#### Documentation:
- Update docstrings for new functions
- Add examples to README
- Update API documentation
- Include usage examples

#### Git Workflow:
```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes and test
make dev-test

# 3. Commit with conventional messages
git commit -m "feat: add new extraction feature"

# 4. Push and create pull request
git push origin feature/new-feature
```

## 📈 Performance Tips

### Optimization:
```python
# Use batch processing for large files
config = Config(max_file_size_mb=100)

# Disable OCR for text-based PDFs
config = Config(enable_ocr=False)

# Use specific output formats
config = Config(output_formats=["csv"])
```

### Memory Management:
```python
# Process files in batches
for batch in file_batches:
    df = extractor.process_files(batch)
    # Process batch results
    del df  # Free memory
```

## 🎯 Expected Output

### Files Generated:
- `ολα.csv` / `ολα.xlsx` - All extracted records
- `φoπ.csv` / `φoπ.xlsx` - Residential (ΦΟΠ) records only
- `επαγγελματικα.csv` / `επαγγελματικα.xlsx` - Commercial records only
- `warnings.log` - Processing log file

### Sample Output:
```csv
ΑρΠαροχής,ΑρΛογαριασμού,ΗμΈκδοσης,ΠερίοδοςΚατανάλωσης,Ονοματεπώνυμο_Διεύθυνση,Πόλη,Τελευταία,Προηγούμενη,ΣΩΧΒ,ΣυνΩΧΒ,ΚατηγορίαΤιμολογίου,Υποκατηγορία,Εκαθαριστικός
33240992101,1199969431,06/12/2019,31.10.2019-01.12.2019,ΔΗΜΟΣ ΤΡΙΠΟΛΗΣ,ΠΑΡ.ΑΣΤΡΟΣ,70000.0,70000.0,1.0,0.0,Επαγγελματικό,Απλό επαγγελματικό,True
```

## 🆘 Troubleshooting

### Common Issues:

#### 1. **"Command not found: dei-extract"**
```bash
# Reinstall package
pip install -e .
```

#### 2. **"No PDF files found"**
```bash
# Check file existence
ls -la *.pdf

# Use absolute path
dei-extract --input "/full/path/to/*.pdf"
```

#### 3. **OCR Issues**
```bash
# Check Tesseract
tesseract --version

# Test OCR manually
tesseract test.pdf stdout -l ell+eng
```

#### 4. **Permission Errors**
```bash
# Fix permissions
chmod 644 *.pdf
```

### Getting Help:
```bash
# View logs
tail -f warnings.log

# Run validation
make validate

# Check dependencies
make check-deps

# Test OCR
make check-ocr
```

---

**🎉 The DEI Extractor is now ready for production use with comprehensive documentation and development tools!**
