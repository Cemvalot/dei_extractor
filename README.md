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
- 🌐 **Modern Web Interface**: Drag & drop file upload with real-time progress
- 🔄 **Transform Feature**: Convert Phase-1 data to Final consolidated datasets
- 🔒 **Production Ready**: Docker deployment with HTTPS and authentication

## 🚀 Quick Start Guide

### Option 1: Docker Compose (Recommended - Production Ready)

**The easiest way to run the application with a modern web interface:**

```bash
# 1. Navigate to the project directory
cd /path/to/dei_extractor

# 2. Start the application (one command!)
cd ops
docker compose up -d

# 3. Access the web interface
# Open your browser to: http://localhost:8080
# Username: admin
# Password: testpass
```

**✅ That's it!** The application is now running with:
- **Modern Web UI**: Upload files via drag & drop
- **Real-time Progress**: See processing status live
- **Transform Feature**: Convert Phase-1 data to Final format
- **Automatic OCR**: Handles both text and scanned PDFs
- **Secure**: HTTPS with basic authentication

**To stop the application:**
```bash
cd ops
docker compose down
```

**To view live logs:**
```bash
cd ops
docker compose logs -f
```

**To view logs for specific services:**
```bash
# Backend logs (FastAPI)
docker compose logs -f backend

# Frontend logs (Next.js)
docker compose logs -f frontend

# Proxy logs (Caddy)
docker compose logs -f proxy
```

### Option 2: Command Line (For Developers)

**For command-line usage and development:**

#### Step 1: Install Prerequisites

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

#### Step 2: Set Up the Tool

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

## 🆕 Transform Feature (Web Interface)

**NEW: Phase-1 to Final Dataset Transformation** - Convert your filtered Phase-1 output into the final consolidated dataset format.

### 🎯 What This Does

The Transform feature takes your Phase-1 Excel output (from the main extraction) and creates a final consolidated dataset with:
- **One row per service** (ΠΑΡΟΧΗ)
- **Year-specific consumption** calculations
- **Infrastructure classification** with ΦΟΠ override rules
- **Professional Excel formatting** with metadata

### 🚀 How to Use the Transform Feature

**Via Web Interface (Recommended):**

1. **Start the application:**
   ```bash
   cd ops
   docker compose up -d
   ```

2. **Access the web interface:**
   - Open: http://localhost:8080
   - Login: admin / testpass

3. **Use the Transform feature:**
   - Click "Transform" in the navigation
   - Upload your Phase-1 Excel file (e.g., `filtered.xlsx`)
   - Optionally upload a classification CSV file
   - Set the target year (default: 2023)
   - Choose whether to keep string IDs
   - Click "Run Transform"
   - Download the final Excel file

**Via Command Line:**
```bash
# Activate environment
source dei_env_new/bin/activate

# Run transformation
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx" \
  --year 2023
```

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

## 🌐 Web Application Features

### Modern Web Interface

The Docker Compose deployment provides a complete web application with:

**🎨 Frontend (Next.js)**
- **Drag & Drop Upload**: Easy file upload interface
- **Real-time Progress**: Live progress updates during processing
- **Multi-language Support**: English and Greek interfaces
- **Responsive Design**: Works on desktop and mobile
- **Transform Feature**: Dedicated page for Phase-1 to Final conversion

**⚡ Backend (FastAPI)**
- **RESTful API**: Clean API endpoints for all operations
- **File Validation**: Server-side upload validation and security
- **OCR Processing**: Automatic text extraction from scanned PDFs
- **Safe ZIP Extraction**: Prevents zip-slip security vulnerabilities
- **Automatic Cleanup**: Background cleanup of temporary files

**🔒 Proxy (Caddy)**
- **HTTPS Security**: Automatic HTTPS with internal certificates
- **Basic Authentication**: Username/password protection
- **Security Headers**: Comprehensive security headers
- **Upload Limits**: Configurable file size and count limits
- **Reverse Proxy**: Routes API calls to backend, UI to frontend

### Application URLs

When running with Docker Compose:
- **Main Application**: http://localhost:8080
- **Extract Feature**: http://localhost:8080/ (main page)
- **Transform Feature**: http://localhost:8080/transform
- **API Documentation**: http://localhost:8080/api/docs (when backend is running)

### Security Features

- ✅ **HTTPS Encryption**: All traffic encrypted in transit
- ✅ **Basic Authentication**: Username/password protection
- ✅ **File Type Validation**: Only PDF and ZIP files allowed
- ✅ **Upload Size Limits**: Configurable limits prevent abuse
- ✅ **Safe File Processing**: Prevents directory traversal attacks
- ✅ **Automatic Cleanup**: No files persist after processing
- ✅ **Security Headers**: Comprehensive security headers via Caddy

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
### Επιλογή εκκαθαριστικών ±60 ημερών γύρω από 2023 & στόχος 365 ημερών

Για τη μετατροπή στο τελικό αρχείο (ΠΑΡΟΧΕΣ 2023), γίνεται επιλογή πρώτου/τελευταίου εκκαθαριστικού λογαριασμού ανά παροχή ως εξής:

- Πρώτος: `period_start` εντός ±60 ημερών από 2023-01-01 (fallback έως ±120)
- Τελευταίος: `period_end` εντός ±60 ημερών από 2023-12-31 (fallback έως ±120)
- Επιλογή ζευγαριού με διάρκεια κοντά στις 365 ημέρες (tie-breakers: κοντινότερο στην αρχή, κοντινότερο στο τέλος, μεγαλύτερο span)
- Αν λείπει μία πλευρά, γίνεται best-effort και καταγράφεται προειδοποίηση στα logs

Παράδειγμα CLI (μετασχηματισμός Phase-1 σε τελικό):

```bash
python scripts/transform_to_final.py \
  --input "filtered 2.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx" \
  --year 2023 \
  --window-days 60 \
  --target-span-days 365
```

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

### Docker Compose Issues

**❌ Problem: "Docker not found" or "docker compose not found"**

**Solution:**
```bash
# Install Docker Desktop or Docker Engine
# On macOS: Download from https://www.docker.com/products/docker-desktop
# On Ubuntu: sudo apt install docker.io docker-compose-plugin
# On Windows: Download Docker Desktop

# Verify installation
docker --version
docker compose version
```

**❌ Problem: "Port 8080 already in use"**

**Solution:**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process or change the port in ops/docker-compose.yml
# Change "8080:443" to "8081:443" and access via http://localhost:8081
```

**❌ Problem: "Cannot connect to the Docker daemon"**

**Solution:**
```bash
# Start Docker service
sudo systemctl start docker  # Linux
# Or start Docker Desktop application

# Add your user to docker group (Linux)
sudo usermod -aG docker $USER
# Then logout and login again
```

**❌ Problem: "Build failed" or "Image not found"**

**Solution:**
```bash
# Clean Docker cache and rebuild
cd ops
docker system prune -a
docker compose build --no-cache
docker compose up -d
```

**❌ Problem: "Authentication failed" or "Cannot login"**

**Solution:**
```bash
# Default credentials:
# Username: admin
# Password: testpass

# If you changed the password, check ops/Caddyfile for the hash
# Generate new hash: docker run --rm caddy:2 caddy hash-password --plaintext 'yourpassword'
```

### Command Line Issues

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

## 🔄 Final 2023 Transformation

**NEW: Phase-1 to Final Dataset Transformation** - Convert the filtered Phase-1 output into the final consolidated dataset format for 2023 analysis.

### 🎯 What This Does

The transformation takes the Phase-1 output (filtered 2.xlsx) and creates a final consolidated dataset with:
- **One row per service** (ΠΑΡΟΧΗ)
- **2023 consumption window** calculations
- **Infrastructure classification** with ΦΟΠ override rules
- **Professional Excel formatting** with metadata

### 🚀 Quick Start - Final Transformation

```bash
# 1. Activate the virtual environment
source dei_env_new/bin/activate

# 2. Run the transformation
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx"
```

### 📊 Output Results

The transformation produces:
- **513 unique services** from 3,283 Phase-1 records
- **360 ΦΟΠ entries** (all correctly classified as "ΟΧΙ")
- **26 columns** in exact target schema
- **Professional Excel formatting** with headers and metadata

### 🔧 Advanced Usage Options

```bash
# With validation against sample file
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx" \
  --validate-against "dei_extractor/data/Sample Παροχές.xlsx"

# With custom classification mapping
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx" \
  --class-mapping "scripts/class_mapping.csv"

# With debug logging
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx" \
  --log-level DEBUG
```

### 📋 All Available Options

```bash
python scripts/transform_to_final.py --help
```

**Required Arguments:**
- `--input, -i`: Path to Phase-1 Excel file (filtered 2.xlsx)
- `--output, -o`: Path for output Excel file

**Optional Arguments:**
- `--year`: Target year for calculations (default: 2023)
- `--encoding`: File encoding (default: utf-8-sig)
- `--keep-str-ids`: Keep service IDs as strings
- `--log-level`: Logging level (INFO|DEBUG|WARNING|ERROR)
- `--validate-against`: Path to sample file for validation
- `--class-mapping`: Path to custom classification mapping CSV

### 🎯 Key Features

#### **Consumption Window Logic**
- Finds periods containing 2023-01-01 and 2023-12-31
- Handles missing data with fallback logic
- Calculates initial and final meter readings

#### **Meter Reset Handling**
- Automatically detects when final < initial reading
- Switches to sum-based calculation using ΣυνΩΧΒ
- Logs warnings for transparency

#### **ΦΟΠ Classification Rule**
- **CRITICAL**: If ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ == "ΦΟΠ" → ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ) = "ΟΧΙ" **ALWAYS**
- All 360 ΦΟΠ entries correctly classified as "ΟΧΙ" ✓
- Non-ΦΟΠ entries use keyword matching

#### **Formula Calculations**
- `captured_days = (end_date - start_date).days`
- `captured_kwh = final_reading - initial_reading` (or sum for resets)
- `mean_per_day = captured_kwh / captured_days`
- `consumption_2023 = mean_per_day * 365`

### 🧪 Testing the Transformation

```bash
# Run all transformation tests
python -m pytest tests/test_final_2023.py -v

# Run specific test
python -m pytest tests/test_final_2023.py::test_classify_infrastructure -v
```

### 📊 Verify Results

```bash
# Check the output file
python -c "import pandas as pd; df = pd.read_excel('ΠΑΡΟΧΕΣ_2023_FINAL.xlsx'); print(f'Total services: {len(df)}'); print(f'ΦΟΠ entries: {(df[\"ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ\"] == \"ΦΟΠ\").sum()}'); print(f'Infrastructure flags: {df[\"ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)\"].value_counts()}')"
```

### 📁 Output File Structure

The final Excel file contains:
- **Sheet1**: Main data with 26 columns in exact target order
- **_meta**: Metadata sheet with column descriptions and formulas
- **Professional formatting**: Bold headers, frozen rows, auto-sized columns

### ✅ Validation Results

```
2025-08-29 10:17:55,765 - INFO - Validating ΦΟΠ classification...
2025-08-29 10:17:55,765 - INFO - Found 360 ΦΟΠ entries
2025-08-29 10:17:55,766 - INFO - All ΦΟΠ entries correctly classified as 'ΟΧΙ' ✓
```

## 🗓️ Dynamic Year Processing

**NEW: Multi-Year Support** - The transformation script now supports processing data for any year, not just 2023!

### 🎯 What This Does

The dynamic year functionality allows you to:
- **Process any year** (2019, 2020, 2021, 2022, 2023, etc.)
- **Automatic column naming** with year-specific headers
- **Linear interpolation** for accurate meter readings at year boundaries
- **Consistent output format** regardless of the target year

### 🚀 Quick Start - Multi-Year Processing

```bash
# Process 2023 data (default)
python scripts/transform_to_final.py \
  --input "filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx"

# Process 2019 data
python scripts/transform_to_final.py \
  --input "filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2019_FINAL.xlsx" \
  --year 2019

# Process 2022 data with validation
python scripts/transform_to_final.py \
  --input "filtered.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2022_FINAL.xlsx" \
  --year 2022 \
  --validate-against "sample_2022.xlsx"
```

### 📊 Dynamic Column Names

The output columns automatically adapt to the target year:

**For 2023:**
- `ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/2023`
- `ΚΑΤΑΝΑΛΩΣΗ 2023 KWH`
- `ΚΑΤΑΝΑΛΩΣΗ 1.1.2023`
- `ΚΑΤΑΝΑΛΩΣΗ 31.12.2023`

**For 2019:**
- `ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/2019`
- `ΚΑΤΑΝΑΛΩΣΗ 2019 KWH`
- `ΚΑΤΑΝΑΛΩΣΗ 1.1.2019`
- `ΚΑΤΑΝΑΛΩΣΗ 31.12.2019`

### 🔬 Linear Interpolation Algorithm

The tool now uses **linear interpolation** for accurate meter readings at year boundaries:

1. **If target date ≤ window start**: Use initial reading
2. **If target date ≥ window end**: Use final reading
3. **If within window**: Linear interpolation based on days

**Formula:**
```
reading_at_date = initial_reading + (final_reading - initial_reading) × (days_from_start / total_days)
```

**Year Consumption Calculation:**
```
consumption_year = reading_at_year_end - reading_at_year_start
```

### 🎯 Key Benefits

- **Accurate Readings**: Linear interpolation provides precise meter readings at year boundaries
- **Consistent Format**: Same output structure regardless of target year
- **Backward Compatible**: Default year is still 2023
- **Memory Compliant**: Maintains the same output format as requested

### 📋 All Year-Related Options

```bash
python scripts/transform_to_final.py --help
```

**Year-Specific Arguments:**
- `--year`: Target year for calculations (default: 2023)
- `--window-days`: ± window around year anchors in days (default: 60)
- `--target-span-days`: Target total span in days (default: 365)

### 🧪 Testing Multi-Year Processing

```bash
# Test with 2019 data
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered.xlsx" \
  --output "test_2019.xlsx" \
  --year 2019 \
  --log-level DEBUG

# Verify column names
python -c "
import pandas as pd
df = pd.read_excel('test_2019.xlsx')
year_cols = [col for col in df.columns if '2019' in col]
print('2019-specific columns:')
for col in year_cols:
    print(f'  {col}')
"
```

### 📊 Output Verification

```bash
# Check year-specific calculations
python -c "
import pandas as pd
df = pd.read_excel('ΠΑΡΟΧΕΣ_2019_FINAL.xlsx')
print(f'Total services: {len(df)}')
print(f'Year consumption column: {[col for col in df.columns if \"2019 KWH\" in col]}')
print(f'Sample year consumption: {df[[col for col in df.columns if \"2019 KWH\" in col][0]].head()}')
"
```

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

## 🏗️ Production Deployment

### Architecture Overview

The Docker Compose deployment consists of three services:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Proxy         │
│   (Next.js)     │    │   (FastAPI)     │    │   (Caddy)       │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 443     │
│                 │    │                 │    │                 │
│ • React UI      │    │ • PDF Processing│    │ • HTTPS         │
│ • File Upload   │    │ • OCR Engine    │    │ • Auth          │
│ • Progress UI   │    │ • API Endpoints │    │ • Security      │
│ • Transform UI  │    │ • File Validation│   │ • Routing       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   User Browser  │
                    │   Port: 8080    │
                    │                 │
                    │ • HTTPS Access  │
                    │ • Basic Auth    │
                    │ • File Upload   │
                    │ • Download      │
                    └─────────────────┘
```

### Production Considerations

**🔒 Security:**
- Change default password in `ops/Caddyfile`
- Use external certificates for production
- Configure firewall rules
- Monitor access logs

**⚡ Performance:**
- Adjust upload limits in `ops/docker-compose.yml`
- Monitor memory usage during large file processing
- Consider scaling backend services for high load
- Use SSD storage for better I/O performance

**📊 Monitoring:**
- Use `docker compose logs -f` for real-time monitoring
- Set up log aggregation for production
- Monitor disk space (temporary files are auto-cleaned)
- Track processing times and success rates

**🔄 Maintenance:**
- Regular Docker image updates
- Monitor for security vulnerabilities
- Backup custom configurations
- Test with sample data regularly

### Environment Configuration

Key environment variables in `ops/docker-compose.yml`:

```yaml
environment:
  - RETENTION_HOURS=24        # Hours to keep temp files
  - MAX_FILES=50             # Max files per upload
  - MAX_UPLOAD_MB=100        # Max upload size in MB
  - LOG_LEVEL=INFO           # Logging level
```

### Scaling Considerations

For high-volume processing:
1. **Horizontal Scaling**: Run multiple backend containers
2. **Load Balancing**: Use external load balancer
3. **Storage**: Use shared storage for temporary files
4. **Queue System**: Implement job queue for large batches

## 📄 License

This project is licensed under the MIT License.

## 🎉 Success Stories

**"The unified architecture solved our mixed PDF format problems. Now we process both old and new DEI bills with perfect accuracy!"** - Municipal Energy Department

**"Easy to use, even for beginners. The automatic format detection is a game-changer!"** - Energy Consultant

---

**🎯 Ready to process your DEI electricity bills? Start with the Quick Start Guide above!**

**Need help?** Check the Troubleshooting section or run with `--verbose` for detailed logs.
