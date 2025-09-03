"""
Test suite for final_2023 transformation module.
"""

import os

# Add project root to path
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from dei_extractor.transform.final_2023 import (
    _calculate_sum_consumption,
    _classify_infrastructure,
    _clean_site_name,
    _convert_numeric_columns,
    _find_consumption_window,
    _parse_consumption_periods,
    compute_final,
    load_phase1,
    write_final,
)


@pytest.fixture
def sample_phase1_data():
    """Create sample Phase-1 data for testing."""
    return pd.DataFrame(
        {
            "ΑρΠαροχής": ["60016100101", "60016100101", "60016100201", "60016100201"],
            "ΑρΛογαριασμού": ["ACC001", "ACC001", "ACC002", "ACC002"],
            "ΠερίοδοςΚατανάλωσης": [
                "25.02.2021-30.08.2022",
                "31.08.2022-21.02.2023",
                "22.02.2023-27.08.2023",
                "28.08.2023-21.02.2024",
            ],
            "Τελευταία": [23344, 24446, 25618, 26133],
            "Προηγούμενη": [19849, 23344, 24446, 25618],
            "ΣυνΩΧΒ": [3495, 1102, 1172, 515],
            "ΣΩΧΒ": [1, 1, 1, 1],
            "Ονοματεπώνυμο_Διεύθυνση": [
                "ΚΟΙΝΟΤΗΣ ΒΟΥΛ/ΝΗΣ",
                "ΚΟΙΝΟΤΗΣ ΒΟΥΛ/ΝΗΣ",
                "ΚΟΙΝΟΤΗΣ ΒΟΥΛΙΑΓΜΕΝΗ",
                "ΚΟΙΝΟΤΗΣ ΒΟΥΛΙΑΓΜΕΝΗ",
            ],
            "ΚατηγορίαΤιμολογίου": ["ΦΟΠ", "ΦΟΠ", "ΦΟΠ", "ΦΟΠ"],
            "Υποκατηγορία": ["ΔΗΜΟΣΙΑ", "ΔΗΜΟΣΙΑ", "ΔΗΜΟΣΙΑ", "ΔΗΜΟΣΙΑ"],
            "Εκαθαριστικός": [True, True, True, True],
        }
    )


@pytest.fixture
def sample_phase1_file(sample_phase1_data):
    """Create a temporary Phase-1 Excel file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        with pd.ExcelWriter(tmp.name, engine="openpyxl") as writer:
            sample_phase1_data.to_excel(writer, sheet_name="Sheet1", index=False)
        yield tmp.name
    os.unlink(tmp.name)


def test_parse_consumption_periods():
    """Test consumption period parsing."""
    df = pd.DataFrame(
        {
            "ΠερίοδοςΚατανάλωσης": [
                "25.02.2021-30.08.2022",
                "31.08.2022-21.02.2023",
                "invalid-period",
                None,
            ]
        }
    )

    result = _parse_consumption_periods(df)

    # Check that valid periods were parsed
    assert len(result) == 2  # Invalid and None should be filtered out
    assert result["start_date"].iloc[0] == pd.Timestamp("2021-02-25")
    assert result["end_date"].iloc[0] == pd.Timestamp("2022-08-30")
    assert result["period_days"].iloc[0] == 551
    assert result["start_date"].iloc[1] == pd.Timestamp("2022-08-31")
    assert result["end_date"].iloc[1] == pd.Timestamp("2023-02-21")


def test_convert_numeric_columns():
    """Test numeric column conversion."""
    df = pd.DataFrame(
        {
            "Τελευταία": ["23344", "24446", "invalid"],
            "Προηγούμενη": ["19849", "23344", "24446"],
            "ΣυνΩΧΒ": ["3495", "1102", "1172"],
            "ΑρΠαροχής": ["60016100101", "60016100201", "60016100301"],
            "ΑρΛογαριασμού": ["ACC001", "ACC002", "ACC003"],
        }
    )

    result = _convert_numeric_columns(df)

    # Check numeric conversions (should be float64 to handle NaN)
    assert result["Τελευταία"].dtype == "float64"
    assert result["Προηγούμενη"].dtype == "float64"
    assert result["ΣυνΩΧΒ"].dtype == "float64"

    # Check string conversions
    assert result["ΑρΠαροχής"].dtype == "object"
    assert result["ΑρΛογαριασμού"].dtype == "object"


def test_find_consumption_window():
    """Test consumption window finding logic."""
    df = pd.DataFrame(
        {
            "start_date": [
                pd.Timestamp("2022-02-25"),
                pd.Timestamp("2022-08-31"),
                pd.Timestamp("2023-02-22"),
                pd.Timestamp("2023-08-28"),
            ],
            "end_date": [
                pd.Timestamp("2022-08-30"),
                pd.Timestamp("2023-02-21"),
                pd.Timestamp("2023-08-27"),
                pd.Timestamp("2024-02-21"),
            ],
            "Προηγούμενη": [19849, 23344, 24446, 25618],
            "Τελευταία": [23344, 24446, 25618, 26133],
        }
    )

    window_start, window_end, initial_reading, final_reading = _find_consumption_window(
        df, 2023
    )

    # Should find the period containing 2023-01-01 and 2023-12-31
    assert window_start == pd.Timestamp("2022-08-31")
    assert window_end == pd.Timestamp("2024-02-21")
    assert initial_reading == 23344
    assert final_reading == 26133


def test_calculate_sum_consumption():
    """Test sum consumption calculation."""
    df = pd.DataFrame(
        {
            "start_date": [
                pd.Timestamp("2023-01-01"),
                pd.Timestamp("2023-06-01"),
                pd.Timestamp("2023-12-01"),
            ],
            "end_date": [
                pd.Timestamp("2023-05-31"),
                pd.Timestamp("2023-11-30"),
                pd.Timestamp("2023-12-31"),
            ],
            "ΣυνΩΧΒ": [1000, 1500, 500],
        }
    )

    window_start = pd.Timestamp("2023-01-01")
    window_end = pd.Timestamp("2023-12-31")

    total = _calculate_sum_consumption(df, window_start, window_end)
    assert total == 3000


def test_clean_site_name():
    """Test site name cleaning."""
    assert _clean_site_name("ΚΟΙΝΟΤΗΣ ΒΟΥΛ/ΝΗΣ") == "ΚΟΙΝΟΤΗΣ ΒΟΥΛ/ΝΗΣ"
    assert _clean_site_name("  ΔΗΜΟΣ  ΔΗΜΟΣ  ") == "ΔΗΜΟΣ"
    assert (
        _clean_site_name("ΚΟΙΝΟΤΗΤΑ ΚΟΙΝΟΤΗΤΑ ΒΟΥΛΙΑΓΜΕΝΗ") == "ΚΟΙΝΟΤΗΤΑ ΒΟΥΛΙΑΓΜΕΝΗ"
    )
    assert _clean_site_name(None) == ""


def test_classify_infrastructure():
    """Test infrastructure classification."""
    name = "ΚΟΙΝΟΤΗΣ ΒΟΥΛ/ΝΗΣ"
    group = pd.DataFrame({"ΚατηγορίαΤιμολογίου": ["ΦΟΠ"]})

    infra_flag, facility_type, subtype, sector = _classify_infrastructure(
        name, group, {}
    )

    # ΦΟΠ should NEVER be classified as infrastructure
    assert infra_flag == "ΟΧΙ"  # ΦΟΠ overrides keyword matching
    assert facility_type == "ΦΟΠ"
    assert subtype == "ΟΧΙ"
    assert sector == "ΛΟΙΠΕΣ ΥΠΟΔΟΜΕΣ"


def test_classify_infrastructure_fop_override():
    """Test that ΦΟΠ always overrides infrastructure classification."""
    # Test with infrastructure keywords but ΦΟΠ category
    name = "ΣΧΟΛΕΙΟ ΚΑΙ ΚΑΠΗ"  # Contains infrastructure keywords
    group = pd.DataFrame({"ΚατηγορίαΤιμολογίου": ["ΦΟΠ"]})

    infra_flag, facility_type, subtype, sector = _classify_infrastructure(
        name, group, {}
    )

    # Even with infrastructure keywords, ΦΟΠ should be "ΟΧΙ"
    assert infra_flag == "ΟΧΙ"
    assert facility_type == "ΦΟΠ"
    assert subtype == "ΟΧΙ"
    assert sector == "ΛΟΙΠΕΣ ΥΠΟΔΟΜΕΣ"


def test_classify_infrastructure_non_fop():
    """Test infrastructure classification for non-ΦΟΠ cases."""
    name = "ΣΧΟΛΕΙΟ ΚΑΙ ΚΑΠΗ"
    group = pd.DataFrame({"ΚατηγορίαΤιμολογίου": ["ΔΗΜΟΣΙΑ"]})

    infra_flag, facility_type, subtype, sector = _classify_infrastructure(
        name, group, {}
    )

    # Should be classified as infrastructure due to keywords
    assert infra_flag == "ΝΑΙ"
    assert facility_type == "ΔΗΜΟΣΙΑ"
    assert subtype == "ΝΑΙ"
    assert sector == "ΣΧΟΛΕΙΟ"  # ΣΧΟΛΕΙΟ keyword matches


def test_load_phase1(sample_phase1_file):
    """Test Phase-1 data loading."""
    df = load_phase1(sample_phase1_file)

    assert len(df) == 4
    assert "start_date" in df.columns
    assert "end_date" in df.columns
    assert "period_days" in df.columns
    assert df["ΑρΠαροχής"].dtype == "object"
    assert df["Τελευταία"].dtype == "float64"  # Should be float64 to handle NaN


def test_compute_final(sample_phase1_data):
    """Test final dataset computation."""
    final_df = compute_final(sample_phase1_data, year=2023)

    assert len(final_df) == 2  # Two unique services
    assert "Α/Α" in final_df.columns
    assert "ΠΑΡΟΧΗ" in final_df.columns
    assert final_df["Α/Α"].iloc[0] == 1
    assert final_df["Α/Α"].iloc[1] == 2


def test_compute_final_with_meter_reset():
    """Test computation with meter reset scenario."""
    # Create data with meter reset (final < initial)
    df = pd.DataFrame(
        {
            "ΑρΠαροχής": ["60016100101", "60016100101"],
            "ΑρΛογαριασμού": ["ACC001", "ACC001"],
            "ΠερίοδοςΚατανάλωσης": ["01.01.2023-30.06.2023", "01.07.2023-31.12.2023"],
            "Τελευταία": [9999, 1000],  # Meter reset
            "Προηγούμενη": [9000, 9999],
            "ΣυνΩΧΒ": [999, 1],  # Sum should be 1000
            "Ονοματεπώνυμο_Διεύθυνση": ["TEST SITE", "TEST SITE"],
            "ΚατηγορίαΤιμολογίου": ["TEST", "TEST"],
        }
    )

    # Parse periods
    df = _parse_consumption_periods(df)
    df = _convert_numeric_columns(df)

    final_df = compute_final(df, year=2023)

    # Should handle meter reset by using sum method
    assert len(final_df) == 1
    assert final_df["ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH"].iloc[0] == 1000


def test_compute_final_edge_cases():
    """Test edge cases in final computation."""
    # Test with missing 2023 overlap
    df = pd.DataFrame(
        {
            "ΑρΠαροχής": ["60016100101"],
            "ΑρΛογαριασμού": ["ACC001"],
            "ΠερίοδοςΚατανάλωσης": ["01.01.2021-31.12.2021"],  # No 2023 overlap
            "Τελευταία": [1000],
            "Προηγούμενη": [500],
            "ΣυνΩΧΒ": [500],
            "Ονοματεπώνυμο_Διεύθυνση": ["TEST SITE"],
            "ΚατηγορίαΤιμολογίου": ["TEST"],
        }
    )

    df = _parse_consumption_periods(df)
    df = _convert_numeric_columns(df)

    final_df = compute_final(df, year=2023)

    # Should still create a row but the system will extrapolate to 2023
    assert len(final_df) == 1
    # The system will use the available data to extrapolate, so it won't be NaN
    assert not pd.isna(final_df["ΚΑΤΑΝΑΛΩΣΗ 2023 KWH"].iloc[0])


def test_write_final(sample_phase1_data):
    """Test final dataset writing."""
    final_df = compute_final(sample_phase1_data, year=2023)

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        write_final(final_df, tmp.name)

        # Verify file was created and contains expected sheets
        assert Path(tmp.name).exists()

        # Read back and verify
        xls = pd.ExcelFile(tmp.name)
        assert "Sheet1" in xls.sheet_names
        assert "_meta" in xls.sheet_names

        # Check main data
        df_read = pd.read_excel(tmp.name, "Sheet1")
        assert len(df_read) == len(final_df)

        # Check that the expected columns are present (after renaming)
        expected_columns = [
            "Α/Α",
            "ΠΑΡΟΧΗ",
            "ΑΡΙΘΜΟΣ ΣΥΜΒΟΛΑΙΟΥ ",
            "ΟΝΟΜΑ ",
            "ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)",
            "ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ",
            "ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
            "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ",
            "ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
            "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
            "ΣΧΟΛΙΟ",
            "ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/23",
            "ΑΡ. ΗΜΕΡΩΝ ΜΕΤΑ ΤΙΣ 31/12/2023",
            "ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ",
            "ΑΡ. ΗΜΕΡΩΝ 2019",
            "ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH",
            "ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ.",
            "ΚΑΤΑΝΑΛΩΣΗ 2023 KWH",
            "ΚΑΤΑΝΑΛΩΣΗ ΗΜΕΡΩΝ ΠΡΙΝ ΤΗΣ 1.1.2023",
            "ΚΑΤΑΝΑΛΩΣΗ 1.1.2023",
            "ΚΑΤΑΝΑΛΩΣΗ 1.1.2023 Πραγματικό",
            "ΚΑΤΑΝΑΛΩΣΗ 31.12.2023",
            "ΔΙΑΦΟΡΑ ΚΑΤΑΝΑΛΩΣΗΣ KWH",
            "Unnamed: 25",
        ]
        assert list(df_read.columns) == expected_columns

        os.unlink(tmp.name)


def test_integration_end_to_end(sample_phase1_file):
    """Test complete end-to-end integration."""
    # Load data
    df = load_phase1(sample_phase1_file)

    # Compute final
    final_df = compute_final(df, year=2023)

    # Write to file
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        write_final(final_df, tmp.name)

        # Verify output
        assert Path(tmp.name).exists()

        # Read back and verify structure
        with pd.ExcelFile(tmp.name) as xls:
            df_read = pd.read_excel(xls, "Sheet1")

            # Check column structure
            expected_columns = [
                "Α/Α",
                "ΠΑΡΟΧΗ",
                "ΑΡΙΘΜΟΣ ΣΥΜΒΟΛΑΙΟΥ ",
                "ΟΝΟΜΑ ",
                "ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)",
                "ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ",
                "ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
                "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ",
                "ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
                "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
                "ΣΧΟΛΙΟ",
                "ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/23",
                "ΑΡ. ΗΜΕΡΩΝ ΜΕΤΑ ΤΙΣ 31/12/2023",
                "ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ",
                "ΑΡ. ΗΜΕΡΩΝ 2019",
                "ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH",
                "ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ.",
                "ΚΑΤΑΝΑΛΩΣΗ 2023 KWH",
                "ΚΑΤΑΝΑΛΩΣΗ ΗΜΕΡΩΝ ΠΡΙΝ ΤΗΣ 1.1.2023",
                "ΚΑΤΑΝΑΛΩΣΗ 1.1.2023",
                "ΚΑΤΑΝΑΛΩΣΗ 1.1.2023 Πραγματικό",
                "ΚΑΤΑΝΑΛΩΣΗ 31.12.2023",
                "ΔΙΑΦΟΡΑ ΚΑΤΑΝΑΛΩΣΗΣ KWH",
                "Unnamed: 25",
            ]

            assert list(df_read.columns) == expected_columns
            assert len(df_read) == 2  # Two services

            # Check that Α/Α is sequential
            assert df_read["Α/Α"].iloc[0] == 1
            assert df_read["Α/Α"].iloc[1] == 2

            # Check that ΠΑΡΟΧΗ contains the service IDs (convert to string for comparison)
            service_ids = df_read["ΠΑΡΟΧΗ"].astype(str).values
            assert "60016100101" in service_ids
            assert "60016100201" in service_ids

        os.unlink(tmp.name)


def test_formula_verification(sample_phase1_data):
    """Test that computed formulas are correct."""
    final_df = compute_final(sample_phase1_data, year=2023)

    # Test a few key formulas
    for idx, row in final_df.iterrows():
        # Test that captured days is positive
        assert row["ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ"] > 0

        # Test that mean consumption is calculated correctly
        if not pd.isna(row["ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ."]):
            expected_mean = (
                row["ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH"]
                / row["ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ"]
            )
            assert abs(row["ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ."] - expected_mean) < 1e-6

        # Test that 2023 consumption is prorated correctly
        if not pd.isna(row["ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ."]):
            expected_2023 = row["ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ."] * 365
            assert abs(row["ΚΑΤΑΝΑΛΩΣΗ 2023 KWH"] - expected_2023) < 1e-6

        # Test that days 2019 is always 365
        assert row["ΑΡ. ΗΜΕΡΩΝ 2019"] == 365


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
