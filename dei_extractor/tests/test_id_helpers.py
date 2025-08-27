#!/usr/bin/env python3
"""
Tests for ID helper functions.

This module tests the ID processing functionality added to the DEI Extractor.
"""

import unittest

import pandas as pd

from dei_extractor.utils.id_helpers import compute_arparchi_group_id


class TestIDHelpers(unittest.TestCase):
    """Test cases for ID helper functions."""

    def test_compute_arparchi_group_id_numeric(self):
        """Test compute_arparchi_group_id with numeric IDs."""
        # Test case 1: Same ID appears multiple times
        ids = pd.Series(["60016100101", "60016100101", "60016100201"])
        result = compute_arparchi_group_id(ids)
        expected = pd.Series([1, 1, 2])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_compute_arparchi_group_id_numeric_extended(self):
        """Test compute_arparchi_group_id with extended numeric IDs."""
        # Test case 2: Adding new ID
        ids = pd.Series(["60016100101", "60016100101", "60016100201", "60016100301"])
        result = compute_arparchi_group_id(ids)
        expected = pd.Series([1, 1, 2, 3])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_compute_arparchi_group_id_non_numeric(self):
        """Test compute_arparchi_group_id with non-numeric IDs."""
        # Test case 3: Non-numeric IDs with fallback to appearance order
        ids = pd.Series(["A1", "A1", "B2"])
        result = compute_arparchi_group_id(ids)
        expected = pd.Series([1, 1, 2])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_compute_arparchi_group_id_mixed(self):
        """Test compute_arparchi_group_id with mixed numeric and non-numeric IDs."""
        # Test case 4: Mixed IDs (numeric extraction behavior)
        # "60016100101" -> 60016100101, "A1" -> 1, "60016100201" -> 60016100201, "B2" -> 2
        ids = pd.Series(["60016100101", "A1", "60016100201", "B2"])
        result = compute_arparchi_group_id(ids)
        expected = pd.Series(
            [3, 1, 4, 2]
        )  # Based on numeric ranking: 1, 2, 60016100101, 60016100201
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_compute_arparchi_group_id_empty(self):
        """Test compute_arparchi_group_id with empty series."""
        ids = pd.Series([])
        result = compute_arparchi_group_id(ids)
        expected = pd.Series([])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_compute_arparchi_group_id_whitespace(self):
        """Test compute_arparchi_group_id with whitespace in IDs."""
        ids = pd.Series([" 60016100101 ", "60016100101", "  60016100201  "])
        result = compute_arparchi_group_id(ids)
        expected = pd.Series([1, 1, 2])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)

    def test_compute_arparchi_group_id_dense_ranking(self):
        """Test that dense ranking works correctly for numeric IDs."""
        # Test dense ranking: same values get same rank, next different value gets next rank
        ids = pd.Series(["100", "100", "200", "300", "200", "400"])
        result = compute_arparchi_group_id(ids)
        expected = pd.Series([1, 1, 2, 3, 2, 4])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
