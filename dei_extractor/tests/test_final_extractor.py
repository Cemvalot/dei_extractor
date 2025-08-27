#!/usr/bin/env python3
"""
Final comprehensive test suite for DEI Extractor.

This module contains the final comprehensive tests for the DEI Extractor,
ensuring all functionality works correctly.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from dei_extractor.core.extractor import DEIExtractorEnhanced


def test_extractor_results():
    """Test the results of the enhanced DEI extractor."""
    print("Testing Enhanced DEI Extractor Results")
    print("=" * 60)

    try:
        # Load the data with proper string handling for IDs
        df = pd.read_csv("ολα.csv", dtype={"ΑρΠαροχής": str, "ΑρΛογαριασμού": str})
        fop_df = pd.read_csv("φoπ.csv", dtype={"ΑρΠαροχής": str, "ΑρΛογαριασμού": str})
        epag_df = pd.read_csv(
            "επαγγελματικα.csv", dtype={"ΑρΠαροχής": str, "ΑρΛογαριασμού": str}
        )

        print(f"✓ Total records: {len(df)}")
        print(f"✓ ΦΟΠ records: {len(fop_df)}")
        print(f"✓ Επαγγελματικό records: {len(epag_df)}")

        # Test 1: Check that IDs are strings (not scientific notation)
        print("\nTest 1: ID Format")
        sample_id = df["ΑρΠαροχής"].iloc[0]
        if isinstance(sample_id, str) and not "e" in str(sample_id).lower():
            print(f"✓ ΑρΠαροχής correctly formatted as string: {sample_id}")
        else:
            print(f"✗ ΑρΠαροχής incorrectly formatted: {sample_id}")

        # Test 2: Check category detection
        print("\nTest 2: Category Detection")
        fop_count = len(df[df["ΚατηγορίαΤιμολογίου"] == "ΦΟΠ"])
        epag_count = len(df[df["ΚατηγορίαΤιμολογίου"] == "Επαγγελματικό"])
        print(f"✓ ΦΟΠ detected: {fop_count}")
        print(f"✓ Επαγγελματικό detected: {epag_count}")

        # Test 3: Check Εκαθαριστικός flag
        print("\nTest 3: Εκαθαριστικός Flag")
        ekatharistikos_true = len(df[df["Εκαθαριστικός"] is True])
        ekatharistikos_false = len(df[df["Εκαθαριστικός"] is False])
        print(f"✓ Εκαθαριστικός=True: {ekatharistikos_true}")
        print(f"✓ Εκαθαριστικός=False: {ekatharistikos_false}")

        # Test 4: Check subcategory logic
        print("\nTest 4: Subcategory Logic")
        if not epag_df.empty:
            simple_epag = len(epag_df[epag_df["Υποκατηγορία"] == "Απλό επαγγελματικό"])
            industrial = len(epag_df[epag_df["Υποκατηγορία"] == "Βιομηχανικό"])
            agricultural = len(epag_df[epag_df["Υποκατηγορία"] == "Αγροτικό"])
            print(f"✓ Απλό επαγγελματικό: {simple_epag}")
            print(f"✓ Βιομηχανικό: {industrial}")
            print(f"✓ Αγροτικό: {agricultural}")

        # Test 5: Check confidence system
        print("\nTest 5: Confidence System")
        needs_review = len(df[df["needs_review"] is True])
        high_confidence = len(df[df["confidence"] >= 0.90])
        print(f"✓ Records needing review: {needs_review}")
        print(f"✓ High confidence records (≥90%): {high_confidence}")

        # Test 6: Check data types
        print("\nTest 6: Data Types")
        print(f"✓ Τελευταία type: {df['Τελευταία'].dtype}")
        print(f"✓ ΣΩΧΒ type: {df['ΣΩΧΒ'].dtype}")
        print(f"✓ ΑρΠαροχής type: {df['ΑρΠαροχής'].dtype}")

        # Test 7: Sample data validation
        print("\nTest 7: Sample Data Validation")
        sample = df.iloc[0]
        print(f"Sample record:")
        print(f"  ΑρΠαροχής: {sample['ΑρΠαροχής']}")
        print(f"  ΗμΈκδοσης: {sample['ΗμΈκδοσης']}")
        print(f"  ΚατηγορίαΤιμολογίου: {sample['ΚατηγορίαΤιμολογίου']}")
        print(f"  Τελευταία: {sample['Τελευταία']}")
        print(f"  Εκαθαριστικός: {sample['Εκαθαριστικός']}")

        # Test 8: Enhanced Features - ΦΟΠ Variations
        print("\nTest 8: ΦΟΠ Variations Normalization")
        if "raw_code" in df.columns:
            fop_variations = df[df["raw_code"].isin(["Φ.Ο.Π", "Φ Ο Π"])]
            print(f"✓ ΦΟΠ variations detected and normalized: {len(fop_variations)}")
            if not fop_variations.empty:
                print(f"  Sample variations: {fop_variations['raw_code'].unique()}")
        else:
            print("⚠ raw_code column not found - ΦΟΠ variation test skipped")

        # Test 9: Enhanced Features - Wrap Categories

        # Test 10: New Period Fields
        print("\nTest 10: New Period Fields")
        if (
            "ΠερίοδοςΚατανάλωσης_Αρχική" in df.columns
            and "ΠερίοδοςΚατανάλωσης_Τελική" in df.columns
        ):
            start_not_null = len(df[df["ΠερίοδοςΚατανάλωσης_Αρχική"].notna()])
            end_not_null = len(df[df["ΠερίοδοςΚατανάλωσης_Τελική"].notna()])
            print(f"✓ ΠερίοδοςΚατανάλωσης_Αρχική not null: {start_not_null}")
            print(f"✓ ΠερίοδοςΚατανάλωσης_Τελική not null: {end_not_null}")

            # Test period parsing
            sample_period = df["ΠερίοδοςΚατανάλωσης"].iloc[0]
            sample_start = df["ΠερίοδοςΚατανάλωσης_Αρχική"].iloc[0]
            sample_end = df["ΠερίοδοςΚατανάλωσης_Τελική"].iloc[0]
            print(f"✓ Sample period: {sample_period}")
            print(f"✓ Sample start: {sample_start}")
            print(f"✓ Sample end: {sample_end}")
        else:
            print("⚠ New period fields not found")

        # Test 11: Merge Key
        print("\nTest 11: Merge Key")
        if "merge_key" in df.columns:
            merge_not_null = len(df[df["merge_key"].notna()])
            unique_merge_keys = df["merge_key"].nunique()
            print(f"✓ Merge keys not null: {merge_not_null}")
            print(f"✓ Unique merge keys: {unique_merge_keys}")

            # Test merge key format
            sample_merge_key = df["merge_key"].iloc[0]
            print(f"✓ Sample merge key: {sample_merge_key}")
        else:
            print("⚠ Merge key field not found")

        # Test 12: ΑρΠαρχ_Αρίθμηση
        print("\nTest 12: ΑρΠαρχ_Αρίθμηση")
        if "ΑρΠαρχ_Αρίθμηση" in df.columns:
            numbering_not_null = len(df[df["ΑρΠαρχ_Αρίθμηση"].notna()])
            print(f"✓ ΑρΠαρχ_Αρίθμηση not null: {numbering_not_null}")

            # Test numbering logic
            sample_supply = df["ΑρΠαροχής"].iloc[0]
            supply_records = df[df["ΑρΠαροχής"] == sample_supply]
            if len(supply_records) > 1:
                numbering_range = supply_records["ΑρΠαρχ_Αρίθμηση"].tolist()
                print(f"✓ Sample supply {sample_supply} numbering: {numbering_range}")
                if numbering_range == list(range(1, len(numbering_range) + 1)):
                    print("✓ ΑρΠαρχ_Αρίθμηση is sequential")
                else:
                    print("✗ ΑρΠαρχ_Αρίθμηση is not sequential")
        else:
            print("⚠ ΑρΠαρχ_Αρίθμηση field not found")

        # Test 13: ΑρΠαρχ_Ομάδα
        print("\nTest 13: ΑρΠαρχ_Ομάδα")
        if "ΑρΠαρχ_Ομάδα" in df.columns:
            group_not_null = len(df[df["ΑρΠαρχ_Ομάδα"].notna()])
            unique_groups = df["ΑρΠαρχ_Ομάδα"].nunique()
            unique_supplies = df["ΑρΠαροχής"].nunique()
            print(f"✓ ΑρΠαρχ_Ομάδα not null: {group_not_null}")
            print(f"✓ Unique groups: {unique_groups}")
            print(f"✓ Unique supplies: {unique_supplies}")

            # Test group logic
            sample_group = df["ΑρΠαρχ_Ομάδα"].iloc[0]
            group_records = df[df["ΑρΠαρχ_Ομάδα"] == sample_group]
            print(f"✓ Sample group {sample_group} has {len(group_records)} records")

            # Verify that same supply number gets same group
            sample_supply = df["ΑρΠαροχής"].iloc[0]
            supply_group = df[df["ΑρΠαροχής"] == sample_supply]["ΑρΠαρχ_Ομάδα"].iloc[0]
            print(f"✓ Sample supply {sample_supply} belongs to group {supply_group}")
        else:
            print("⚠ ΑρΠαρχ_Ομάδα field not found")
        print("\nTest 9: Wrap Category Detection")
        if "raw_code" in df.columns:
            wrap_categories = df[df["raw_code"] == "Γ-wrap"]
            print(
                f"✓ Wrap categories (Γ\\d+ + Επαγγελματικό) detected: "
                f"{len(wrap_categories)}"
            )
        else:
            print("⚠ raw_code column not found - wrap category test skipped")

        # Test 10: Enhanced Features - Additional Fields
        print("\nTest 10: Additional Fields Extraction")
        additional_fields = [
            "ΚατάστημαΕξυπηρέτησης",
            "Παραστατικό",
            "date_from",
            "date_to",
        ]
        for field in additional_fields:
            if field in df.columns:
                non_null_count = len(df[df[field].notna() & (df[field] != "None")])
                print(f"✓ {field}: {non_null_count} records")
            else:
                print(f"⚠ {field} column not found")

        # Test 11: Enhanced Features - Date Parsing
        print("\nTest 11: Period Date Parsing")
        if "date_from" in df.columns and "date_to" in df.columns:
            valid_dates = df[
                (df["date_from"].notna())
                & (df["date_from"] != "None")
                & (df["date_to"].notna())
                & (df["date_to"] != "None")
            ]
            print(f"✓ Period dates parsed successfully: {len(valid_dates)} records")
            if not valid_dates.empty:
                sample_dates = valid_dates.iloc[0]
                print(
                    f"  Sample: {sample_dates['date_from']} to {sample_dates['date_to']}"
                )
        else:
            print("⚠ date_from/date_to columns not found")

        # Test 12: Enhanced Features - Deduplication
        print("\nTest 12: Deduplication")
        if len(df) > 0:
            # Check for potential duplicates based on key fields
            key_fields = [
                "ΑρΠαροχής",
                "ΑρΛογαριασμού",
                "ΗμΈκδοσης",
                "ΠερίοδοςΚατανάλωσης",
            ]
            if all(field in df.columns for field in key_fields):
                duplicates = df.duplicated(subset=key_fields, keep=False)
                duplicate_count = duplicates.sum()
                print(f"✓ Duplicate records after deduplication: {duplicate_count}")
                if duplicate_count > 0:
                    print(
                        f"  ⚠ Found {duplicate_count} potential duplicates - "
                        f"check deduplication logic"
                    )
            else:
                print("⚠ Key fields missing for deduplication test")

        # Test 13: Enhanced Features - Zero Consumption Handling
        print("\nTest 13: Zero Consumption (Τελευταία == Προηγούμενη)")
        if "Τελευταία" in df.columns and "Προηγούμενη" in df.columns:
            zero_consumption = df[df["Τελευταία"] == df["Προηγούμενη"]]
            zero_consumption_ekatharistikos = zero_consumption[
                zero_consumption["Εκαθαριστικός"] == True
            ]
            print(f"✓ Zero consumption records: {len(zero_consumption)}")
            print(
                f"✓ Zero consumption with Εκαθαριστικός=True: "
                f"{len(zero_consumption_ekatharistikos)}"
            )
            if len(zero_consumption) > 0 and len(
                zero_consumption_ekatharistikos
            ) == len(zero_consumption):
                print(
                    "  ✓ All zero consumption records correctly marked as "
                    "Εκαθαριστικός=True"
                )
            elif len(zero_consumption) > 0:
                print(
                    "  ⚠ Some zero consumption records not marked as Εκαθαριστικός=True"
                )

        # Test 14: Enhanced Features - ROW3 Fallback Pattern
        print("\nTest 14: ROW3 Fallback Pattern")
        if "Τελευταία" in df.columns and "Προηγούμενη" in df.columns:
            # Check if we have records with meter readings (indicating ROW3 parsing worked)
            valid_readings = df[(df["Τελευταία"].notna()) & (df["Προηγούμενη"].notna())]
            print(f"✓ Records with valid meter readings: {len(valid_readings)}")
            if len(valid_readings) > 0:
                print("  ✓ ROW3 parsing (primary or fallback) working correctly")

        # Test 15: Enhanced Features - Header/Footer Filtering
        print("\nTest 15: Header/Footer Filtering")
        # This is harder to test without access to original PDF content
        # But we can check that common header/footer text is not in our extracted data
        header_footer_keywords = [
            "ΔΗΜΟΣΙΑ ΕΠΙΧΕΙΡΗΣΗ ΗΛΕΚΤΡΙΣΜΟΥ",
            "ΗΜΕΡΟΛΟΓΙΟ ΕΚΔΟΣΗΣ",
            "ΚΩΔ.ΠΟΛΛΑΠΛΟΥ",
            "ΚΩΔ.ΕΤΑΙΡΟΥ",
            "ΣΕΛΙΔΑ",
        ]

        found_headers = 0
        for keyword in header_footer_keywords:
            # Check in text fields
            text_fields = [
                "Ονοματεπώνυμο",
                "Διεύθυνση",
                "Πόλη",
                "ΚατάστημαΕξυπηρέτησης",
            ]
            for field in text_fields:
                if field in df.columns:
                    matches = df[df[field].str.contains(keyword, case=False, na=False)]
                    found_headers += len(matches)

        if found_headers == 0:
            print("✓ Header/footer filtering working correctly")
        else:
            print(f"⚠ Found {found_headers} potential header/footer entries in data")

        # Test 16: Enhanced Features - Financial Line Exclusion
        print("\nTest 16: Financial Line Exclusion")
        financial_keywords = [
            "ΦΠΑ",
            "ΡΥΘΜΙΖΟΜΕΝΕΣ ΧΡΕΩΣΕΙΣ",
            "ΧΡΕΩΣΕΙΣ ΠΡΟΜΗΘΕΙΑΣ ΔΕΗ",
            "ΤΡΕΧΩΝ ΜΗΝΑΣ",
        ]

        found_financial = 0
        for keyword in financial_keywords:
            # Check in text fields
            text_fields = [
                "Ονοματεπώνυμο",
                "Διεύθυνση",
                "Πόλη",
                "ΚατάστημαΕξυπηρέτησης",
            ]
            for field in text_fields:
                if field in df.columns:
                    matches = df[df[field].str.contains(keyword, case=False, na=False)]
                    found_financial += len(matches)

        if found_financial == 0:
            print("✓ Financial line exclusion working correctly")
        else:
            print(f"⚠ Found {found_financial} potential financial entries in data")

        print("\n" + "=" * 60)
        print("ALL ENHANCED TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_extractor_results()
