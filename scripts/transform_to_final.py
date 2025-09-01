#!/usr/bin/env python3
"""
CLI script for transforming Phase-1 output to final 2023 dataset format.

Usage:
    python scripts/transform_to_final.py --input "filtered 2.xlsx" --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx"
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dei_extractor.transform.final_2023 import compute_final, load_phase1, write_final


def setup_logging(level: str):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def validate_against_sample(
    final_df: pd.DataFrame, sample_path: str, tolerance: float = 1e-3
):
    """
    Validate final dataset against sample file.

    Args:
        final_df: Final DataFrame to validate
        sample_path: Path to sample file for comparison
        tolerance: Tolerance for numeric comparisons
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Validating against sample file: {sample_path}")

    try:
        sample_df = pd.read_excel(sample_path, sheet_name="Sheet1")
        logger.info(
            f"Loaded sample with {len(sample_df)} rows and {len(sample_df.columns)} columns"
        )

        # Check column structure
        if len(final_df.columns) != len(sample_df.columns):
            logger.warning(
                f"Column count mismatch: final={len(final_df.columns)}, sample={len(sample_df.columns)}"
            )

        # Check column names (ignoring trailing spaces)
        final_cols = [col.strip() for col in final_df.columns]
        sample_cols = [col.strip() for col in sample_df.columns]

        if final_cols != sample_cols:
            logger.warning("Column name mismatch:")
            for i, (fcol, scol) in enumerate(zip(final_cols, sample_cols)):
                if fcol != scol:
                    logger.warning(f"  Column {i}: final='{fcol}' vs sample='{scol}'")

        # Sample validation for numeric fields (if sample has data)
        numeric_columns = [
            "ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/23",
            "ΑΡ. ΗΜΕΡΩΝ ΜΕΤΑ ΤΙΣ 31/12/2023",
            "ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ",
            "ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH",
            "ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ.",
            "ΚΑΤΑΝΑΛΩΣΗ 2023 KWH",
        ]

        # Check if sample has actual data (not all NaN)
        sample_has_data = False
        for col in numeric_columns:
            if col in sample_df.columns and sample_df[col].notna().any():
                sample_has_data = True
                break

        if sample_has_data:
            logger.info("Sample has data, performing numeric validation...")

            # For each numeric column, compare values where both sides have data
            for col in numeric_columns:
                if col in final_df.columns and col in sample_df.columns:
                    final_vals = pd.to_numeric(final_df[col], errors="coerce")
                    sample_vals = pd.to_numeric(sample_df[col], errors="coerce")

                    # Find common non-null values
                    common_mask = final_vals.notna() & sample_vals.notna()
                    if common_mask.any():
                        differences = np.abs(
                            final_vals[common_mask] - sample_vals[common_mask]
                        )
                        max_diff = differences.max()
                        mean_diff = differences.mean()

                        logger.info(
                            f"  {col}: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}"
                        )

                        if max_diff > tolerance:
                            logger.warning(
                                f"  {col}: max difference {max_diff:.6f} exceeds tolerance {tolerance}"
                            )
        else:
            logger.info(
                "Sample file appears to be empty (all NaN values), skipping numeric validation"
            )

        logger.info("Validation completed")

    except Exception as e:
        logger.error(f"Error during validation: {e}")
        raise


def validate_fop_classification(final_df: pd.DataFrame):
    """
    Validate that all ΦΟΠ entries are correctly classified as "ΟΧΙ".

    Args:
        final_df: Final DataFrame to validate
    """
    logger = logging.getLogger(__name__)
    logger.info("Validating ΦΟΠ classification...")

    # Check if ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ column exists
    if "ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ" not in final_df.columns:
        logger.warning("ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ column not found, skipping ΦΟΠ validation")
        return

    # Find all ΦΟΠ entries
    fop_mask = final_df["ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ"] == "ΦΟΠ"
    fop_count = fop_mask.sum()

    if fop_count == 0:
        logger.info("No ΦΟΠ entries found in the dataset")
        return

    logger.info(f"Found {fop_count} ΦΟΠ entries")

    # Check that all ΦΟΠ entries have ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ) = "ΟΧΙ"
    fop_entries = final_df[fop_mask]
    incorrect_classifications = fop_entries[
        fop_entries["ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)"] != "ΟΧΙ"
    ]

    if len(incorrect_classifications) > 0:
        logger.error(
            f"Found {len(incorrect_classifications)} ΦΟΠ entries incorrectly classified as infrastructure:"
        )
        for idx, row in incorrect_classifications.iterrows():
            logger.error(
                f"  Service {row['ΠΑΡΟΧΗ']}: {row['ΟΝΟΜΑ ']} - Flag: {row['ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)']}"
            )
        raise ValueError(
            f"ΦΟΠ classification validation failed: {len(incorrect_classifications)} incorrect entries"
        )
    else:
        logger.info("All ΦΟΠ entries correctly classified as 'ΟΧΙ' ✓")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Transform Phase-1 output to final 2023 dataset format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/transform_to_final.py --input "filtered 2.xlsx" --output "ΠΑΡΟΧΕΣ_2023_FINAL.xlsx"
  python scripts/transform_to_final.py --input "data.xlsx" --output "output.xlsx" --year 2022 --validate-against "sample.xlsx"
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to Phase-1 Excel file (filtered 2.xlsx)",
    )

    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path for output Excel file (ΠΑΡΟΧΕΣ_2023_FINAL.xlsx)",
    )

    parser.add_argument(
        "--year",
        type=int,
        default=2023,
        help="Target year for calculations (default: 2023)",
    )

    parser.add_argument(
        "--window-days",
        type=int,
        default=60,
        help="± window around anchors in days for selecting settlement periods (default: 60)",
    )

    parser.add_argument(
        "--target-span-days",
        type=int,
        default=365,
        help="Target total span in days between selected start/end (default: 365)",
    )

    parser.add_argument(
        "--encoding", default="utf-8-sig", help="File encoding (default: utf-8-sig)"
    )

    parser.add_argument(
        "--keep-str-ids",
        action="store_true",
        help="Keep service IDs as strings (default: convert to numeric if possible)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument("--validate-against", help="Path to sample file for validation")

    parser.add_argument(
        "--class-mapping", help="Path to custom classification mapping CSV file"
    )

    parser.add_argument(
        "--decimals-mode",
        choices=["round", "truncate"],
        default="round",
        help="Format numeric values to 2 decimals using rounding (default) or truncation",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # Validate input file exists
        if not Path(args.input).exists():
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)

        # Load Phase-1 data
        logger.info("Loading Phase-1 data...")
        df = load_phase1(args.input)

        # Compute final dataset
        logger.info("Computing final dataset...")
        final_df = compute_final(
            df,
            year=args.year,
            class_map_path=args.class_mapping,
            window_days=args.window_days,
            target_span_days=args.target_span_days,
        )

        # Write output
        logger.info("Writing final dataset...")
        write_final(final_df, args.output, decimals_mode=args.decimals_mode)

        # Validate ΦΟΠ classification
        validate_fop_classification(final_df)

        # Validate against sample if provided
        if args.validate_against:
            if Path(args.validate_against).exists():
                validate_against_sample(final_df, args.validate_against)
            else:
                logger.warning(f"Sample file not found: {args.validate_against}")

        logger.info(f"Transformation completed successfully!")
        logger.info(f"Input: {args.input}")
        logger.info(f"Output: {args.output}")
        logger.info(f"Records processed: {len(df)}")
        logger.info(f"Services in final dataset: {len(final_df)}")

    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
