#!/usr/bin/env python3
"""
Minimal tests for XLSX exporter.

This module contains lightweight tests for the XLSX exporter functionality.
"""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ..exporters.xlsx_exporter import COLUMNS, row_from_payload, to_xlsx


class TestXlsxExporterMin(unittest.TestCase):
    """Minimal tests for XLSX exporter."""

    def test_columns_definition(self):
        """Test that COLUMNS is defined correctly."""
        expected_columns = [
            "ΑρΠαροχής",
            "ΑρΠαρχ_Ομάδα",
            "ΑρΛογαριασμού",
            "ΗμΈκδοσης",
            "ΠερίοδοςΚατανάλωσης",
            "Ονοματεπώνυμο_Διεύθυνση",
            "Πόλη",
            "Τελευταία",
            "Προηγούμενη",
            "ΣΩΧΒ",
            "ΣυνΩΧΒ",
            "ΚατηγορίαΤιμολογίου",
            "Υποκατηγορία",
            "Εκαθαριστικός",
            "source_file",
            "ΠερίοδοςΚατανάλωσης_Αρχική",
            "ΠερίοδοςΚατανάλωσης_Τελική",
            "raw_code",
            "raw_label",
        ]

        self.assertEqual(
            COLUMNS, expected_columns, "COLUMNS should match expected definition"
        )
        self.assertEqual(len(COLUMNS), 19, "Should have exactly 19 columns")

    def test_row_from_payload(self):
        """Test row_from_payload function with sample data."""
        # Sample payload
        payload = {
            "format": "format_3",
            "supply_number": {"pretty": "123 4567890-12", "normalized": "123456789012"},
            "account_number": "987654321",
            "issue_date": "2018-06-15",
            "period_from": "2018-05-01",
            "period_to": "2018-05-31",
            "recipient_name": "JOHN DOE",
            "recipient_address_line1": "123 MAIN STREET",
            "recipient_postcode_city": "12345 ATHENS",
            "city": "ATHENS",
            "reading_last": 1000,
            "reading_prev": 950,
            "kwh_night": 50.5,
            "kwh_total": 100.0,
            "tariff_category": "ΦΟΠ",
            "tariff_subcategory": "Standard",
            "is_clearing": True,
        }

        source_file = "test_file.pdf"
        row = row_from_payload(payload, source_file)

        # Check that row has all required columns
        for column in COLUMNS:
            self.assertIn(column, row, f"Column {column} should be present in row")

        # Check specific mappings
        self.assertEqual(row["ΑρΠαροχής"], "123456789012")
        self.assertEqual(row["ΑρΠαρχ_Ομάδα"], "123")  # First digit block
        self.assertEqual(row["ΑρΛογαριασμού"], "987654321")
        self.assertEqual(row["ΗμΈκδοσης"], "2018-06-15")
        self.assertEqual(row["ΠερίοδοςΚατανάλωσης"], "2018-05-01-2018-05-31")
        self.assertEqual(row["Ονοματεπώνυμο_Διεύθυνση"], "JOHN DOE, 123 MAIN STREET")
        self.assertEqual(row["Πόλη"], "ATHENS")
        self.assertEqual(row["Τελευταία"], 1000)
        self.assertEqual(row["Προηγούμενη"], 950)
        self.assertEqual(row["ΣΩΧΒ"], 50.5)
        self.assertEqual(row["ΣυνΩΧΒ"], 100.0)
        self.assertEqual(row["ΚατηγορίαΤιμολογίου"], "ΦΟΠ")
        self.assertEqual(row["Υποκατηγορία"], "Standard")
        self.assertEqual(row["Εκαθαριστικός"], "ΝΑΙ")
        self.assertEqual(row["source_file"], "test_file.pdf")
        self.assertEqual(row["ΠερίοδοςΚατανάλωσης_Αρχική"], "2018-05-01")
        self.assertEqual(row["ΠερίοδοςΚατανάλωσης_Τελική"], "2018-05-31")
        self.assertEqual(row["raw_code"], "987654321")
        self.assertEqual(row["raw_label"], "format_3")

    def test_row_from_payload_minimal(self):
        """Test row_from_payload with minimal data."""
        # Minimal payload
        payload = {
            "format": "format_3",
            "supply_number": {"normalized": "123456789012"},
            "is_clearing": False,
        }

        source_file = "minimal_test.pdf"
        row = row_from_payload(payload, source_file)

        # Check that all columns are present (even if None/empty)
        for column in COLUMNS:
            self.assertIn(column, row, f"Column {column} should be present in row")

        # Check specific values
        self.assertEqual(row["ΑρΠαροχής"], "123456789012")
        self.assertEqual(row["Εκαθαριστικός"], "ΟΧΙ")
        self.assertEqual(row["source_file"], "minimal_test.pdf")
        self.assertEqual(row["raw_label"], "format_3")

    def test_to_xlsx(self):
        """Test to_xlsx function creates valid XLSX file."""
        # Sample payloads
        payloads = [
            {
                "format": "format_3",
                "supply_number": {"normalized": "123456789012"},
                "account_number": "987654321",
                "issue_date": "2018-06-15",
                "period_from": "2018-05-01",
                "period_to": "2018-05-31",
                "recipient_name": "JOHN DOE",
                "recipient_address_line1": "123 MAIN STREET",
                "recipient_postcode_city": "12345 ATHENS",
                "city": "ATHENS",
                "reading_last": 1000,
                "reading_prev": 950,
                "kwh_night": 50.5,
                "kwh_total": 100.0,
                "tariff_category": "ΦΟΠ",
                "tariff_subcategory": "Standard",
                "is_clearing": True,
            }
        ]

        source_files = ["test_file.pdf"]

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Test XLSX creation
            result_path = to_xlsx(payloads, source_files, tmp_path)
            self.assertEqual(result_path, tmp_path)

            # Verify file exists
            self.assertTrue(Path(tmp_path).exists(), "XLSX file should be created")

            # Read back and verify structure
            df = pd.read_excel(tmp_path)

            # Check columns match exactly
            self.assertEqual(
                list(df.columns),
                COLUMNS,
                "XLSX columns should match COLUMNS definition",
            )

            # Check we have one row
            self.assertEqual(len(df), 1, "Should have one row of data")

            # Check some key values
            self.assertEqual(df.iloc[0]["ΑρΠαροχής"], "123456789012")
            self.assertEqual(df.iloc[0]["Εκαθαριστικός"], "ΝΑΙ")
            self.assertEqual(df.iloc[0]["source_file"], "test_file.pdf")

        finally:
            # Clean up
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    def test_to_xlsx_empty_data(self):
        """Test to_xlsx with empty data."""
        payloads = []
        source_files = []

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            result_path = to_xlsx(payloads, source_files, tmp_path)
            self.assertEqual(result_path, tmp_path)

            # Verify file exists
            self.assertTrue(
                Path(tmp_path).exists(),
                "XLSX file should be created even with empty data",
            )

            # Read back and verify structure
            df = pd.read_excel(tmp_path)

            # Check columns match exactly
            self.assertEqual(
                list(df.columns),
                COLUMNS,
                "XLSX columns should match COLUMNS definition",
            )

            # Check we have no rows
            self.assertEqual(len(df), 0, "Should have no rows of data")

        finally:
            # Clean up
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    def test_to_xlsx_mismatched_lengths(self):
        """Test to_xlsx with mismatched payload and source file lengths."""
        payloads = [{"format": "format_3"}]
        source_files = ["file1.pdf", "file2.pdf"]  # Different length

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            with self.assertRaises(ValueError):
                to_xlsx(payloads, source_files, tmp_path)
        finally:
            # Clean up
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()


if __name__ == "__main__":
    unittest.main()
