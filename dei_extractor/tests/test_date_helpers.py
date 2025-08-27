#!/usr/bin/env python3
"""
Tests for date parsing helper functions.

This module tests the new date parsing functionality added to the DEI Extractor.
"""

import unittest
from datetime import date

from dei_extractor.utils.validators import parse_ddmmyyyy, split_period


class TestDateHelpers(unittest.TestCase):
    """Test cases for date parsing helper functions."""

    def test_split_period_valid(self):
        """Test split_period with valid period string."""
        period = "25.02.2021-30.08.2022"
        start, end = split_period(period)

        self.assertEqual(start, "25.02.2021")
        self.assertEqual(end, "30.08.2022")

    def test_split_period_invalid_format(self):
        """Test split_period with invalid format."""
        invalid_periods = [
            "25.02.2021",  # No dash
            "25-02-2021-30-08-2022",  # Wrong separator
            "25.02.21-30.08.22",  # Wrong year format
            "",  # Empty string
            None,  # None value
        ]

        for period in invalid_periods:
            start, end = split_period(period)
            self.assertIsNone(start)
            self.assertIsNone(end)

    def test_split_period_whitespace(self):
        """Test split_period with whitespace."""
        period = "  25.02.2021-30.08.2022  "
        start, end = split_period(period)

        self.assertEqual(start, "25.02.2021")
        self.assertEqual(end, "30.08.2022")

    def test_parse_ddmmyyyy_valid(self):
        """Test parse_ddmmyyyy with valid date string."""
        date_str = "25.02.2021"
        result = parse_ddmmyyyy(date_str)

        self.assertIsInstance(result, date)
        self.assertEqual(result.year, 2021)
        self.assertEqual(result.month, 2)
        self.assertEqual(result.day, 25)

    def test_parse_ddmmyyyy_invalid(self):
        """Test parse_ddmmyyyy with invalid date string."""
        invalid_dates = [
            "25.13.2021",  # Invalid month
            "32.02.2021",  # Invalid day
            "25.02.21",  # Wrong year format
            "25-02-2021",  # Wrong separator
            "",  # Empty string
            None,  # None value
        ]

        for date_str in invalid_dates:
            result = parse_ddmmyyyy(date_str)
            self.assertIsNone(result)

    def test_parse_ddmmyyyy_edge_cases(self):
        """Test parse_ddmmyyyy with edge cases."""
        # Leap year
        leap_date = parse_ddmmyyyy("29.02.2020")
        self.assertIsInstance(leap_date, date)
        self.assertEqual(leap_date.day, 29)

        # Non-leap year February 29
        non_leap_date = parse_ddmmyyyy("29.02.2021")
        self.assertIsNone(non_leap_date)


if __name__ == "__main__":
    unittest.main()
