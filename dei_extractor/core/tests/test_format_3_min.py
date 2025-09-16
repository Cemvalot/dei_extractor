#!/usr/bin/env python3
"""
Minimal tests for format_3 parser.

This module contains lightweight tests for the format_3 parser functionality.
"""

import os
import unittest
from pathlib import Path

from ..parsers.format_3 import detect, parse


class TestFormat3Min(unittest.TestCase):
    """Minimal tests for format_3 parser."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample PDF path - skip test if not present
        self.sample_pdf_path = "/mnt/data/686452861017_2018-06-05.pdf"
        self.sample_pdf_available = os.path.exists(self.sample_pdf_path)

    def test_detect_format_3(self):
        """Test format_3 detection with sample text."""
        # Sample text that should match format_3
        sample_text = """
        ΑΡΙΘΜΟΣ ΠΑΡΟΧΗΣ 1234567890
        ΗΜΕΡΟΜΗΝΙΑ ΕΚΔΟΣΗΣ 15/06/2018
        ΠΕΡΙΟΔΟΣ ΚΑΤΑΝΑΛΩΣΗΣ 01/05/2018 - 31/05/2018
        A/A ΛΟΓΑΡΙΑΣΜΟΥ 987654321
        """

        self.assertTrue(detect(sample_text), "Should detect format_3 with sample text")

    def test_detect_format_3_insufficient_patterns(self):
        """Test format_3 detection with insufficient patterns."""
        # Text with only one matching pattern
        sample_text = """
        ΑΡΙΘΜΟΣ ΠΑΡΟΧΗΣ 1234567890
        Some other text without matching patterns
        """

        self.assertFalse(
            detect(sample_text), "Should not detect format_3 with insufficient patterns"
        )

    def test_parse_format_3_structure(self):
        """Test format_3 parsing returns correct structure."""
        # Create a minimal PDF-like text for testing
        sample_text = """
        ΑΡΙΘΜΟΣ ΠΑΡΟΧΗΣ 1234567890
        ΗΜΕΡΟΜΗΝΙΑ ΕΚΔΟΣΗΣ 15/06/2018
        ΠΕΡΙΟΔΟΣ ΚΑΤΑΝΑΛΩΣΗΣ 01/05/2018 - 31/05/2018
        A/A ΛΟΓΑΡΙΑΣΜΟΥ 987654321
        ΟΝΟΜ/ΜΟ - Δ/ΝΣΗ ΕΠΙΔΟΣΗΣ
        JOHN DOE
        123 MAIN STREET
        12345 ATHENS
        Τελευταία: 1000
        Προηγούμενη: 950
        ΣΩΧΒ: 50,5
        ΣυνΩΧΒ: 100,0
        Κατηγορία Τιμολογίου: ΦΟΠ
        Υποκατηγορία: Standard
        ΕΚΚΑΘΑΡΙΣΤΙΚΟΣ
        """

        # Convert text to bytes (simulating PDF bytes)
        pdf_bytes = sample_text.encode("utf-8")

        result = parse(pdf_bytes, "test_file.pdf")

        # Check that result has the expected structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("format"), "format_3")

        # Check required fields exist
        required_fields = [
            "supply_number",
            "account_number",
            "issue_date",
            "period_from",
            "period_to",
            "recipient_name",
            "recipient_address_line1",
            "recipient_postcode_city",
            "city",
            "reading_last",
            "reading_prev",
            "kwh_night",
            "kwh_total",
            "tariff_category",
            "tariff_subcategory",
            "is_clearing",
        ]

        for field in required_fields:
            self.assertIn(field, result, f"Field {field} should be present in result")

        # Check supply_number structure
        supply_number = result.get("supply_number", {})
        self.assertIsInstance(supply_number, dict)
        self.assertIn("pretty", supply_number)
        self.assertIn("normalized", supply_number)

        # Check normalized supply number is digits-only
        normalized = supply_number.get("normalized", "")
        self.assertTrue(
            normalized.isdigit(), "Normalized supply number should be digits-only"
        )
        self.assertGreaterEqual(
            len(normalized), 10, "Normalized supply number should be at least 10 digits"
        )

        # Check date format is ISO
        issue_date = result.get("issue_date")
        if issue_date:
            self.assertRegex(
                issue_date, r"^\d{4}-\d{2}-\d{2}$", "Issue date should be in ISO format"
            )

        # Check clearing flag mapping
        is_clearing = result.get("is_clearing")
        self.assertIsInstance(is_clearing, bool)

    @unittest.skipUnless(
        os.path.exists("/mnt/data/686452861017_2018-06-05.pdf"),
        "Sample PDF not available",
    )
    def test_parse_sample_pdf(self):
        """Test parsing with actual sample PDF file."""
        if not self.sample_pdf_available:
            self.skipTest("Sample PDF not available")

        # Read the sample PDF
        with open(self.sample_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # Test detection
        from ..utils.text import extract_text, normalize_text

        text = extract_text(pdf_bytes)
        normalized_text = normalize_text(text)

        self.assertTrue(detect(normalized_text), "Should detect format_3 in sample PDF")

        # Test parsing
        result = parse(pdf_bytes, self.sample_pdf_path)

        # Basic structure checks
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("format"), "format_3")

        # Check that we extracted some meaningful data
        supply_number = result.get("supply_number", {})
        self.assertTrue(
            supply_number.get("normalized"),
            "Should extract supply number from sample PDF",
        )


if __name__ == "__main__":
    unittest.main()
