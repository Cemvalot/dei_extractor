"""
Unit tests for transform_consumptions function.

Tests the field selection logic based on date differences for DEI invoice data.
"""

from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the function to test
from dei_extractor.transform.final_2023 import (
    save_transform_consumptions,
    transform_consumptions,
)


class TestTransformConsumptions:
    """Test cases for transform_consumptions function."""

    def test_case_a_high_difference_initial_previous_values(self):
        """Test Case A: days_diff=97 (>60) → use initial/previous values."""

        # Create test data
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["10/06/2025"],
            "ΠερίοδοςΚατανάλωσης_Τέλος": ["10/07/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "Κατανάλωση_Αρχική": [100.5],
            "Κατανάλωση_Προηγούμενη": [200.3],
            "Λογαριασμός_Αρχική": [300.7],
            "Λογαριασμός_Αρχική_Προηγούμενη": [400.1],
            "Κατανάλωση_Τελευταία": [500.9],
            "Κατανάλωση_Σύνολο": [600.2],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check days_diff calculation
        assert result["days_diff"].iloc[0] == 97

        # Check that initial/previous values are populated
        assert result["ΑρχικήΚατανάλωση"].iloc[0] == 100.5
        assert result["ΠροηγούμενηΚατανάλωση"].iloc[0] == 200.3
        assert result["ΑρχικήΛογαριασμού"].iloc[0] == 300.7
        assert result["ΑρχικήΠροηγούμενηΛογαριασμού"].iloc[0] == 400.1

        # Check that latest/total values are NaN
        assert pd.isna(result["ΤελευταίαΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΣυνολικήΚατανάλωση"].iloc[0])

        # Check metadata fields
        assert result["ΑρΠαροχής"].iloc[0] == "12345"
        assert result["ΑρΛογαριασμού"].iloc[0] == "67890"
        assert result["ΗμΈκδοσης"].iloc[0] == "15/09/2025"
        assert result["ΠερίοδοςΚατανάλωσης_Αρχή"].iloc[0] == "10/06/2025"
        assert result["ΠερίοδοςΚατανάλωσης_Τέλος"].iloc[0] == "10/07/2025"
        assert result["Ονοματεπώνυμο_Διεύθυνση"].iloc[0] == "Test Address"
        assert result["Πόλη"].iloc[0] == "Athens"

    def test_case_b_low_difference_latest_total_values(self):
        """Test Case B: days_diff=60 (≤60) → use latest/total values."""

        # Create test data
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["17/07/2025"],
            "ΠερίοδοςΚατανάλωσης_Τέλος": ["17/08/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "Κατανάλωση_Αρχική": [100.5],
            "Κατανάλωση_Προηγούμενη": [200.3],
            "Λογαριασμός_Αρχική": [300.7],
            "Λογαριασμός_Αρχική_Προηγούμενη": [400.1],
            "Κατανάλωση_Τελευταία": [500.9],
            "Κατανάλωση_Σύνολο": [600.2],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check days_diff calculation
        assert result["days_diff"].iloc[0] == 60

        # Check that latest/total values are populated
        assert result["ΤελευταίαΚατανάλωση"].iloc[0] == 500.9
        assert result["ΣυνολικήΚατανάλωση"].iloc[0] == 600.2

        # Check that initial/previous values are NaN
        assert pd.isna(result["ΑρχικήΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΠροηγούμενηΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΑρχικήΛογαριασμού"].iloc[0])
        assert pd.isna(result["ΑρχικήΠροηγούμενηΛογαριασμού"].iloc[0])

    def test_case_c_fallback_mapping(self):
        """Test Case C: Fallback mapping for alternative column names."""

        # Create test data with alternative column names
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["17/07/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "Τελευταία": [500.9],  # Alternative name
            "Προηγούμενη": [200.3],  # Alternative name
            "ΣυνΩΧΒ": [600.2],  # Alternative name
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check that fallback mapping worked
        assert result["ΤελευταίαΚατανάλωση"].iloc[0] == 500.9
        # Note: ΠροηγούμενηΚατανάλωση should be NaN because days_diff=60 (≤60) uses latest/total values
        assert pd.isna(result["ΠροηγούμενηΚατανάλωση"].iloc[0])
        assert result["ΣυνολικήΚατανάλωση"].iloc[0] == 600.2

    def test_fallback_mapping_high_difference(self):
        """Test fallback mapping with high difference (>60) to test Προηγούμενη mapping."""

        # Create test data with alternative column names and high difference
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["10/06/2025"],  # 97 days before
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "Τελευταία": [500.9],  # Alternative name
            "Προηγούμενη": [200.3],  # Alternative name
            "ΣυνΩΧΒ": [600.2],  # Alternative name
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check that fallback mapping worked for high difference case
        # Note: With days_diff=97 (>60), should use initial/previous values
        # The fallback mapping creates Κατανάλωση_Προηγούμενη from Προηγούμενη
        assert pd.isna(
            result["ΑρχικήΚατανάλωση"].iloc[0]
        )  # No Κατανάλωση_Αρχική column
        assert (
            result["ΠροηγούμενηΚατανάλωση"].iloc[0] == 200.3
        )  # Fallback mapping worked
        assert pd.isna(
            result["ΤελευταίαΚατανάλωση"].iloc[0]
        )  # Not used in high diff case
        assert pd.isna(
            result["ΣυνολικήΚατανάλωση"].iloc[0]
        )  # Not used in high diff case

    def test_case_d_invalid_date_handling(self):
        """Test Case D: Invalid date → days_diff=NaN, all condition fields NaN."""

        # Create test data with invalid date
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["invalid_date"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["17/07/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "Κατανάλωση_Τελευταία": [500.9],
            "Κατανάλωση_Σύνολο": [600.2],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check that days_diff is NaN
        assert pd.isna(result["days_diff"].iloc[0])

        # Check that all condition-dependent fields are NaN
        assert pd.isna(result["ΑρχικήΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΠροηγούμενηΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΑρχικήΛογαριασμού"].iloc[0])
        assert pd.isna(result["ΑρχικήΠροηγούμενηΛογαριασμού"].iloc[0])
        assert pd.isna(result["ΤελευταίαΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΣυνολικήΚατανάλωση"].iloc[0])

    def test_missing_date_columns(self):
        """Test handling of missing required date columns."""

        # Create test data without date columns
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check that days_diff is NaN
        assert pd.isna(result["days_diff"].iloc[0])

        # Check that all condition-dependent fields are NaN
        assert pd.isna(result["ΑρχικήΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΠροηγούμενηΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΑρχικήΛογαριασμού"].iloc[0])
        assert pd.isna(result["ΑρχικήΠροηγούμενηΛογαριασμού"].iloc[0])
        assert pd.isna(result["ΤελευταίαΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΣυνολικήΚατανάλωση"].iloc[0])

    def test_mixed_scenarios(self):
        """Test multiple records with different scenarios."""

        # Create test data with mixed scenarios
        data = {
            "ΑρΠαροχής": ["12345", "12346", "12347"],
            "ΑρΛογαριασμού": ["67890", "67891", "67892"],
            "ΗμΈκδοσης": ["15/09/2025", "15/09/2025", "invalid_date"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["10/06/2025", "17/07/2025", "17/07/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": [
                "Test Address 1",
                "Test Address 2",
                "Test Address 3",
            ],
            "Πόλη": ["Athens", "Thessaloniki", "Patras"],
            "Κατανάλωση_Αρχική": [100.5, 200.5, 300.5],
            "Κατανάλωση_Προηγούμενη": [150.3, 250.3, 350.3],
            "Κατανάλωση_Τελευταία": [500.9, 600.9, 700.9],
            "Κατανάλωση_Σύνολο": [600.2, 700.2, 800.2],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check first record (days_diff=97, >60) - should use initial/previous
        assert result["days_diff"].iloc[0] == 97
        assert result["ΑρχικήΚατανάλωση"].iloc[0] == 100.5
        assert result["ΠροηγούμενηΚατανάλωση"].iloc[0] == 150.3
        assert pd.isna(result["ΤελευταίαΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΣυνολικήΚατανάλωση"].iloc[0])

        # Check second record (days_diff=60, ≤60) - should use latest/total
        assert result["days_diff"].iloc[1] == 60
        assert pd.isna(result["ΑρχικήΚατανάλωση"].iloc[1])
        assert pd.isna(result["ΠροηγούμενηΚατανάλωση"].iloc[1])
        assert result["ΤελευταίαΚατανάλωση"].iloc[1] == 600.9
        assert result["ΣυνολικήΚατανάλωση"].iloc[1] == 700.2

        # Check third record (invalid date) - should have NaN for all condition fields
        assert pd.isna(result["days_diff"].iloc[2])
        assert pd.isna(result["ΑρχικήΚατανάλωση"].iloc[2])
        assert pd.isna(result["ΠροηγούμενηΚατανάλωση"].iloc[2])
        assert pd.isna(result["ΤελευταίαΚατανάλωση"].iloc[2])
        assert pd.isna(result["ΣυνολικήΚατανάλωση"].iloc[2])

    def test_date_formatting(self):
        """Test that dates are formatted as dd/mm/yyyy strings."""

        # Create test data
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["10/06/2025"],
            "ΠερίοδοςΚατανάλωσης_Τέλος": ["10/07/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check that dates are formatted as strings
        assert isinstance(result["ΗμΈκδοσης"].iloc[0], str)
        assert isinstance(result["ΠερίοδοςΚατανάλωσης_Αρχή"].iloc[0], str)
        assert isinstance(result["ΠερίοδοςΚατανάλωσης_Τέλος"].iloc[0], str)

        # Check format is dd/mm/yyyy
        assert result["ΗμΈκδοσης"].iloc[0] == "15/09/2025"
        assert result["ΠερίοδοςΚατανάλωσης_Αρχή"].iloc[0] == "10/06/2025"
        assert result["ΠερίοδοςΚατανάλωσης_Τέλος"].iloc[0] == "10/07/2025"

    def test_output_column_order(self):
        """Test that output columns are in the correct order."""

        # Create minimal test data
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["10/06/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check column order
        expected_columns = [
            "ΑρΠαροχής",
            "ΑρΛογαριασμού",
            "ΗμΈκδοσης",
            "ΠερίοδοςΚατανάλωσης_Αρχή",
            "ΠερίοδοςΚατανάλωσης_Τέλος",
            "Ονοματεπώνυμο_Διεύθυνση",
            "Πόλη",
            "days_diff",
            "ΑρχικήΚατανάλωση",
            "ΠροηγούμενηΚατανάλωση",
            "ΑρχικήΛογαριασμού",
            "ΑρχικήΠροηγούμενηΛογαριασμού",
            "ΤελευταίαΚατανάλωση",
            "ΣυνολικήΚατανάλωση",
        ]

        assert list(result.columns) == expected_columns

    def test_save_function(self):
        """Test the save_transform_consumptions function."""

        # Create test data
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["10/06/2025"],
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "days_diff": [97],
            "ΑρχικήΚατανάλωση": [100.5],
            "ΠροηγούμενηΚατανάλωση": [200.3],
            "ΑρχικήΛογαριασμού": [300.7],
            "ΑρχικήΠροηγούμενηΛογαριασμού": [400.1],
            "ΤελευταίαΚατανάλωση": [np.nan],
            "ΣυνολικήΚατανάλωση": [np.nan],
        }

        df = pd.DataFrame(data)
        output_path = "./output/test_transform_consumptions.xlsx"

        # Save the data
        save_transform_consumptions(df, output_path)

        # Check that file was created
        assert Path(output_path).exists()

        # Clean up
        Path(output_path).unlink()

    def test_edge_case_exactly_60_days(self):
        """Test edge case where days_diff is exactly 60 (should use latest/total)."""

        # Create test data with exactly 60 days difference
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["15/09/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["17/07/2025"],  # Exactly 60 days before
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "Κατανάλωση_Αρχική": [100.5],
            "Κατανάλωση_Προηγούμενη": [200.3],
            "Κατανάλωση_Τελευταία": [500.9],
            "Κατανάλωση_Σύνολο": [600.2],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check days_diff calculation
        assert result["days_diff"].iloc[0] == 60

        # Check that latest/total values are used (≤60 includes exactly 60)
        assert result["ΤελευταίαΚατανάλωση"].iloc[0] == 500.9
        assert result["ΣυνολικήΚατανάλωση"].iloc[0] == 600.2

        # Check that initial/previous values are NaN
        assert pd.isna(result["ΑρχικήΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΠροηγούμενηΚατανάλωση"].iloc[0])

    def test_negative_days_diff(self):
        """Test handling of negative days_diff (issue date before consumption period)."""

        # Create test data where issue date is before consumption period
        data = {
            "ΑρΠαροχής": ["12345"],
            "ΑρΛογαριασμού": ["67890"],
            "ΗμΈκδοσης": ["10/06/2025"],
            "ΠερίοδοςΚατανάλωσης_Αρχή": ["15/09/2025"],  # 97 days after issue date
            "Ονοματεπώνυμο_Διεύθυνση": ["Test Address"],
            "Πόλη": ["Athens"],
            "Κατανάλωση_Αρχική": [100.5],
            "Κατανάλωση_Προηγούμενη": [200.3],
            "Κατανάλωση_Τελευταία": [500.9],
            "Κατανάλωση_Σύνολο": [600.2],
        }

        df = pd.DataFrame(data)
        result = transform_consumptions(df)

        # Check days_diff calculation (should be negative)
        assert result["days_diff"].iloc[0] == -97

        # Check that abs(days_diff) > 60, so initial/previous values are used
        assert result["ΑρχικήΚατανάλωση"].iloc[0] == 100.5
        assert result["ΠροηγούμενηΚατανάλωση"].iloc[0] == 200.3
        assert pd.isna(result["ΤελευταίαΚατανάλωση"].iloc[0])
        assert pd.isna(result["ΣυνολικήΚατανάλωση"].iloc[0])
