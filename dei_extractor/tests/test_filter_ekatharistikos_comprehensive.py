#!/usr/bin/env python3
"""
Comprehensive test suite for DEI Filter functionality.

This module contains extensive tests for the DEI Filter functionality,
including data filtering, validation, and processing capabilities.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd

from dei_extractor.core.filter import FilterEkatharistikos

# Sample data for testing
SAMPLE_DATA = {
    "ΑρΠαροχής": ["1234567890", "0987654321", "1122334455"],
    "ΑρΛογαριασμού": ["987654321", "123456789", "5544332211"],
    "ΗμΈκδοσης": ["01/01/2024", "02/01/2024", "03/01/2024"],
    "Εκαθαριστικός": ["True", "False", "True"],
    "Όνομα": ["John Doe", "Jane Smith", "Bob Johnson"],
    "Διεύθυνση": ["Athens", "Thessaloniki", "Patras"],
    "Κατανάλωση": [100, 150, 200],
}


class TestFilterEkatharistikosComprehensive(unittest.TestCase):
    """Comprehensive test suite for filter_ekatharistikos with edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

        # Create sample test data
        self.sample_data = pd.DataFrame(
            {
                "ΑρΠαροχής": ["1234567890", "9876543210", "1234567890", "5555555555"],
                "ΑρΛογαριασμού": ["111111111", "222222222", "333333333", "444444444"],
                "ΗμΈκδοσης": ["01/01/2024", "02/01/2024", "03/01/2024", "04/01/2024"],
                "ΠερίοδοςΚατανάλωσης": [
                    "01.01.2024-31.01.2024",
                    "01.02.2024-29.02.2024",
                    "01.03.2024-31.03.2024",
                    "01.04.2024-30.04.2024",
                ],
                "Ονοματεπώνυμο_Διεύθυνση": [
                    "Customer 1",
                    "Customer 2",
                    "Customer 3",
                    "Customer 4",
                ],
                "Πόλη": ["City 1", "City 2", "City 3", "City 4"],
                "Τελευταία": [1234, 5678, 9999, 1111],
                "Προηγούμενη": [1000, 5000, 9000, 1000],
                "ΣΩΧΒ": [1, 2, 1, 1],
                "ΣυνΩΧΒ": [234, 678, 999, 111],
                "ΚατηγορίαΤιμολογίου": ["ΦΟΠ", "Επαγγελματικό", "ΦΟΠ", "Επαγγελματικό"],
                "Υποκατηγορία": [None, "Βιομηχανικό", None, "Απλό επαγγελματικό"],
                "Εκαθαριστικός": [True, True, False, True],
                "source_file": ["test1.pdf", "test2.pdf", "test3.pdf", "test4.pdf"],
                "raw_code": ["ΦΟΠ", "Γ21", "ΦΟΠ", "Γ22"],
                "raw_label": [
                    "Τιμολόγιο",
                    "Επαγγελματικό",
                    "Τιμολόγιο",
                    "Επαγγελματικό",
                ],
            }
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up any temporary files
        for temp_file in self.test_data_dir.glob("temp_*"):
            temp_file.unlink(missing_ok=True)

    def test_normalize_bool_edge_cases(self):
        """Test boolean normalization with extensive edge cases."""
        # Test True values
        true_cases = [
            True,
            "true",
            "1",
            "ναι",
            "nai",
            "yes",
            "y",
            "t",
            "TRUE",
            "YES",
            "ΝΑΙ",
        ]

        for value in true_cases:
            with self.subTest(value=value):
                result = normalize_bool(value)
                self.assertEqual(result, True)

        # Test False values
        false_cases = [
            False,
            "false",
            "0",
            "όχι",
            "oxi",
            "no",
            "n",
            "f",
            "FALSE",
            "NO",
            "ΟΧΙ",
        ]

        for value in false_cases:
            with self.subTest(value=value):
                result = normalize_bool(value)
                self.assertEqual(result, False)

        # Test None/Invalid values
        none_cases = [None, "", "invalid", "maybe", "unknown", "?", "null", "NULL"]

        for value in none_cases:
            with self.subTest(value=value):
                result = normalize_bool(value)
                self.assertIsNone(result)

        # Test pandas NaN
        import numpy as np

        result = normalize_bool(np.nan)
        self.assertIsNone(result)

        # Test float NaN
        result = normalize_bool(float("nan"))
        self.assertIsNone(result)

    def test_setup_logging(self):
        """Test logging setup."""
        # Test that setup_logging doesn't raise exceptions
        try:
            setup_logging()
            # Should not raise an exception
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"setup_logging raised an exception: {e}")

    def test_parse_arguments_edge_cases(self):
        """Test argument parsing with edge cases."""
        # Test default arguments
        with patch("sys.argv", ["filter_ekatharistikos.py"]):
            args = parse_arguments()
            self.assertEqual(args.inputs, "ολα.csv,φoπ.csv,επαγγελματικα.csv")
            self.assertEqual(args.out_csv, "filtered.csv")
            self.assertEqual(args.out_xlsx, "filtered.xlsx")

        # Test custom arguments
        with patch(
            "sys.argv",
            [
                "filter_ekatharistikos.py",
                "--inputs",
                "custom1.csv,custom2.csv",
                "--out-csv",
                "custom_output.csv",
                "--out-xlsx",
                "custom_output.xlsx",
            ],
        ):
            args = parse_arguments()
            self.assertEqual(args.inputs, "custom1.csv,custom2.csv")
            self.assertEqual(args.out_csv, "custom_output.csv")
            self.assertEqual(args.out_xlsx, "custom_output.xlsx")

    def test_read_input_files_edge_cases(self):
        """Test input file reading with edge cases."""
        # Test with existing files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f1:
            f1.write(self.sample_data.to_csv(index=False, encoding="utf-8-sig"))
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f2:
            f2.write(self.sample_data.to_csv(index=False, encoding="utf-8-sig"))
            temp_file2 = f2.name

        try:
            df, found_files = read_input_files([temp_file1, temp_file2])
            self.assertIsNotNone(df)
            self.assertEqual(len(found_files), 2)
            self.assertEqual(len(df), len(self.sample_data) * 2)  # Two files
        finally:
            os.unlink(temp_file1)
            os.unlink(temp_file2)

        # Test with non-existent files
        df, found_files = read_input_files(["nonexistent1.csv", "nonexistent2.csv"])
        self.assertIsNone(df)
        self.assertEqual(len(found_files), 0)

        # Test with mixed existing and non-existing files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(self.sample_data.to_csv(index=False, encoding="utf-8-sig"))
            temp_file = f.name

        try:
            df, found_files = read_input_files([temp_file, "nonexistent.csv"])
            self.assertIsNotNone(df)
            self.assertEqual(len(found_files), 1)
            self.assertEqual(len(df), len(self.sample_data))
        finally:
            os.unlink(temp_file)

        # Test with empty file list
        df, found_files = read_input_files([])
        self.assertIsNone(df)
        self.assertEqual(len(found_files), 0)

    def test_filter_ekatharistikos_edge_cases(self):
        """Test Εκαθαριστικός filtering with edge cases."""
        # Test with mixed boolean values
        mixed_data = pd.DataFrame(
            {
                "Εκαθαριστικός": [
                    True,
                    False,
                    "true",
                    "false",
                    "1",
                    "0",
                    "ναι",
                    "όχι",
                    None,
                    "invalid",
                ]
            }
        )

        result = filter_ekatharistikos(mixed_data)
        # Should only keep True values (normalized)
        expected_true_count = 4  # True, 'true', '1', 'ναι'
        self.assertEqual(len(result), expected_true_count)

        # Test with all False values
        all_false_data = pd.DataFrame(
            {"Εκαθαριστικός": [False, "false", "0", "όχι", "no"]}
        )

        result = filter_ekatharistikos(all_false_data)
        self.assertEqual(len(result), 0)

        # Test with all True values
        all_true_data = pd.DataFrame(
            {"Εκαθαριστικός": [True, "true", "1", "ναι", "yes"]}
        )

        result = filter_ekatharistikos(all_true_data)
        self.assertEqual(len(result), 5)

        # Test with missing Εκαθαριστικός column
        no_column_data = pd.DataFrame(
            {"ΑρΠαροχής": ["1234567890"], "Other_Column": ["value"]}
        )

        with self.assertRaises(KeyError):
            filter_ekatharistikos(no_column_data)

        # Test with empty DataFrame
        empty_data = pd.DataFrame()
        with self.assertRaises(KeyError):
            filter_ekatharistikos(empty_data)

    def test_remove_duplicates_edge_cases(self):
        """Test duplicate removal with edge cases."""
        # Test with complete composite key
        duplicate_data = pd.DataFrame(
            {
                "ΑρΠαροχής": ["1234567890", "1234567890", "9876543210", "1234567890"],
                "ΑρΛογαριασμού": ["111111111", "111111111", "222222222", "111111111"],
                "ΗμΈκδοσης": ["01/01/2024", "01/01/2024", "02/01/2024", "01/01/2024"],
                "Other_Column": ["A", "B", "C", "A"],  # Same as first row
            }
        )

        result = remove_duplicates(duplicate_data)
        # Should keep first occurrence of each duplicate
        self.assertEqual(len(result), 2)

        # Test with missing composite key columns
        incomplete_data = pd.DataFrame(
            {"ΑρΠαροχής": ["1234567890", "1234567890"], "Other_Column": ["A", "B"]}
        )

        result = remove_duplicates(incomplete_data)
        # Should use full row comparison
        self.assertEqual(len(result), 2)

        # Test with no duplicates
        no_duplicates_data = pd.DataFrame(
            {
                "ΑρΠαροχής": ["1234567890", "9876543210"],
                "ΑρΛογαριασμού": ["111111111", "222222222"],
                "ΗμΈκδοσης": ["01/01/2024", "02/01/2024"],
            }
        )

        result = remove_duplicates(no_duplicates_data)
        self.assertEqual(len(result), 2)

        # Test with empty DataFrame
        empty_data = pd.DataFrame()
        result = remove_duplicates(empty_data)
        self.assertEqual(len(result), 0)

        # Test with single row
        single_row_data = pd.DataFrame(
            {
                "ΑρΠαροχής": ["1234567890"],
                "ΑρΛογαριασμού": ["111111111"],
                "ΗμΈκδοσης": ["01/01/2024"],
            }
        )

        result = remove_duplicates(single_row_data)
        self.assertEqual(len(result), 1)

    def test_drop_afm_column_edge_cases(self):
        """Test ΑΦΜ column dropping with edge cases."""
        # Test with ΑΦΜ column (case insensitive)
        afm_data = pd.DataFrame(
            {
                "ΑρΠαροχής": ["1234567890"],
                "ΑΦΜ": ["123456789"],
                "Other_Column": ["value"],
            }
        )

        result = drop_afm_column(afm_data)
        self.assertNotIn("ΑΦΜ", result.columns)
        self.assertIn("ΑρΠαροχής", result.columns)
        self.assertIn("Other_Column", result.columns)

        # Test with different case variations
        afm_variations = ["αφμ", "Αφμ", "αΦμ", "ΑΦΜ"]
        for afm_col in afm_variations:
            with self.subTest(afm_col=afm_col):
                test_data = pd.DataFrame(
                    {
                        "ΑρΠαροχής": ["1234567890"],
                        afm_col: ["123456789"],
                        "Other_Column": ["value"],
                    }
                )

                result = drop_afm_column(test_data)
                self.assertNotIn(afm_col, result.columns)

        # Test without ΑΦΜ column
        no_afm_data = pd.DataFrame(
            {"ΑρΠαροχής": ["1234567890"], "Other_Column": ["value"]}
        )

        result = drop_afm_column(no_afm_data)
        self.assertEqual(len(result.columns), 2)  # No change

        # Test with empty DataFrame
        empty_data = pd.DataFrame()
        result = drop_afm_column(empty_data)
        self.assertEqual(len(result.columns), 0)

    def test_parse_dates_edge_cases(self):
        """Test date parsing with edge cases."""
        # Test valid date formats
        valid_data = pd.DataFrame(
            {"ΗμΈκδοσης": ["01/01/2024", "31/12/2023", "29/02/2024"]}  # Leap year
        )

        result = parse_dates(valid_data)
        # Should not raise exceptions and should preserve valid dates
        self.assertIn("ΗμΈκδοσης", result.columns)

        # Test invalid date formats
        invalid_data = pd.DataFrame(
            {
                "ΗμΈκδοσης": [
                    "invalid",
                    "32/01/2024",
                    "01/13/2024",
                    "2024-01-01",
                ]  # Wrong format
            }
        )

        result = parse_dates(invalid_data)
        # Should handle invalid dates gracefully
        self.assertIn("ΗμΈκδοσης", result.columns)

        # Test without ΗμΈκδοσης column
        no_date_data = pd.DataFrame(
            {"ΑρΠαροχής": ["1234567890"], "Other_Column": ["value"]}
        )

        result = parse_dates(no_date_data)
        self.assertNotIn("ΗμΈκδοσης", result.columns)

        # Test with empty DataFrame
        empty_data = pd.DataFrame()
        result = parse_dates(empty_data)
        self.assertEqual(len(result.columns), 0)

        # Test with mixed valid/invalid dates
        mixed_data = pd.DataFrame(
            {"ΗμΈκδοσης": ["01/01/2024", "invalid", "31/12/2023", "32/01/2024"]}
        )

        result = parse_dates(mixed_data)
        self.assertIn("ΗμΈκδοσης", result.columns)

    def test_write_output_files_edge_cases(self):
        """Test output file writing with edge cases."""
        # Test with normal data
        with tempfile.TemporaryDirectory() as temp_dir:
            out_csv = os.path.join(temp_dir, "test_output.csv")
            out_xlsx = os.path.join(temp_dir, "test_output.xlsx")

            write_output_files(self.sample_data, out_csv, out_xlsx)

            # Check that files were created
            self.assertTrue(os.path.exists(out_csv))
            self.assertTrue(os.path.exists(out_xlsx))

            # Check that data was written correctly
            written_df = pd.read_csv(out_csv, encoding="utf-8-sig")
            self.assertEqual(len(written_df), len(self.sample_data))

        # Test with empty DataFrame
        with tempfile.TemporaryDirectory() as temp_dir:
            out_csv = os.path.join(temp_dir, "empty_output.csv")
            out_xlsx = os.path.join(temp_dir, "empty_output.xlsx")

            empty_df = pd.DataFrame()
            write_output_files(empty_df, out_csv, out_xlsx)

            # Check that files were created (even if empty)
            self.assertTrue(os.path.exists(out_csv))
            self.assertTrue(os.path.exists(out_xlsx))

        # Test with DataFrame missing ΑρΠαροχής column
        with tempfile.TemporaryDirectory() as temp_dir:
            out_csv = os.path.join(temp_dir, "no_id_output.csv")
            out_xlsx = os.path.join(temp_dir, "no_id_output.xlsx")

            no_id_df = pd.DataFrame({"Other_Column": ["value"]})
            write_output_files(no_id_df, out_csv, out_xlsx)

            # Should not raise an exception
            self.assertTrue(os.path.exists(out_csv))
            self.assertTrue(os.path.exists(out_xlsx))

    def test_comprehensive_integration(self):
        """Test comprehensive integration with real-world scenarios."""
        # Create comprehensive test scenario
        comprehensive_data = pd.DataFrame(
            {
                "ΑρΠαροχής": [
                    "1234567890",
                    "1234567890",
                    "9876543210",
                    "5555555555",
                    "1234567890",
                ],
                "ΑρΛογαριασμού": [
                    "111111111",
                    "222222222",
                    "333333333",
                    "444444444",
                    "111111111",
                ],
                "ΗμΈκδοσης": [
                    "01/01/2024",
                    "02/01/2024",
                    "03/01/2024",
                    "04/01/2024",
                    "01/01/2024",
                ],
                "ΠερίοδοςΚατανάλωσης": [
                    "01.01.2024-31.01.2024",
                    "01.02.2024-29.02.2024",
                    "01.03.2024-31.03.2024",
                    "01.04.2024-30.04.2024",
                    "01.01.2024-31.01.2024",
                ],
                "Ονοματεπώνυμο_Διεύθυνση": [
                    "Customer 1",
                    "Customer 2",
                    "Customer 3",
                    "Customer 4",
                    "Customer 1",
                ],
                "Πόλη": ["City 1", "City 2", "City 3", "City 4", "City 1"],
                "Τελευταία": [1234, 5678, 9999, 1111, 1234],
                "Προηγούμενη": [1000, 5000, 9000, 1000, 1000],
                "ΣΩΧΒ": [1, 2, 1, 1, 1],
                "ΣυνΩΧΒ": [234, 678, 999, 111, 234],
                "ΚατηγορίαΤιμολογίου": [
                    "ΦΟΠ",
                    "Επαγγελματικό",
                    "ΦΟΠ",
                    "Επαγγελματικό",
                    "ΦΟΠ",
                ],
                "Υποκατηγορία": [None, "Βιομηχανικό", None, "Απλό επαγγελματικό", None],
                "Εκαθαριστικός": [
                    True,
                    True,
                    False,
                    True,
                    True,
                ],  # One False, rest True
                "ΑΦΜ": [
                    "123456789",
                    "987654321",
                    "555555555",
                    "111111111",
                    "123456789",
                ],  # Should be dropped
                "source_file": [
                    "test1.pdf",
                    "test2.pdf",
                    "test3.pdf",
                    "test4.pdf",
                    "test1.pdf",
                ],
                "raw_code": ["ΦΟΠ", "Γ21", "ΦΟΠ", "Γ22", "ΦΟΠ"],
                "raw_label": [
                    "Τιμολόγιο",
                    "Επαγγελματικό",
                    "Τιμολόγιο",
                    "Επαγγελματικό",
                    "Τιμολόγιο",
                ],
            }
        )

        # Test full pipeline
        # 1. Filter Εκαθαριστικός
        filtered_data = filter_ekatharistikos(comprehensive_data)
        self.assertEqual(len(filtered_data), 4)  # 5 total - 1 False = 4

        # 2. Remove duplicates
        deduplicated_data = remove_duplicates(filtered_data)
        self.assertEqual(len(deduplicated_data), 3)  # 4 filtered - 1 duplicate = 3

        # 3. Drop ΑΦΜ column
        no_afm_data = drop_afm_column(deduplicated_data)
        self.assertNotIn("ΑΦΜ", no_afm_data.columns)

        # 4. Parse dates
        parsed_data = parse_dates(no_afm_data)
        self.assertIn("ΗμΈκδοσης", parsed_data.columns)

        # 5. Write output files
        with tempfile.TemporaryDirectory() as temp_dir:
            out_csv = os.path.join(temp_dir, "comprehensive_output.csv")
            out_xlsx = os.path.join(temp_dir, "comprehensive_output.xlsx")

            write_output_files(parsed_data, out_csv, out_xlsx)

            # Verify output
            self.assertTrue(os.path.exists(out_csv))
            self.assertTrue(os.path.exists(out_xlsx))

            # Read back and verify
            output_df = pd.read_csv(out_csv, encoding="utf-8-sig")
            self.assertEqual(len(output_df), 3)
            self.assertNotIn("ΑΦΜ", output_df.columns)
            self.assertIn("ΑρΠαροχής", output_df.columns)
            self.assertIn("ΗμΈκδοσης", output_df.columns)


class TestFilterEkatharistikosPerformance(unittest.TestCase):
    """Performance tests for filter_ekatharistikos."""

    def setUp(self):
        """Set up test fixtures."""
        # Create large test dataset
        self.large_data = pd.DataFrame(
            {
                "ΑρΠαροχής": [f"123456789{i:03d}" for i in range(10000)],
                "ΑρΛογαριασμού": [f"987654321{i:03d}" for i in range(10000)],
                "ΗμΈκδοσης": ["01/01/2024"] * 10000,
                "ΠερίοδοςΚατανάλωσης": ["01.01.2024-31.01.2024"] * 10000,
                "Ονοματεπώνυμο_Διεύθυνση": [f"Customer {i}" for i in range(10000)],
                "Πόλη": [f"City {i}" for i in range(10000)],
                "Τελευταία": [1000 + i for i in range(10000)],
                "Προηγούμενη": [i for i in range(10000)],
                "ΣΩΧΒ": [1] * 10000,
                "ΣυνΩΧΒ": [1000 + i for i in range(10000)],
                "ΚατηγορίαΤιμολογίου": ["ΦΟΠ"] * 5000 + ["Επαγγελματικό"] * 5000,
                "Υποκατηγορία": [None] * 5000 + ["Απλό επαγγελματικό"] * 5000,
                "Εκαθαριστικός": [True] * 7000 + [False] * 3000,  # 70% True, 30% False
                "ΑΦΜ": [f"123456789{i:03d}" for i in range(10000)],
                "source_file": ["test.pdf"] * 10000,
                "raw_code": ["ΦΟΠ"] * 5000 + ["Γ21"] * 5000,
                "raw_label": ["Τιμολόγιο"] * 5000 + ["Επαγγελματικό"] * 5000,
            }
        )

    def test_large_data_processing(self):
        """Test processing of large datasets."""
        # Test filtering
        filtered_data = filter_ekatharistikos(self.large_data)
        self.assertEqual(len(filtered_data), 7000)  # 70% of 10000

        # Test deduplication
        deduplicated_data = remove_duplicates(filtered_data)
        self.assertEqual(len(deduplicated_data), 7000)  # No duplicates in test data

        # Test ΑΦΜ column dropping
        no_afm_data = drop_afm_column(deduplicated_data)
        self.assertNotIn("ΑΦΜ", no_afm_data.columns)

        # Test date parsing
        parsed_data = parse_dates(no_afm_data)
        self.assertIn("ΗμΈκδοσης", parsed_data.columns)

    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Process large dataset
        self.test_large_data_processing()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 200MB)
        self.assertLess(memory_increase, 200 * 1024 * 1024)

    def test_duplicate_heavy_scenario(self):
        """Test performance with many duplicates."""
        # Create data with many duplicates
        duplicate_heavy_data = pd.DataFrame(
            {
                "ΑρΠαροχής": ["1234567890"] * 1000
                + ["9876543210"] * 1000
                + ["5555555555"] * 1000,
                "ΑρΛογαριασμού": ["111111111"] * 1000
                + ["222222222"] * 1000
                + ["333333333"] * 1000,
                "ΗμΈκδοσης": ["01/01/2024"] * 3000,
                "ΠερίοδοςΚατανάλωσης": ["01.01.2024-31.01.2024"] * 3000,
                "Ονοματεπώνυμο_Διεύθυνση": ["Customer 1"] * 1000
                + ["Customer 2"] * 1000
                + ["Customer 3"] * 1000,
                "Πόλη": ["City 1"] * 1000 + ["City 2"] * 1000 + ["City 3"] * 1000,
                "Τελευταία": [1234] * 3000,
                "Προηγούμενη": [1000] * 3000,
                "ΣΩΧΒ": [1] * 3000,
                "ΣυνΩΧΒ": [234] * 3000,
                "ΚατηγορίαΤιμολογίου": ["ΦΟΠ"] * 3000,
                "Υποκατηγορία": [None] * 3000,
                "Εκαθαριστικός": [True] * 3000,
                "ΑΦΜ": ["123456789"] * 3000,
                "source_file": ["test.pdf"] * 3000,
                "raw_code": ["ΦΟΠ"] * 3000,
                "raw_label": ["Τιμολόγιο"] * 3000,
            }
        )

        # Test filtering
        filtered_data = filter_ekatharistikos(duplicate_heavy_data)
        self.assertEqual(len(filtered_data), 3000)

        # Test deduplication (should reduce to 3 unique records)
        deduplicated_data = remove_duplicates(filtered_data)
        self.assertEqual(len(deduplicated_data), 3)


class TestFilterEkatharistikosErrorHandling(unittest.TestCase):
    """Error handling tests for filter_ekatharistikos."""

    def test_file_reading_errors(self):
        """Test handling of file reading errors."""
        # Test with corrupted CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("invalid,csv,format\nwith,wrong,structure")
            corrupted_file = f.name

        try:
            df, found_files = read_input_files([corrupted_file])
            # Should handle gracefully and return None
            self.assertIsNone(df)
        finally:
            os.unlink(corrupted_file)

        # Test with permission denied
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("ΑρΠαροχής,Εκαθαριστικός\n1234567890,True")
            protected_file = f.name

        try:
            # Make file read-only
            os.chmod(protected_file, 0o000)

            df, found_files = read_input_files([protected_file])
            # Should handle gracefully
            self.assertIsNone(df)
        finally:
            # Restore permissions and clean up
            os.chmod(protected_file, 0o644)
            os.unlink(protected_file)

    def test_boolean_normalization_errors(self):
        """Test handling of boolean normalization errors."""
        # Test with non-string/non-bool types
        test_cases = [
            123,  # Integer
            3.14,  # Float
            [],  # Empty list
            {},  # Empty dict
            object(),  # Custom object
        ]

        for value in test_cases:
            with self.subTest(value=value):
                result = normalize_bool(value)
                # Should handle gracefully and return None
                self.assertIsNone(result)

    def test_date_parsing_errors(self):
        """Test handling of date parsing errors."""
        # Test with various invalid date formats
        invalid_dates = [
            "invalid",
            "2024/01/01",  # Wrong separator
            "01-01-2024",  # Wrong separator
            "2024-01-01",  # Wrong format
            "32/01/2024",  # Invalid day
            "01/13/2024",  # Invalid month
            "01/01/2024/extra",  # Extra parts
        ]

        for invalid_date in invalid_dates:
            with self.subTest(invalid_date=invalid_date):
                test_data = pd.DataFrame({"ΗμΈκδοσης": [invalid_date]})
                result = parse_dates(test_data)
                # Should handle gracefully and not raise exceptions
                self.assertIn("ΗμΈκδοσης", result.columns)


if __name__ == "__main__":
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestFilterEkatharistikosComprehensive
    )
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestFilterEkatharistikosPerformance)
    )
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(
            TestFilterEkatharistikosErrorHandling
        )
    )

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")

    print(f"\n{'='*60}")
