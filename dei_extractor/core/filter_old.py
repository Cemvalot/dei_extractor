#!/usr/bin/env python3
"""
Filter old DEI data to keep only Εκαθαριστικός records.

This module provides functionality to filter DEI data files,
keeping only records where the Εκαθαριστικός field is True/1/Yes,
and removing duplicate records.
"""

import argparse
import logging
import sys
from typing import List, Optional, Tuple

import pandas as pd

# Constants
TRUE_SET = {"true", "1", "yes", "ναι", "t", "y"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Filter DEI data to keep only Εκαθαριστικός records"
    )
    parser.add_argument(
        "inputs",
        help="Comma-separated list of input CSV/Excel files",
    )
    parser.add_argument(
        "--out-csv",
        default="filtered_dei_data.csv",
        help="Output CSV file (default: filtered_dei_data.csv)",
    )
    parser.add_argument(
        "--out-xlsx",
        default="filtered_dei_data.xlsx",
        help="Output Excel file (default: filtered_dei_data.xlsx)",
    )
    return parser.parse_args()


def read_input_files(
    input_files: List[str],
) -> Tuple[Optional[pd.DataFrame], List[str]]:
    """Read and combine multiple input files."""
    all_data = []
    found_files = []

    for file_path in input_files:
        file_path = file_path.strip()
        if not file_path:
            continue

        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path, encoding="utf-8")
            elif file_path.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path)
            else:
                logging.warning(f"Unsupported file format: {file_path}")
                continue

            all_data.append(df)
            found_files.append(file_path)
            logging.info(f"Read {file_path} ({len(df)} rows)")

        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            continue

    if not all_data:
        return None, []

    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    logging.info(
        f"Combined {len(found_files)} files into {len(combined_df)} total rows"
    )

    return combined_df, found_files


def filter_ekatharistikos(df: pd.DataFrame) -> pd.DataFrame:
    """Filter data to keep only rows where Εκαθαριστικός is True/1/Yes."""
    if "Εκαθαριστικός" not in df.columns:
        logging.warning("Εκαθαριστικός column not found, returning original data")
        return df

    total_rows = len(df)
    filtered_df = df[df["Εκαθαριστικός"].str.lower().isin(TRUE_SET)]

    removed_count = total_rows - len(filtered_df)
    logging.info(f"Filtered to {len(filtered_df)} rows (removed {removed_count})")

    return filtered_df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows based on composite key or fallback to full row comparison."""
    dedup_key = [
        c for c in ["ΑρΠαροχής", "ΑρΛογαριασμού", "ΗμΈκδοσης"] if c in df.columns
    ]

    before_count = len(df)

    if len(dedup_key) == 3:
        df = df.drop_duplicates(subset=dedup_key, keep="first")
        removed_count = before_count - len(df)
        logging.info(
            f"Dropped {removed_count} duplicate rows (key: {', '.join(dedup_key)})"
        )
    else:
        df = df.drop_duplicates(keep="first")
        removed_count = before_count - len(df)
        logging.info(f"Dropped {removed_count} duplicate rows (full row comparison)")

    # Re-sort by ΑρΠαροχής after removing duplicates
    if "ΑρΠαροχής" in df.columns:
        df = df.sort_values(by=["ΑρΠαροχής"])
        logging.info(f"Re-sorted {len(df)} records by ΑρΠαροχής after deduplication")

    return df


def drop_afm_column(df: pd.DataFrame) -> pd.DataFrame:
    """Drop ΑΦΜ column if present (case-insensitive)."""
    for col in list(df.columns):
        if col.strip().lower() == "αφμ":
            df = df.drop(columns=[col])
            logging.info("Dropped ΑΦΜ column for privacy")
            break
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse ΗμΈκδοσης column to DD/MM/YYYY format if it exists."""
    if "ΗμΈκδοσης" in df.columns:
        try:
            # Try to parse dates, but don't fail if parsing fails
            df["ΗμΈκδοσης"] = pd.to_datetime(
                df["ΗμΈκδοσης"], format="%d/%m/%Y", errors="coerce"
            )
            # Convert back to string format DD/MM/YYYY for non-null values
            df["ΗμΈκδοσης"] = (
                df["ΗμΈκδοσης"].dt.strftime("%d/%m/%Y").fillna(df["ΗμΈκδοσης"])
            )
            logging.info("Successfully parsed ΗμΈκδοσης dates")
        except Exception as e:
            logging.warning(f"Could not parse ΗμΈκδοσης dates: {e}")
    return df


def write_output_files(df: pd.DataFrame, out_csv: str, out_xlsx: str) -> None:
    """Write filtered data to CSV and Excel files."""
    try:
        # Sort and group by ΑρΠαροχής if the column exists
        if "ΑρΠαροχής" in df.columns:
            df = df.sort_values(by=["ΑρΠαροχής"])
            logging.info(f"Sorted {len(df)} records by ΑρΠαροχής")

        # Write CSV with UTF-8 BOM
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        logging.info(f"Wrote {out_csv} ({len(df)} rows)")

        # Write Excel
        df.to_excel(out_xlsx, index=False)
        logging.info(f"Wrote {out_xlsx}")

    except Exception as e:
        logging.error(f"Error writing output files: {e}")
        raise


def main() -> None:
    """Main function to orchestrate the filtering process."""
    setup_logging()
    args = parse_arguments()

    # Parse input files
    input_files = [f.strip() for f in args.inputs.split(",")]

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
