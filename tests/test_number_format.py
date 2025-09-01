import pandas as pd
import pytest

from dei_extractor.utils.number_format import _to_number_series, enforce_two_decimals


def test_greek_number_parsing():
    """Test parsing of Greek-style numbers with commas and dots."""
    # Test Greek format: 1.234,56 -> 1234.56
    s = pd.Series(["1.234,56", "2.500,00", "100,50", "1.000.000,99"])
    result = _to_number_series(s)
    expected = pd.Series([1234.56, 2500.0, 100.5, 1000000.99])
    pd.testing.assert_series_equal(result, expected, check_dtype=False)


def test_english_number_parsing():
    """Test parsing of English-style numbers."""
    s = pd.Series(["1234.56", "2500.00", "100.50", "1000000.99"])
    result = _to_number_series(s)
    expected = pd.Series([1234.56, 2500.0, 100.5, 1000000.99])
    pd.testing.assert_series_equal(result, expected, check_dtype=False)


def test_mixed_formats():
    """Test mixed Greek and English formats."""
    s = pd.Series(["1.234,56", "2500.00", "100,50", "1000000.99"])
    result = _to_number_series(s)
    # Greek format should be parsed, English format should be parsed
    expected = pd.Series([1234.56, 2500.0, 100.5, 1000000.99])
    pd.testing.assert_series_equal(
        result, expected, check_dtype=False, check_names=False
    )


def test_non_numeric_values():
    """Test that non-numeric values are preserved."""
    s = pd.Series(["1.234,56", "text", "100,50", "another text"])
    result = _to_number_series(s)
    # Only numeric values should be converted
    assert result.iloc[0] == 1234.56
    assert result.iloc[1] == "text"
    assert result.iloc[2] == 100.5
    assert result.iloc[3] == "another text"


def test_enforce_two_decimals_round():
    """Test rounding to 2 decimals only for values that originally had decimals."""
    df = pd.DataFrame(
        {
            "decimal_values": [123.456, 789.123, 100.999],
            "integer_values": [123, 789, 100],
            "mixed_values": [123.456, 789, 100.999],
            "text": ["hello", "world", "test"],
        }
    )
    result = enforce_two_decimals(df, mode="round")

    # Decimal values should be rounded to 2 decimals
    expected_decimal = pd.Series([123.46, 789.12, 101.0], name="decimal_values")
    pd.testing.assert_series_equal(
        result["decimal_values"], expected_decimal, check_dtype=False
    )

    # Integer values should remain as integers (no .00 added)
    expected_integer = pd.Series([123.0, 789.0, 100.0], name="integer_values")
    pd.testing.assert_series_equal(
        result["integer_values"], expected_integer, check_dtype=False
    )

    # Mixed values: only those with decimals should be formatted
    expected_mixed = pd.Series([123.46, 789.0, 101.0], name="mixed_values")
    pd.testing.assert_series_equal(
        result["mixed_values"], expected_mixed, check_dtype=False
    )

    assert result["text"].iloc[0] == "hello"  # Text should be preserved


def test_enforce_two_decimals_truncate():
    """Test truncating to 2 decimals only for values that originally had decimals."""
    df = pd.DataFrame(
        {
            "decimal_values": [123.456, 789.123, 100.999],
            "integer_values": [123, 789, 100],
            "text": ["hello", "world", "test"],
        }
    )
    result = enforce_two_decimals(df, mode="truncate")

    # Decimal values should be truncated to 2 decimals
    expected_decimal = pd.Series([123.45, 789.12, 100.99], name="decimal_values")
    pd.testing.assert_series_equal(
        result["decimal_values"], expected_decimal, check_dtype=False
    )

    # Integer values should remain as integers (no .00 added)
    expected_integer = pd.Series([123.0, 789.0, 100.0], name="integer_values")
    pd.testing.assert_series_equal(
        result["integer_values"], expected_integer, check_dtype=False
    )

    assert result["text"].iloc[0] == "hello"  # Text should be preserved


def test_already_numeric_columns():
    """Test that already numeric columns are handled correctly."""
    df = pd.DataFrame(
        {
            "float_col": [123.456, 789.123, 100.999],
            "int_col": [1, 2, 3],
            "text_col": ["a", "b", "c"],
        }
    )
    result = enforce_two_decimals(df, mode="round")
    expected_float = pd.Series([123.46, 789.12, 101.0], name="float_col")
    expected_int = pd.Series([1.0, 2.0, 3.0], name="int_col")
    pd.testing.assert_series_equal(
        result["float_col"], expected_float, check_dtype=False
    )
    pd.testing.assert_series_equal(result["int_col"], expected_int, check_dtype=False)
    assert result["text_col"].iloc[0] == "a"  # Text should be preserved


def test_greek_number_formatting():
    """Test that Greek number formats are handled correctly with decimal preservation."""
    df = pd.DataFrame(
        {
            "greek_decimals": ["1.234,56", "2.500,00", "100,50"],
            "greek_integers": ["1.234", "2.500", "100"],
            "mixed_greek": ["1.234,56", "2.500", "100,50"],
        }
    )
    result = enforce_two_decimals(df, mode="round")

    # Greek decimals should be converted and rounded to 2 decimals
    expected_decimals = pd.Series([1234.56, 2500.0, 100.5], name="greek_decimals")
    pd.testing.assert_series_equal(
        result["greek_decimals"], expected_decimals, check_dtype=False
    )

    # Greek integers should be converted but remain as integers (no .00)
    expected_integers = pd.Series([1234.0, 2500.0, 100.0], name="greek_integers")
    pd.testing.assert_series_equal(
        result["greek_integers"], expected_integers, check_dtype=False
    )

    # Mixed: only those with commas (decimals) should be formatted to 2 decimals
    expected_mixed = pd.Series([1234.56, 2500.0, 100.5], name="mixed_greek")
    pd.testing.assert_series_equal(
        result["mixed_greek"], expected_mixed, check_dtype=False
    )


def test_date_formatting():
    """Test that date columns are formatted to dd/mm/yyyy string format."""
    from dei_extractor.transform.final_2023 import format_dates

    df = pd.DataFrame(
        {
            "ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ": ["2023-01-01", "2023-06-15", "2023-12-31"],
            "ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ": ["2023-01-31", "2023-06-30", "2023-12-31"],
            "other_col": [1, 2, 3],
        }
    )

    result = format_dates(df)

    # Check that date columns are formatted as dd/mm/yyyy strings
    expected_start = pd.Series(
        ["01/01/2023", "15/06/2023", "31/12/2023"], name="ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ "
    )
    expected_end = pd.Series(
        ["31/01/2023", "30/06/2023", "31/12/2023"], name="ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ "
    )

    pd.testing.assert_series_equal(
        result["ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ "], expected_start, check_dtype=False
    )
    pd.testing.assert_series_equal(
        result["ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ "], expected_end, check_dtype=False
    )

    # Check that other columns are unchanged
    assert result["other_col"].iloc[0] == 1


def test_column_renaming():
    """Test that specific columns are renamed correctly."""
    from dei_extractor.transform.final_2023 import rename_columns

    df = pd.DataFrame(
        {
            "ΚΑΤΑΝΑΛΩΣΗ 1.1.2023.1": [100, 200, 300],
            "other_col": [1, 2, 3],
            "another_col": ["a", "b", "c"],
        }
    )

    result = rename_columns(df)

    # Check that the specific column was renamed
    assert "1.1.2023 Πραγματικό" in result.columns
    assert "ΚΑΤΑΝΑΛΩΣΗ 1.1.2023.1" not in result.columns

    # Check that the values are preserved
    assert result["1.1.2023 Πραγματικό"].iloc[0] == 100
    assert result["1.1.2023 Πραγματικό"].iloc[1] == 200
    assert result["1.1.2023 Πραγματικό"].iloc[2] == 300

    # Check that other columns are unchanged
    assert "other_col" in result.columns
    assert "another_col" in result.columns
    assert result["other_col"].iloc[0] == 1
    assert result["another_col"].iloc[0] == "a"
