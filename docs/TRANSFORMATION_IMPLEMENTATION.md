# Final 2023 Transformation Implementation

This document describes the implementation of the deterministic Python transformation that converts Phase-1 output (filtered 2.xlsx) into the final dataset format matching the structure of "ΠΑΡΟΧΕΣ 2023".

## Overview

The transformation system consists of:

1. **Core Module**: `dei_extractor/transform/final_2023.py` - Pure functions for data transformation
2. **CLI Script**: `scripts/transform_to_final.py` - Command-line interface
3. **Test Suite**: `tests/test_final_2023.py` - Comprehensive unit tests
4. **Configuration**: `scripts/class_mapping.csv` - Custom classification mapping

## Architecture

### Core Functions

#### `load_phase1(path: str) -> pd.DataFrame`
- Loads Phase-1 Excel file from the specified path
- Performs initial data cleaning and validation
- Parses consumption periods into start/end dates
- Converts numeric columns to appropriate types
- Validates required columns are present

#### `compute_final(df: pd.DataFrame, year: int = 2023, class_map_path: Optional[str] = None) -> pd.DataFrame`
- Groups data by service ID (ΑρΠαροχής)
- Computes consumption window covering the target year
- Calculates all required metrics and formulas
- Applies infrastructure classification
- Returns final dataset with exact column structure

#### `write_final(df: pd.DataFrame, path: str)`
- Writes final dataset to Excel with proper formatting
- Creates metadata sheet with column descriptions
- Applies header formatting and column widths
- Freezes top row for better usability

### Key Features

#### 1. Consumption Window Calculation
- Finds periods containing 2023-01-01 and 2023-12-31
- Handles cases where data doesn't span the full year
- Uses fallback logic for missing periods
- Calculates initial and final meter readings

#### 2. Meter Reset Handling
- Detects when final reading < initial reading
- Automatically switches to sum-based calculation
- Uses ΣυνΩΧΒ values across the window period
- Logs warnings for transparency

#### 3. Infrastructure Classification
- Keyword-based classification for infrastructure types
- Configurable via CSV mapping file
- Supports custom patterns and overrides
- Categorizes into sectors and subtypes

#### 4. Formula Calculations
- **Captured Days**: `(window_end - window_start).days`
- **Mean Daily Consumption**: `captured_kwh / captured_days`
- **2023 Consumption**: `mean_per_day * 365` (prorated)
- **Days Before/After 2023**: Relative to year boundaries
- **Boundary Readings**: Linear interpolation to year start/end

## Output Schema

The final Excel file contains exactly 26 columns in this order:

1. `Α/Α` - Sequential index (1..N)
2. `ΠΑΡΟΧΗ` - Service/Meter ID
3. `ΑΡΙΘΜΟΣ ΣΥΜΒΟΛΑΙΟΥ ` - Account/Contract number
4. `ΟΝΟΜΑ ` - Cleaned site name and address
5. `ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)` - Infrastructure flag
6. `ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ` - Facility type
7. `ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ` - Window start date
8. `ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ` - Initial meter reading
9. `ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ` - Window end date
10. `ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ` - Final meter reading
11. `ΣΧΟΛΙΟ` - Comments (empty by default)
12. `ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/23` - Days before 2023
13. `ΑΡ. ΗΜΕΡΩΝ ΜΕΤΑ ΤΙΣ 31/12/2023` - Days after 2023
14. `ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ` - Captured period days
15. `ΑΡ. ΗΜΕΡΩΝ 2019` - Constant 365
16. `ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH` - Captured consumption
17. `ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ.` - Average daily consumption
18. `ΚΑΤΑΝΑΛΩΣΗ 2023 KWH` - 2023 consumption (prorated)
19. `ΚΑΤΑΝΑΛΩΣΗ ΗΜΕΡΩΝ ΠΡΙΝ ΤΗΣ 1.1.2023` - Consumption before 2023
20. `ΚΑΤΑΝΑΛΩΣΗ 1.1.2023` - Reading at 2023-01-01
21. `ΚΑΤΑΝΑΛΩΣΗ 1.1.2023.1` - Absolute reading at 2023-01-01
22. `ΚΑΤΑΝΑΛΩΣΗ 31.12.2023` - Reading at 2023-12-31
23. `ΔΙΑΦΟΡΑ ΚΑΤΑΝΑΛΩΣΗΣ KWH` - Duplicate of consumption_2023
24. `Unnamed: 23` - Reserved for future use
25. `Unnamed: 24` - Classification subtype
26. `Unnamed: 25` - Sector classification

## Usage

### Basic Usage
```bash
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered 2.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx"
```

### With Custom Classification
```bash
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered 2.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx" \
  --class-mapping "scripts/class_mapping.csv"
```

### With Validation
```bash
python scripts/transform_to_final.py \
  --input "dei_extractor/data/filtered 2.xlsx" \
  --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx" \
  --validate-against "dei_extractor/data/Sample Παροχές.xlsx"
```

### CLI Options
- `--input, -i`: Path to Phase-1 Excel file (required)
- `--output, -o`: Path for output Excel file (required)
- `--year`: Target year for calculations (default: 2023)
- `--encoding`: File encoding (default: utf-8-sig)
- `--keep-str-ids`: Keep service IDs as strings
- `--log-level`: Logging level (INFO|DEBUG|WARNING|ERROR)
- `--validate-against`: Path to sample file for validation
- `--class-mapping`: Path to custom classification mapping CSV

## Classification System

### Infrastructure Keywords
The system recognizes these Greek keywords to identify infrastructure:
- `ΣΧΟΛΕΙΟ`, `ΓΥΜΝΑΣΙΟ`, `ΛΥΚΕΙΟ`, `ΝΗΠΙΑΓΩΓΕΙΟ` → Schools
- `ΔΗΜΑΡΧΕΙΟ`, `ΥΠΗΡΕΣΙΑ`, `ΚΟΙΝΟΤΗΣ`, `ΚΟΙΝΟΤΗΤΑ` → Municipal services
- `ΓΗΠΕΔΟ`, `ΚΛΕΙΣΤΟ`, `ΚΟΛΥΜΒΗΤΗΡΙΟ` → Sports facilities
- `ΑΝΤΛΙΟΣΤΑΣΙΟ` → Pumping stations
- And more...

### Sector Mapping
- **ΣΧΟΛΕΙΟ**: Educational institutions
- **ΚΑΠΗ**: Municipal community centers
- **ΔΗΜΑΡΧΕΙΑ - ΔΗΜΟΣΙΕΣ ΥΠΗΡΕΣΙΕΣ**: Municipal services
- **ΑΘΛ. ΕΓΚ/ΣΤΑΣΗ**: Sports facilities
- **ΛΟΙΠΕΣ ΥΠΟΔΟΜΕΣ**: Other infrastructure

### Custom Mapping
The `scripts/class_mapping.csv` file allows custom overrides:
```csv
pattern,subtype,bucket
ΑΝΤΛΙΟΣΤΑΣΙΟ,ΑΝΤΛΙΟΣΤΑΣΙΟ,ΛΟΙΠΕΣ ΥΠΟΔΟΜΕΣ
ΣΧΟΛΕΙΟ,ΣΧΟΛΕΙΟ,ΣΧΟΛΕΙΟ
```

## Testing

### Running Tests
```bash
python -m pytest tests/test_final_2023.py -v
```

### Test Coverage
- **Unit Tests**: Individual function testing
- **Integration Tests**: End-to-end workflow testing
- **Edge Cases**: Meter resets, missing data, invalid periods
- **Formula Verification**: Mathematical correctness validation
- **Data Type Testing**: Proper column type handling

### Test Scenarios
1. **Normal Operation**: Standard data processing
2. **Meter Reset**: Handling final < initial readings
3. **Missing 2023 Overlap**: Extrapolation from available data
4. **Invalid Periods**: Filtering out bad data
5. **Classification**: Infrastructure type detection
6. **File I/O**: Excel reading and writing

## Data Processing Details

### Period Parsing
- Input format: `dd.mm.yyyy-dd.mm.yyyy`
- Day-first parsing for Greek date format
- Invalid periods are filtered out
- Period days are calculated and validated

### Numeric Handling
- Meter readings converted to float64 (handles NaN)
- Service IDs preserved as strings (leading zeros)
- Consumption calculations use proper numeric types
- Rounding to 6 decimal places for precision

### Greek Text Processing
- Site names converted to uppercase
- Spaces normalized and trimmed
- Duplicate words removed (e.g., "ΔΗΜΟΣ ΔΗΜΟΣ" → "ΔΗΜΟΣ")
- Classification uses uppercase Greek keywords

## Error Handling

### Robust Processing
- Invalid periods are logged and filtered
- Missing data handled gracefully with NaN values
- Meter resets detected and handled automatically
- Classification failures fall back to defaults

### Logging
- Comprehensive logging at INFO level
- DEBUG level for detailed processing steps
- Warnings for data quality issues
- Errors for processing failures

## Performance

### Optimization
- Efficient pandas operations for large datasets
- Minimal memory usage with streaming processing
- Fast Excel writing with xlsxwriter engine
- Optimized date parsing and calculations

### Scalability
- Handles thousands of records efficiently
- Memory usage scales linearly with data size
- Processing time scales with number of services
- Suitable for production data volumes

## Output Quality

### Excel Formatting
- Bold headers with borders
- Frozen top row for navigation
- Auto-sized columns based on content
- Metadata sheet with documentation
- Professional appearance matching requirements

### Data Quality
- Deterministic output ordering
- Consistent data types across runs
- Proper handling of edge cases
- Validation against sample data
- Comprehensive error checking

## Future Enhancements

### Potential Improvements
1. **Parallel Processing**: Multi-threading for large datasets
2. **Caching**: Intermediate results for repeated runs
3. **Validation Rules**: Configurable data quality checks
4. **Reporting**: Detailed processing statistics
5. **API Interface**: REST API for integration

### Extensibility
- Modular design allows easy feature addition
- Configuration-driven classification
- Plugin architecture for custom processing
- Version control for transformation logic

## Conclusion

The transformation system successfully converts Phase-1 data to the final 2023 format with:
- **Accuracy**: Correct mathematical calculations
- **Reliability**: Robust error handling
- **Performance**: Efficient processing of large datasets
- **Maintainability**: Well-tested, documented code
- **Usability**: Simple CLI interface with comprehensive options

The implementation meets all specified requirements and provides a solid foundation for future enhancements.
