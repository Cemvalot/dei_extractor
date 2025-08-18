# Enhanced DEI Extractor Features & Edge Cases

## Overview
The DEI extractor has been significantly enhanced to handle various edge cases and provide more robust data extraction from Greek DEI (Public Power Corporation) PDF invoices.

## Version 3.0 - Enhanced Features

### 1. ΦΟΠ Variations Recognition
**Problem**: ΦΟΠ codes appear in multiple formats across different invoices.
**Solution**: Normalize all variations to "ΦΟΠ"

**Supported Variations**:
- `ΦΟΠ` (standard)
- `Φ.Ο.Π` (with dots)
- `Φ Ο Π` (with spaces)

**Implementation**:
```python
# Enhanced ROW2 pattern
ROW2_PATTERN = re.compile(r"^(?P<code>ΦΟΠ|Φ\.Ο\.Π|Φ\s+Ο\s+Π|Γ\d+)\s+(?P<label>Τιμολόγιο|Επαγγελματικό)\b")

# Normalization logic
if code in ['ΦΟΠ', 'Φ.Ο.Π', 'Φ Ο Π']:
    category = 'ΦΟΠ'
```

### 2. Wrap Category Detection
**Problem**: Some invoices have Γ\d+ codes (e.g., Γ21) on one line with "Επαγγελματικό" appearing 1-2 lines later.
**Solution**: Detect and combine these as "Επαγγελματικό" category.

**Implementation**:
```python
def find_wrap_category(self, lines: List[str], current_index: int) -> Optional[str]:
    """Find wrap category (Γ\d+ followed by 'Επαγγελματικό' in next 1-2 lines)."""
    # Check current line for Γ\d+ pattern
    gamma_match = re.match(r"^(Γ\d+)\s+(.+)$", current_line)
    
    # Check next 1-2 lines for "Επαγγελματικό"
    for i in range(1, 3):
        if "Επαγγελματικό" in next_line:
            return "Επαγγελματικό"
```

### 3. Header/Footer Filtering
**Problem**: Headers and footers pollute the extracted data.
**Solution**: Filter out common header/footer patterns.

**Filtered Patterns**:
- `ΔΗΜΟΣΙΑ ΕΠΙΧΕΙΡΗΣΗ ΗΛΕΚΤΡΙΣΜΟΥ`
- `ΗΜΕΡΟΛΟΓΙΟ ΕΚΔΟΣΗΣ`
- `ΚΩΔ.ΠΟΛΛΑΠΛΟΥ`
- `ΚΩΔ.ΕΤΑΙΡΟΥ`
- `ΟΝΟΜΑ ΔΗΜΟΥ`
- `ΑΦΜ`
- `ΣΕΛΙΔΑ`

**Implementation**:
```python
HEADER_FOOTER_PATTERNS = [
    re.compile(r"ΔΗΜΟΣΙΑ\s+ΕΠΙΧΕΙΡΗΣΗ\s+ΗΛΕΚΤΡΙΣΜΟΥ", re.IGNORECASE),
    # ... other patterns
]

def should_ignore_line(self, line: str) -> bool:
    for pattern in HEADER_FOOTER_PATTERNS:
        if pattern.search(line_upper):
            return True
```

### 4. Summary Block Exclusion
**Problem**: Summary blocks with "Σ Υ Ν Ο Λ Α Π Ο Λ Λ Α Π Λ Ο Υ" should be ignored.
**Solution**: Filter out summary blocks.

**Implementation**:
```python
SUMMARY_PATTERN = re.compile(r"Σ\s+Υ\s+Ν\s+Ο\s+Λ\s+Α\s+Π\s+Ο\s+Λ\s+Λ\s+Α\s+Π\s+Λ\s+Ο\s+Υ", re.IGNORECASE)
```

### 5. Deduplication System
**Problem**: Duplicate records based on key fields.
**Solution**: Implement deduplication using composite key.

**Deduplication Key**: `ΑρΠαροχής_ΑρΛογαριασμού_ΗμΈκδοσης_ΠερίοδοςΚατανάλωσης`

**Implementation**:
```python
def create_deduplication_key(self, record: Dict) -> str:
    return f"{record.get('ΑρΠαροχής', '')}_{record.get('ΑρΛογαριασμού', '')}_{record.get('ΗμΈκδοσης', '')}_{record.get('ΠερίοδοςΚατανάλωσης', '')}"

# Check for duplicates
dedup_key = self.create_deduplication_key(record)
if dedup_key in self.processed_blocks:
    return None  # Skip duplicate
```

### 6. Enhanced ROW1 Regex
**Problem**: Names, addresses, and cities may contain numbers or special characters.
**Solution**: Improved regex pattern with better field separation.

**Implementation**:
```python
ROW1_PATTERN = re.compile(
    r"(?P<par>\d{10,11})\s+(?P<log>\d{9,12})\s+(?P<issued>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<period>\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<name>[^0-9]+?)\s{2,}(?P<addr>[^0-9]+?)\s{2,}(?P<city>[^0-9]+)$"
)
```

### 7. Enhanced ROW3 Regex with Fallback
**Problem**: Meter readings may appear in different formats.
**Solution**: Primary pattern with fallback option.

**Patterns**:
- Primary: `^Ημέρα\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$`
- Fallback: `^(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$`

**Implementation**:
```python
def parse_row3(self, line: str) -> Optional[Dict]:
    # Try primary pattern first
    match = ROW3_PATTERN.match(line)
    if match:
        return {...}
    
    # Try fallback pattern
    match = ROW3_FALLBACK_PATTERN.match(line)
    if match:
        return {...}
```

### 8. Zero Consumption Handling
**Problem**: When Τελευταία == Προηγούμενη (zero consumption), Εκαθαριστικός should still be True.
**Solution**: Always set Εκαθαριστικός=True when ROW3 data is present.

**Implementation**:
```python
if row3_data:
    record.update(row3_data)
    # Set Εκαθαριστικός=True even if Τελευταία == Προηγούμενη
    record['Εκαθαριστικός'] = True
```

### 9. Additional Fields Extraction
**Problem**: Missing useful information like store details and receipt numbers.
**Solution**: Extract additional fields from context.

**New Fields**:
- `ΚατάστημαΕξυπηρέτησης`: From "ΚΑΤΑΣΤΗΜΑ ΕΞΥΠΗΡ.ΔΕΗ : ..."
- `Παραστατικό`: From "ΠΑΡΑΣΤ: <digits>"
- `date_from` / `date_to`: Parsed from ΠερίοδοςΚατανάλωσης

**Implementation**:
```python
def extract_additional_fields(self, lines: List[str]) -> Dict:
    all_text = ' '.join(lines)
    
    # Extract store information
    store_match = STORE_PATTERN.search(all_text)
    if store_match:
        additional_fields['ΚατάστημαΕξυπηρέτησης'] = store_match.group(1).strip()
    
    # Extract receipt number
    receipt_match = RECEIPT_PATTERN.search(all_text)
    if receipt_match:
        additional_fields['Παραστατικό'] = receipt_match.group(1)
```

### 10. Period Date Parsing
**Problem**: ΠερίοδοςΚατανάλωσης is a string, need structured dates.
**Solution**: Parse into date_from and date_to fields.

**Format**: `DD.MM.YYYY-DD.MM.YYYY` → `YYYY-MM-DD`

**Implementation**:
```python
def parse_period_dates(self, period_str: str) -> Tuple[Optional[str], Optional[str]]:
    if '-' in period_str:
        start_part, end_part = period_str.split('-', 1)
        
        start_date = datetime.strptime(start_part.strip(), '%d.%m.%Y')
        date_from = start_date.strftime('%Y-%m-%d')
        
        end_date = datetime.strptime(end_part.strip(), '%d.%m.%Y')
        date_to = end_date.strftime('%Y-%m-%d')
        
        return date_from, date_to
```

### 11. Financial Line Exclusion
**Problem**: Financial lines like ΦΠΑ, charges, etc. should be excluded.
**Solution**: Filter out financial patterns.

**Excluded Patterns**:
- `ΦΠΑ`
- `ΡΥΘΜΙΖΟΜΕΝΕΣ ΧΡΕΩΣΕΙΣ`
- `ΧΡΕΩΣΕΙΣ ΠΡΟΜΗΘΕΙΑΣ ΔΕΗ`
- `ΤΡΕΧΩΝ ΜΗΝΑΣ`

**Implementation**:
```python
FINANCIAL_PATTERNS = [
    re.compile(r"ΦΠΑ", re.IGNORECASE),
    re.compile(r"ΡΥΘΜΙΖΟΜΕΝΕΣ\s+ΧΡΕΩΣΕΙΣ", re.IGNORECASE),
    # ... other patterns
]
```

## Usage Examples

### Running the Enhanced Extractor
```bash
python extract_dei_final.py --input "*.pdf"
```

### Expected Output Files
- `ολα.csv` / `ολα.xlsx`: All extracted records
- `φoπ.csv` / `φoπ.xlsx`: Residential (ΦΟΠ) records
- `επαγγελματικα.csv` / `επαγγελματικα.xlsx`: Commercial records

### New Output Fields
```csv
ΑρΠαροχής,ΑρΛογαριασμού,ΗμΈκδοσης,ΠερίοδοςΚατανάλωσης,Ονοματεπώνυμο,Διεύθυνση,Πόλη,Τελευταία,Προηγούμενη,ΣΩΧΒ,ΣυνΩΧΒ,ΚατηγορίαΤιμολογίου,Υποκατηγορία,Εκαθαριστικός,ΚατάστημαΕξυπηρέτησης,Παραστατικό,date_from,date_to,needs_review,reason,confidence,source_file,raw_code,raw_label
```

## Testing Enhanced Features

### Run Comprehensive Tests
```bash
python test_final_extractor.py
```

### Test Coverage
1. **ΦΟΠ Variations**: Verify all variations are normalized to "ΦΟΠ"
2. **Wrap Categories**: Check Γ\d+ + Επαγγελματικό detection
3. **Deduplication**: Ensure no duplicate records based on key fields
4. **Additional Fields**: Verify ΚατάστημαΕξυπηρέτησης, Παραστατικό extraction
5. **Date Parsing**: Check date_from/date_to parsing from periods
6. **Zero Consumption**: Verify Εκαθαριστικός=True for zero consumption
7. **Header/Footer Filtering**: Ensure no header/footer text in data
8. **Financial Exclusion**: Verify no financial lines in extracted data

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

## Error Handling

### Graceful Degradation
- OCR fallback when text extraction fails
- Partial record creation when some fields are missing
- Detailed logging for debugging

### Warning System
- Logs warnings to `warnings.log`
- Console output for user-friendly messages
- Confidence scoring for quality assessment

## Future Enhancements

### Potential Improvements
1. **Machine Learning**: Train models for better pattern recognition
2. **Multi-language Support**: Extend to other utility companies
3. **Real-time Processing**: Web interface for instant processing
4. **API Integration**: REST API for programmatic access
5. **Advanced Analytics**: Consumption pattern analysis

### Configuration Options
1. **Custom Patterns**: User-defined regex patterns
2. **Threshold Tuning**: Adjustable confidence thresholds
3. **Output Formats**: Additional export formats (JSON, XML)
4. **Batch Processing**: Parallel processing for large datasets

## Troubleshooting

### Common Issues
1. **Low Confidence**: Check PDF quality and format
2. **Missing Records**: Verify PDF structure matches expected format
3. **Duplicate Records**: Review deduplication logic
4. **OCR Errors**: Ensure Tesseract is properly installed

### Debug Mode
Enable detailed logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues or questions about the enhanced features:
1. Check the `warnings.log` file for detailed error messages
2. Review the test output for specific feature validation
3. Verify PDF format matches expected structure
4. Ensure all dependencies are properly installed
