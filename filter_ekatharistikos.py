#!/usr/bin/env python3
"""
Filter electricity bills data based on εκαθαριστικος field

Example usage:
python filter_ekatharistikos.py \
  --inputs ολα.csv,φoπ.csv,επαγγελματικα.csv \
  --out-csv filtered.csv \
  --out-xlsx filtered.xlsx
"""

import argparse
import logging
import pandas as pd
from pathlib import Path
import sys

# Constants for boolean normalization
TRUE_SET = {"true", "1", "ναι", "nai", "yes", "y", "t"}
FALSE_SET = {"false", "0", "όχι", "oxi", "no", "n", "f"}

def normalize_bool(v):
    """Normalize boolean values to True/False/None."""
    if isinstance(v, bool):
        return v
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip().lower()
    if s in TRUE_SET:
        return True
    if s in FALSE_SET:
        return False
    return None

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Filter electricity bills data based on εκαθαριστικος field"
    )
    parser.add_argument(
        '--inputs',
        default='ολα.csv,φoπ.csv,επαγγελματικα.csv',
        help='Comma-separated list of input CSV files (default: ολα.csv,φoπ.csv,επαγγελματικα.csv)'
    )
    parser.add_argument(
        '--out-csv',
        default='filtered.csv',
        help='Output CSV file path (default: filtered.csv)'
    )
    parser.add_argument(
        '--out-xlsx',
        default='filtered.xlsx',
        help='Output Excel file path (default: filtered.xlsx)'
    )
    return parser.parse_args()

def read_input_files(input_files):
    """Read and combine input CSV files."""
    all_data = []
    found_files = []
    missing_files = []
    
    for csv_file in input_files:
        if Path(csv_file).exists():
            try:
                df = pd.read_csv(csv_file, encoding='utf-8-sig', dtype=str)
                all_data.append(df)
                found_files.append(csv_file)
                logging.info(f"Read {csv_file}: {len(df)} rows")
            except Exception as e:
                logging.error(f"Error reading {csv_file}: {e}")
                missing_files.append(csv_file)
        else:
            missing_files.append(csv_file)
    
    if missing_files:
        logging.warning(f"Missing files: {', '.join(missing_files)}")
    
    if not all_data:
        logging.error("No input files found or readable")
        return None, found_files
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    logging.info(f"Combined data: {len(combined_df)} rows from {len(found_files)} files")
    
    return combined_df, found_files

def filter_ekatharistikos(df):
    """Filter dataframe to keep only rows where Εκαθαριστικός is True."""
    if "Εκαθαριστικός" not in df.columns:
        raise KeyError("Missing required column: 'Εκαθαριστικός'")
    
    # Normalize boolean values
    df["Εκαθαριστικός"] = df["Εκαθαριστικός"].map(normalize_bool)
    
    # Count before filtering
    total_rows = len(df)
    true_count = len(df[df["Εκαθαριστικός"] == True])
    false_count = len(df[df["Εκαθαριστικός"] == False])
    null_count = total_rows - true_count - false_count
    
    logging.info(f"Boolean normalization results:")
    logging.info(f"  True values: {true_count}")
    logging.info(f"  False values: {false_count}")
    logging.info(f"  Null/Invalid values: {null_count}")
    
    # Filter to keep only True values
    filtered_df = df[df["Εκαθαριστικός"] == True].copy()
    removed_count = total_rows - len(filtered_df)
    
    logging.info(f"Filtered to {len(filtered_df)} rows (removed {removed_count})")
    
    return filtered_df

def remove_duplicates(df):
    """Remove duplicate rows based on composite key or fallback to full row comparison."""
    dedup_key = [c for c in ["ΑρΠαροχής", "ΑρΛογαριασμού", "ΗμΈκδοσης"] if c in df.columns]
    
    before_count = len(df)
    
    if len(dedup_key) == 3:
        df = df.drop_duplicates(subset=dedup_key, keep="first")
        removed_count = before_count - len(df)
        logging.info(f"Dropped {removed_count} duplicate rows (key: {', '.join(dedup_key)})")
    else:
        logging.warning(f"Composite key incomplete ({len(dedup_key)}/3 columns found); using full-row drop_duplicates()")
        df = df.drop_duplicates(keep="first")
        removed_count = before_count - len(df)
        logging.info(f"Dropped {removed_count} duplicate rows (full row comparison)")
    
    return df

def drop_afm_column(df):
    """Drop ΑΦΜ column if present (case-insensitive)."""
    for col in list(df.columns):
        if col.strip().lower() == "αφμ":
            df = df.drop(columns=[col])
            logging.info(f"Dropped ΑΦΜ column for privacy")
            break
    return df

def parse_dates(df):
    """Parse ΗμΈκδοσης column to DD/MM/YYYY format if it exists."""
    if "ΗμΈκδοσης" in df.columns:
        try:
            # Try to parse dates, but don't fail if parsing fails
            df["ΗμΈκδοσης"] = pd.to_datetime(df["ΗμΈκδοσης"], format="%d/%m/%Y", errors="coerce")
            # Convert back to string format DD/MM/YYYY for non-null values
            df["ΗμΈκδοσης"] = df["ΗμΈκδοσης"].dt.strftime("%d/%m/%Y").fillna(df["ΗμΈκδοσης"])
            logging.info("Successfully parsed ΗμΈκδοσης dates")
        except Exception as e:
            logging.warning(f"Could not parse ΗμΈκδοσης dates: {e}")
    return df

def write_output_files(df, out_csv, out_xlsx):
    """Write filtered data to CSV and Excel files."""
    try:
        # Write CSV with UTF-8 BOM
        df.to_csv(out_csv, index=False, encoding='utf-8-sig')
        logging.info(f"Wrote {out_csv} ({len(df)} rows)")
        
        # Write Excel
        df.to_excel(out_xlsx, index=False)
        logging.info(f"Wrote {out_xlsx}")
        
    except Exception as e:
        logging.error(f"Error writing output files: {e}")
        raise

def main():
    """Main function to orchestrate the filtering process."""
    setup_logging()
    args = parse_arguments()
    
    # Parse input files
    input_files = [f.strip() for f in args.inputs.split(',')]
    
    try:
        # Read input files
        df, found_files = read_input_files(input_files)
        if df is None:
            sys.exit(1)
        
        if not found_files:
            logging.error("No input files found")
            sys.exit(1)
        
        # Filter by Εκαθαριστικός
        df = filter_ekatharistikos(df)
        
        # Remove duplicates
        df = remove_duplicates(df)
        
        # Drop ΑΦΜ column if present
        df = drop_afm_column(df)
        
        # Parse dates (optional)
        df = parse_dates(df)
        
        # Write output files
        write_output_files(df, args.out_csv, args.out_xlsx)
        
        # Final summary
        logging.info("=" * 50)
        logging.info("PROCESSING SUMMARY:")
        logging.info(f"Found {len(found_files)} input files, read {len(df)} final rows")
        logging.info(f"Wrote {args.out_csv} ({len(df)} rows), {args.out_xlsx}")
        logging.info("=" * 50)
        
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
