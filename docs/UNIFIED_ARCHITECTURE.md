# DEI Extractor - Unified Architecture

## Overview

The DEI Extractor has been restructured to use a **unified architecture** that automatically detects PDF formats and routes to the appropriate dedicated extractor. This approach provides better results when processing mixed PDF formats and eliminates the issues that arise from trying to handle both old and new formats in a single extractor.

## Architecture Components

### 1. Unified Extractor (`DEIUnifiedExtractor`)
- **Location**: `dei_extractor/core/unified_extractor.py`
- **Purpose**: Main entry point that intelligently routes PDFs to appropriate extractors
- **Features**:
  - Automatic format detection (v2018 vs modern)
  - Routes to dedicated extractors for optimal results
  - Combines results from both formats
  - Maintains consistent output format
  - Provides format statistics

### 2. v2018 Extractor (`DEIV2018Extractor`)
- **Location**: `dei_extractor/core/extractor_v2018.py`
- **Purpose**: Dedicated extractor for older DEI PDF format (2018 and earlier)
- **Features**:
  - Optimized for v2018 layout patterns
  - High confidence parsing for v2018 format
  - Extracts all v2018 specific fields
  - Generates standardized output compatible with modern format

### 3. Modern Extractor (`DEIModernExtractor`)
- **Location**: `dei_extractor/core/extractor_modern.py`
- **Purpose**: Dedicated extractor for current DEI PDF format
- **Features**:
  - Optimized for modern 3-row block structure
  - Enhanced edge case handling
  - Confidence threshold system
  - Deduplication and validation

## How It Works

### 1. Format Detection
The unified extractor automatically detects PDF format using specific text anchors:

**v2018 Detection Patterns:**
- "Ο λογαριασμός σας συνοπτικά"
- "Κωδικός Ηλεκτρονικής Πληρωμής"
- "Κατανάλωση Ηλεκτρικής Ενέργειας"

**Modern Detection:**
- Default when v2018 patterns are not found
- Uses 3-row block structure parsing

### 2. Processing Flow
```
PDF Files → Format Detection → Route to Dedicated Extractor → Combine Results → Output
```

1. **Input**: PDF files are provided to the unified extractor
2. **Detection**: Each PDF is analyzed for format-specific patterns
3. **Routing**: PDFs are categorized and sent to appropriate extractors
4. **Processing**: Each extractor processes its assigned PDFs optimally
5. **Combination**: Results are combined into a single DataFrame
6. **Output**: Standardized CSV/Excel files are generated

### 3. Output Format
Both extractors produce the same standardized field names, ensuring compatibility:

| Field | Description | v2018 | Modern |
|-------|-------------|-------|--------|
| `ΑρΠαροχής` | Supply number | ✅ | ✅ |
| `ΑρΛογαριασμού` | Account number | ✅ | ✅ |
| `ΗμΈκδοσης` | Issue date | ✅ | ✅ |
| `ΠερίοδοςΚατανάλωσης` | Billing period | ✅ | ✅ |
| `Ονοματεπώνυμο_Διεύθυνση` | Name and address | ✅ | ✅ |
| `Πόλη` | City | ✅ | ✅ |
| `Τελευταία` | Current reading | ✅ | ✅ |
| `Προηγούμενη` | Previous reading | ✅ | ✅ |
| `ΣΩΧΒ` | Total consumption | ✅ | ✅ |
| `ΣυνΩΧΒ` | Consumption difference | ✅ | ✅ |
| `ΚατηγορίαΤιμολογίου` | Billing category | ✅ | ✅ |
| `Υποκατηγορία` | Billing subcategory | ❌ | ✅ |
| `Εκαθαριστικός` | Final settlement flag | ✅ | ✅ |

## Usage

### Command Line Interface
The CLI automatically uses the unified extractor:

```bash
# Process mixed PDF formats
dei-extract --input "path/to/pdfs" --output-dir "results" --verbose

# With filtering
dei-extract --input "path/to/pdfs" --output-dir "results" --filter --verbose
```

### Python API

```python
from dei_extractor.core.unified_extractor import DEIUnifiedExtractor
from dei_extractor.utils.config import Config

# Initialize unified extractor
config = Config()
extractor = DEIUnifiedExtractor(config)

# Process PDF files (automatic format detection)
pdf_files = ["invoice1.pdf", "invoice2.pdf", "invoice3.pdf"]
df = extractor.process_files(pdf_files)

# Write outputs
extractor.write_outputs(df, output_dir="my_output")

# Get format statistics
stats = extractor.get_format_statistics()
print(f"v2018: {stats['v2018']}, Modern: {stats['modern']}")
```

### Individual Extractors
You can also use individual extractors directly:

```python
# For v2018 PDFs only
from dei_extractor.core.extractor_v2018 import DEIV2018Extractor
v2018_extractor = DEIV2018Extractor()
df_v2018 = v2018_extractor.process_files(v2018_pdfs)

# For modern PDFs only
from dei_extractor.core.extractor_modern import DEIModernExtractor
modern_extractor = DEIModernExtractor()
df_modern = modern_extractor.process_files(modern_pdfs)
```

## Benefits

### 1. Better Accuracy
- Each extractor is optimized for its specific format
- No compromise between different parsing strategies
- Higher success rates for both formats

### 2. Improved Maintainability
- Clear separation of concerns
- Easier to update format-specific logic
- Independent testing of each extractor

### 3. Enhanced Debugging
- Format-specific error messages
- Separate warning logs for each format
- Detailed statistics about processed formats

### 4. Future-Proof
- Easy to add new PDF formats
- Modular architecture supports extensions
- Backward compatibility maintained

## Output Files

The unified extractor generates the same output files as before, but with improved accuracy:

### Standard Output Files
- **`ολα.csv`** / **`ολα.xlsx`** - All extracted records (both formats)
- **`φoπ.csv`** / **`φoπ.xlsx`** - Residential (ΦΟΠ) records only
- **`επαγγελματικα.csv`** / **`επαγγελματικα.xlsx`** - Commercial records only

### Additional Files
- **`format_stats.txt`** - Statistics about processed formats
- **`warnings_unified.log`** - Combined warnings from both extractors

## Migration from Old Architecture

The new architecture is **backward compatible**. Existing code will continue to work:

```python
# Old code (still works)
from dei_extractor.core.extractor import DEIExtractorEnhanced
extractor = DEIExtractorEnhanced()

# New code (recommended)
from dei_extractor.core.unified_extractor import DEIUnifiedExtractor
extractor = DEIUnifiedExtractor()
```

## Testing

Test the new architecture:

```bash
# Run the test script
python test_unified_extractor.py

# Test with CLI
dei-extract --input "dei_extractor/data" --output-dir "output" --verbose
```

## Troubleshooting

### Common Issues

1. **"No records extracted"**
   - Check if PDFs are in supported formats
   - Verify PDF files are not corrupted
   - Check format detection patterns

2. **"Unknown format detected"**
   - PDF may be in unsupported format
   - Check if PDF is actually a DEI invoice
   - Verify OCR is working for scanned PDFs

3. **Mixed results quality**
   - Each format is processed independently
   - Check format-specific warning logs
   - Verify format detection accuracy

### Debug Information

The unified extractor provides detailed logging:

```bash
# Enable verbose logging
dei-extract --input "pdfs" --verbose

# Check format statistics
cat output/format_stats.txt

# Review warnings
cat output/warnings_unified.log
```

## Future Enhancements

1. **Additional Formats**: Easy to add support for new DEI PDF formats
2. **Machine Learning**: Potential for ML-based format detection
3. **Performance**: Parallel processing of different formats
4. **Validation**: Enhanced validation for each format
5. **Reporting**: Detailed format-specific reports

---

This unified architecture provides a robust, maintainable, and accurate solution for processing mixed DEI PDF formats while maintaining backward compatibility and providing clear separation of concerns.
