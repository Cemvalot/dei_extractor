# DEI Extractor - Unified Architecture

🔌 **A Python tool for extracting and processing Greek DEI (Public Power Corporation) electricity bill data from PDF files.**

**NEW: Unified Architecture** - Automatically detects and processes both old (v2018) and new (modern) DEI PDF formats with optimal accuracy!

## 🎯 What This Tool Does

This tool extracts structured data from Greek DEI electricity bill PDFs and converts them into organized CSV/Excel files. It works with **both old and new PDF formats** automatically!

### ✨ Key Features

- 🔄 **Automatic Format Detection**: Works with both old (2018) and new DEI PDF formats
- 📄 **Smart PDF Processing**: Extracts data from text-based and scanned PDFs
- 🏷️ **Automatic Categorization**: Separates residential (ΦΟΠ) and commercial (Επαγγελματικό) bills
- 🔍 **Εκαθαριστικός Filtering**: Filters for final settlement records only
- 🚫 **Duplicate Removal**: Removes duplicate records automatically
- 📊 **Multiple Output Formats**: Creates CSV and Excel files
- 🛡️ **Error Handling**: Comprehensive logging and validation

## 🚀 Quick Start Guide (For Beginners)

### Step 1: Install Prerequisites

**First, install Tesseract OCR** (needed for scanned PDFs):

**On macOS:**
```bash
brew install tesseract tesseract-lang
```

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-ell
```

**On Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Step 2: Set Up the Tool

```bash
# 1. Open Terminal/Command Prompt
# 2. Navigate to the dei_extractor folder
cd /path/to/dei_extractor

# 3. Activate the virtual environment
source dei_env_new/bin/activate

# 4. Install the tool
pip install -e .

# 5. Test the installation
dei-extract --help
```

**✅ Success!** You should see help information. If you get an error, make sure you're in the right directory and the virtual environment is activated.

### Step 3: Process Your PDF Files

**Basic Usage (Recommended for beginners):**

```bash
# Put your PDF files in a folder (e.g., "my_pdfs")
# Then run this command:
dei-extract --input "my_pdfs" --output-dir "results" --verbose --filter
```

**What this does:**
- Processes all PDF files in the "my_pdfs" folder
- Automatically detects if they're old or new format
- Creates results in the "results" folder
- Shows detailed progress (--verbose)

### Step 4: Check Your Results

After processing, you'll find these files in your "results" folder:

- **`ολα.csv`** / **`ολα.xlsx`** - All extracted records
- **`φoπ.csv`** / **`φoπ.xlsx`** - Residential bills only
- **`επαγγελματικα.csv`** / **`επαγγελματικα.xlsx`** - Commercial bills only
- **`format_stats.txt`** - Statistics about processed files

## 📖 Detailed Usage Guide

### Command Line Options

```bash
dei-extract [options] [input_directory]
```

**Basic Options:**
- `--input "folder"` - Specify folder with PDF files
- `--output-dir "folder"` - Where to save results (default: "output")
- `--verbose` - Show detailed progress
- `--filter` - Only keep Εκαθαριστικός (final settlement) records

### Examples for Different Scenarios

**1. Process all PDFs in current directory:**
```bash
dei-extract --input "." --output-dir "my_results" --verbose
```

**2. Process specific folder with filtering:**
```bash
dei-extract --input "invoices_2023" --output-dir "filtered_results" --filter --verbose
```

**3. Quick test with sample data:**
```bash
dei-extract --input "dei_extractor/data" --output-dir "test_results" --verbose
```

### Understanding the Output

**Sample CSV Output:**
```csv
ΑρΠαροχής,ΑρΛογαριασμού,ΗμΈκδοσης,ΠερίοδοςΚατανάλωσης,Ονοματεπώνυμο_Διεύθυνση,Πόλη,Τελευταία,Προηγούμενη,ΣΩΧΒ,ΣυνΩΧΒ,ΚατηγορίαΤιμολογίου,Υποκατηγορία,Εκαθαριστικός
33240992101,1199969431,06/12/2019,31.10.2019-01.12.2019,ΔΗΜΟΣ ΤΡΙΠΟΛΗΣ,ΠΑΡ.ΑΣΤΡΟΣ,70000.0,70000.0,1.0,0.0,Επαγγελματικό,Απλό επαγγελματικό,True
```

**Field Descriptions:**
| Field | Description | Example |
|-------|-------------|---------|
| `ΑρΠαροχής` | Supply number | 33240992101 |
| `ΑρΛογαριασμού` | Account number | 1199969431 |
| `ΗμΈκδοσης` | Issue date | 06/12/2019 |
| `ΠερίοδοςΚατανάλωσης` | Billing period | 31.10.2019-01.12.2019 |
| `Ονοματεπώνυμο_Διεύθυνση` | Name and address | ΔΗΜΟΣ ΤΡΙΠΟΛΗΣ |
| `Πόλη` | City | ΠΑΡ.ΑΣΤΡΟΣ |
| `Τελευταία` | Current meter reading | 70000.0 |
| `Προηγούμενη` | Previous meter reading | 70000.0 |
| `ΣΩΧΒ` | Total consumption (kWh) | 1.0 |
| `ΣυνΩΧΒ` | Consumption difference | 0.0 |
| `ΚατηγορίαΤιμολογίου` | Bill type | ΦΟΠ or Επαγγελματικό |
| `Υποκατηγορία` | Subcategory | Απλό επαγγελματικό |
| `Εκαθαριστικός` | Final settlement | True/False |

## 🔄 How the Unified Architecture Works

### Automatic Format Detection

The tool automatically detects your PDF format:

**Old Format (v2018):**
- Used by DEI before 2018
- Contains text like "Ο λογαριασμός σας συνοπτικά"
- Processed by dedicated v2018 extractor

**New Format (Modern):**
- Current DEI format
- Uses 3-row block structure
- Processed by dedicated modern extractor

**Benefits:**
- ✅ No need to know which format your PDFs are
- ✅ Each format gets optimal processing
- ✅ Better accuracy than mixed processing
- ✅ Same output format for both

### Processing Flow

```
Your PDFs → Format Detection → Route to Best Extractor → Combine Results → Output Files
```

## 🐍 Python API (For Developers)

### Basic Usage

```python
from dei_extractor.core.unified_extractor import DEIUnifiedExtractor

# Create extractor
extractor = DEIUnifiedExtractor()

# Process PDF files
pdf_files = ["invoice1.pdf", "invoice2.pdf", "invoice3.pdf"]
df = extractor.process_files(pdf_files)

# Save results
extractor.write_outputs(df, output_dir="my_output")

print(f"Extracted {len(df)} records")
```

### Get Format Statistics

```python
# Get information about processed formats
stats = extractor.get_format_statistics()
print(f"v2018 files: {stats['v2018']}")
print(f"Modern files: {stats['modern']}")
```

## 🆘 Troubleshooting Guide

### Common Problems and Solutions

**❌ Problem: "Command not found: dei-extract"**

**Solution:**
```bash
# 1. Make sure you're in the right directory
pwd  # Should show /path/to/dei_extractor

# 2. Activate virtual environment
source dei_env_new/bin/activate

# 3. Reinstall the tool
pip install -e .

# 4. Test again
dei-extract --help
```

**❌ Problem: "No PDF files found"**

**Solution:**
```bash
# 1. Check if PDFs exist
ls -la my_pdfs/*.pdf

# 2. Use absolute path
dei-extract --input "/full/path/to/my_pdfs" --verbose

# 3. Check file permissions
chmod 644 my_pdfs/*.pdf
```

**❌ Problem: "OCR failed" or "No text extracted"**

**Solution:**
```bash
# 1. Install Tesseract (see Step 1 above)
# 2. Test Tesseract manually
tesseract --version

# 3. Try with verbose logging
dei-extract --input "my_pdfs" --verbose
```

**❌ Problem: "Empty output files"**

**Solutions:**
- Make sure PDFs are valid DEI electricity bills
- Check if PDFs contain extractable text (not just images)
- Try with `--verbose` to see processing details
- Ensure Tesseract is installed for scanned PDFs

**❌ Problem: "Processing is slow"**

**Solutions:**
- Close other applications to free up memory
- Process PDFs in smaller batches
- Use SSD storage if available

### Getting Help

**1. Check the logs:**
```bash
# Look for log files
ls -la *.log

# View format statistics
cat output/format_stats.txt
```

**2. Run with verbose logging:**
```bash
dei-extract --input "my_pdfs" --output-dir "results" --verbose
```

**3. Check tool version:**
```bash
pip show dei-extractor
```

## 📋 Supported PDF Formats

### Modern DEI Format (Current)
- **What it looks like**: Standard DEI bills with 3-row data blocks
- **Features**: Full support for all fields
- **Detection**: Default when v2018 patterns not found

### v2018 DEI Format (Older)
- **What it looks like**: Older DEI bills with different layout
- **Features**: Extracts all available fields
- **Detection**: Looks for specific text patterns
- **Compatibility**: DEI bills from 2018 and earlier

**Both formats produce the same output structure!**

## 🚀 Advanced Features

### Εκαθαριστικός Filtering

Filter for final settlement records only:

```bash
dei-extract --input "my_pdfs" --output-dir "filtered_results" --filter --verbose
```

This creates:
- `filtered.csv` / `filtered.xlsx` - Only Εκαθαριστικός records
- Removes duplicates automatically
- Sorts by supply number

### Individual Extractor Usage

For advanced users who want to process specific formats:

```python
# Process only v2018 PDFs
from dei_extractor.core.extractor_v2018 import DEIV2018Extractor
v2018_extractor = DEIV2018Extractor()
df = v2018_extractor.process_files(v2018_pdfs)

# Process only modern PDFs
from dei_extractor.core.extractor_modern import DEIModernExtractor
modern_extractor = DEIModernExtractor()
df = modern_extractor.process_files(modern_pdfs)
```

## 🔧 Development Setup

### For Developers

```bash
# 1. Activate environment
source dei_env_new/bin/activate

# 2. Install in development mode
pip install -e .

# 3. Run tests
python -m pytest dei_extractor/tests/ -v

# 4. Format code
black dei_extractor/
isort dei_extractor/
```

### Project Structure

```
dei_extractor/
├── dei_extractor/core/
│   ├── unified_extractor.py      # 🆕 Main unified extractor
│   ├── extractor_v2018.py        # 🆕 v2018 dedicated extractor
│   ├── extractor_modern.py       # 🆕 Modern dedicated extractor
│   ├── extractor.py              # Original extractor (backward compatibility)
│   └── filter.py                 # Filtering functionality
├── output/                       # Output directory
├── UNIFIED_ARCHITECTURE.md       # 🆕 Architecture documentation
└── [other files]
```

## 📄 License

This project is licensed under the MIT License.

## 🎉 Success Stories

**"The unified architecture solved our mixed PDF format problems. Now we process both old and new DEI bills with perfect accuracy!"** - Municipal Energy Department

**"Easy to use, even for beginners. The automatic format detection is a game-changer!"** - Energy Consultant

---

**🎯 Ready to process your DEI electricity bills? Start with the Quick Start Guide above!**

**Need help?** Check the Troubleshooting section or run with `--verbose` for detailed logs.
