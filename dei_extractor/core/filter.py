#!/usr/bin/env python3
"""
Filter DEI data to keep only Εκαθαριστικός records.

This module provides functionality to filter DEI data files,
keeping only records where the Εκαθαριστικός field is True/1/Yes,
and removing duplicate records.
"""

import argparse
import logging
import sys
from typing import List

import pandas as pd

from ..utils.logger import LoggerMixin, log_execution_time

# Constants
TRUE_SET = {"true", "1", "yes", "ναι", "t", "y"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class FilterEkatharistikos(LoggerMixin):
    """Filter DEI data to keep only Εκαθαριστικός records."""

    def __init__(self) -> None:
        """Initialize the filter."""
        super().__init__()

    def read_input_files(self, input_files: List[str]) -> pd.DataFrame:
        """Read and combine multiple input files."""
        all_data = []

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
                    self.logger.warning(f"Unsupported file format: {file_path}")
                    continue

                all_data.append(df)
                self.logger.info(f"Read {file_path} ({len(df)} rows)")

            except Exception as e:
                self.logger.error(f"Error reading {file_path}: {e}")
                continue

        if not all_data:
            return pd.DataFrame()

        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        self.logger.info(
            f"Combined {len(input_files)} files into {len(combined_df)} total rows"
        )

        return combined_df

    def ensure_consistent_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure consistent data types for key columns to prevent sorting issues."""
        # Convert ID columns to strings to prevent mixed type sorting issues
        if "ΑρΠαροχής" in df.columns:
            df["ΑρΠαροχής"] = df["ΑρΠαροχής"].astype(str)
        if "ΑρΛογαριασμού" in df.columns:
            df["ΑρΛογαριασμού"] = df["ΑρΛογαριασμού"].astype(str)

        self.logger.info("Ensured consistent data types for ID columns")
        return df

    def filter_ekatharistikos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data to keep only rows where Εκαθαριστικός is True/1/Yes."""
        if "Εκαθαριστικός" not in df.columns:
            self.logger.warning(
                "Εκαθαριστικός column not found, returning original data"
            )
            return df

        total_rows = len(df)

        # Handle different data types in Εκαθαριστικός column
        if df["Εκαθαριστικός"].dtype == bool:
            # Boolean values - keep True values
            filtered_df = df[df["Εκαθαριστικός"] == True]
        else:
            # String or mixed values - convert to string and check against TRUE_SET
            filtered_df = df[df["Εκαθαριστικός"].astype(str).str.lower().isin(TRUE_SET)]

        removed_count = total_rows - len(filtered_df)
        self.logger.info(
            f"Filtered to {len(filtered_df)} rows (removed {removed_count})"
        )

        return filtered_df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows based on merge_key or fallback to composite key."""
        # Ensure ID columns are strings to prevent sorting issues
        if "ΑρΠαροχής" in df.columns:
            df["ΑρΠαροχής"] = df["ΑρΠαροχής"].astype(str)
        if "ΑρΛογαριασμού" in df.columns:
            df["ΑρΛογαριασμού"] = df["ΑρΛογαριασμού"].astype(str)

        # Use merge_key if available, otherwise fallback to composite key
        dedup_key = []
        if "merge_key" in df.columns:
            dedup_key = ["merge_key"]
        else:
            dedup_key = [
                c
                for c in ["ΑρΠαροχής", "ΑρΛογαριασμού", "ΗμΈκδοσης"]
                if c in df.columns
            ]

        before_count = len(df)

        if dedup_key:
            df = df.drop_duplicates(subset=dedup_key, keep="first")
            removed_count = before_count - len(df)
            self.logger.info(
                f"Dropped {removed_count} duplicate rows (key: {', '.join(dedup_key)})"
            )
        else:
            df = df.drop_duplicates(keep="first")
            removed_count = before_count - len(df)
            self.logger.info(
                f"Dropped {removed_count} duplicate rows (full row comparison)"
            )

        # Re-sort using _start_date if available, otherwise by ΑρΠαροχής
        sort_cols = ["ΑρΠαροχής"]
        if "_start_date" in df.columns:
            sort_cols.append("_start_date")
        df = df.sort_values(by=sort_cols, kind="mergesort")
        self.logger.info(
            f"Re-sorted {len(df)} records by {', '.join(sort_cols)} after deduplication"
        )

        return df

    def drop_afm_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop ΑΦΜ column if present (case-insensitive)."""
        for col in list(df.columns):
            if col.strip().lower() == "αφμ":
                df = df.drop(columns=[col])
                self.logger.info("Dropped ΑΦΜ column for privacy")
                break
        return df

    def parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse ΗμΈκδοσης column to DD/MM/YYYY format if it exists."""
        if "ΗμΈκδοσης" in df.columns:
            try:
                # Create a copy of the original column for fallback
                original_dates = df["ΗμΈκδοσης"].copy()

                # Try to parse dates flexibly - let pandas infer the format
                parsed_dates = pd.to_datetime(df["ΗμΈκδοσης"], errors="coerce")

                # Convert back to string format DD/MM/YYYY for non-null values
                formatted_dates = parsed_dates.dt.strftime("%d/%m/%Y")

                # Use formatted dates where available, otherwise keep original
                # But ensure we don't have NaN values in the final result
                df["ΗμΈκδοσης"] = formatted_dates.where(
                    formatted_dates.notna(), original_dates
                )

                self.logger.info("Successfully parsed ΗμΈκδοσης dates")
            except Exception as e:
                self.logger.warning(f"Could not parse ΗμΈκδοσης dates: {e}")
        return df

    def write_outputs(
        self,
        df: pd.DataFrame,
        out_csv: str = "filtered.csv",
        out_xlsx: str = "filtered.xlsx",
    ) -> None:
        """Write filtered data to CSV and Excel files."""
        try:
            # Ensure ID columns are strings before sorting
            if "ΑρΠαροχής" in df.columns:
                df["ΑρΠαροχής"] = df["ΑρΠαροχής"].astype(str)
                df = df.sort_values(by=["ΑρΠαροχής"])
                self.logger.info(f"Sorted {len(df)} records by ΑρΠαροχής")

            # Write CSV with UTF-8 BOM
            df.to_csv(out_csv, index=False, encoding="utf-8-sig")
            self.logger.info(f"Wrote {out_csv} ({len(df)} rows)")

            # Write Excel
            df.to_excel(out_xlsx, index=False)
            self.logger.info(f"Wrote {out_xlsx}")

        except Exception as e:
            self.logger.error(f"Error writing output files: {e}")
            raise

    @log_execution_time
    def process_files(self, input_files: List[str]) -> pd.DataFrame:
        """Process input files and return filtered DataFrame."""
        # Read input files
        df = self.read_input_files(input_files)

        if df.empty:
            self.logger.warning("No data to process")
            return df

        # Ensure consistent data types first
        df = self.ensure_consistent_data_types(df)

        # Apply filters and transformations
        df = self.filter_ekatharistikos(df)
        df = self.remove_duplicates(df)
        df = self.drop_afm_column(df)
        df = self.parse_dates(df)

        return df


def main() -> None:
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Filter electricity bills data based on εκαθαριστικος field"
    )
    parser.add_argument(
        "--inputs",
        default="ολα.csv,φoπ.csv,επαγγελματικα.csv",
        help=(
            "Comma-separated list of input CSV files "
            "(default: ολα.csv,φoπ.csv,επαγγελματικα.csv)"
        ),
    )
    parser.add_argument(
        "--out-csv",
        default="filtered.csv",
        help="Output CSV file path (default: filtered.csv)",
    )
    parser.add_argument(
        "--out-xlsx",
        default="filtered.xlsx",
        help="Output Excel file path (default: filtered.xlsx)",
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        # Parse input files
        input_files = [f.strip() for f in args.inputs.split(",")]

        # Create filter and process files
        filter_tool = FilterEkatharistikos()
        df = filter_tool.process_files(input_files)

        if df.empty:
            logging.warning("No records found after filtering")
            sys.exit(0)

        # Write outputs
        filter_tool.write_outputs(df, args.out_csv, args.out_xlsx)

        logging.info("Filtering completed successfully")

    except Exception as e:
        logging.error(f"Filtering failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
