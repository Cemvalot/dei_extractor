"""
Final 2023 transformation module for converting Phase-1 output to final dataset format.

This module handles the conversion from the filtered Phase-1 Excel file to the final
ΠΑΡΟΧΕΣ 2023 format with proper grouping, calculations, and classification.
"""

import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def get_target_columns(year: int) -> List[str]:
    """Generate target column names with dynamic year formatting."""
    return [
        "Α/Α",
        "ΠΑΡΟΧΗ",
        "ΑΡΙΘΜΟΣ ΣΥΜΒΟΛΑΙΟΥ ",
        "ΟΝΟΜΑ ",  # Now contains combined name and city
        "ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)",
        "ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ",
        "ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
        "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ",
        "ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
        "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
        "ΣΧΟΛΙΟ",
        f"ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/{year}",
        f"ΑΡ. ΗΜΕΡΩΝ ΜΕΤΑ ΤΙΣ 31/12/{year}",
        "ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ",
        "ΑΡ. ΗΜΕΡΩΝ 2019",
        "ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH",
        "ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ.",
        f"ΚΑΤΑΝΑΛΩΣΗ {year} KWH",
        f"ΚΑΤΑΝΑΛΩΣΗ ΗΜΕΡΩΝ ΠΡΙΝ ΤΗΣ 1.1.{year}",
        f"ΚΑΤΑΝΑΛΩΣΗ 1.1.{year}",
        f"ΚΑΤΑΝΑΛΩΣΗ 1.1.{year}.1",
        f"ΚΑΤΑΝΑΛΩΣΗ 31.12.{year}",
        "ΔΙΑΦΟΡΑ ΚΑΤΑΝΑΛΩΣΗΣ KWH",
        "Unnamed: 25",
    ]


# Target column names exactly as specified (for backward compatibility)
TARGET_COLUMNS = get_target_columns(2023)

# Infrastructure keywords for classification
INFRASTRUCTURE_KEYWORDS = [
    "ΣΧΟΛΕΙΟ",
    "ΓΥΜΝΑΣΙΟ",
    "ΛΥΚΕΙΟ",
    "ΝΗΠΙΑΓΩΓΕΙΟ",
    "ΔΗΜΑΡΧΕΙΟ",
    "ΥΠΗΡΕΣΙΑ",
    "ΓΗΠΕΔΟ",
    "ΚΛΕΙΣΤΟ",
    "ΚΟΛΥΜΒΗΤΗΡΙΟ",
    "ΑΙΘΟΥΣΑ",
    "ΘΕΑΤΡ",
    "ΚΑΠΗ",
    "ΠΑΙΔΙΚΟΣ",
    "ΠΟΛΥΧΩΡΟΣ",
    "ΑΝΤΛΙΟΣΤΑΣΙΟ",
    "ΔΗΜΟΣ",
    "ΚΟΙΝΟΤΗΤΑ",
    "ΚΟΙΝΟΤΗΣ",
    "ΠΕΡΙΦΕΡΕΙΑ",
    "ΝΟΜΑΡΧΙΑ",
]

# Sector classification mapping
SECTOR_MAPPING = {
    "ΣΧΟΛΕΙΟ": "ΣΧΟΛΕΙΟ",
    "ΓΥΜΝΑΣΙΟ": "ΣΧΟΛΕΙΟ",
    "ΛΥΚΕΙΟ": "ΣΧΟΛΕΙΟ",
    "ΝΗΠΙΑΓΩΓΕΙΟ": "ΣΧΟΛΕΙΟ",
    "ΚΑΠΗ": "ΚΑΠΗ",
    "ΔΗΜΑΡΧΕΙΟ": "ΔΗΜΑΡΧΕΙΑ - ΔΗΜΟΣΙΕΣ ΥΠΗΡΕΣΙΕΣ",
    "ΥΠΗΡΕΣΙΑ": "ΔΗΜΑΡΧΕΙΑ - ΔΗΜΟΣΙΕΣ ΥΠΗΡΕΣΙΕΣ",
    "ΚΟΙΝΟΤΗΣ": "ΔΗΜΑΡΧΕΙΑ - ΔΗΜΟΣΙΕΣ ΥΠΗΡΕΣΙΕΣ",
    "ΚΟΙΝΟΤΗΤΑ": "ΔΗΜΑΡΧΕΙΑ - ΔΗΜΟΣΙΕΣ ΥΠΗΡΕΣΙΕΣ",
    "ΓΗΠΕΔΟ": "ΑΘΛ. ΕΓΚ/ΣΤΑΣΗ",
    "ΚΛΕΙΣΤΟ": "ΑΘΛ. ΕΓΚ/ΣΤΑΣΗ",
    "ΚΟΛΥΜΒΗΤΗΡΙΟ": "ΑΘΛ. ΕΓΚ/ΣΤΑΣΗ",
    "ΑΝΤΛΙΟΣΤΑΣΙΟ": "ΛΟΙΠΕΣ ΥΠΟΔΟΜΕΣ",
}


def load_phase1(path: str) -> pd.DataFrame:
    """
    Load Phase-1 Excel file and perform initial data cleaning.

    Args:
        path: Path to the Phase-1 Excel file

    Returns:
        Cleaned DataFrame with parsed dates and validated data
    """
    logger.info(f"Loading Phase-1 data from {path}")

    # Load the Excel file
    df = pd.read_excel(path, sheet_name="Sheet1")

    # Clean column names (strip whitespace, normalize spaces)
    df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)

    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")

    # Parse consumption period dates
    df = _parse_consumption_periods(df)

    # Convert numeric columns
    df = _convert_numeric_columns(df)

    # Validate required columns
    required_columns = [
        "ΑρΠαροχής",
        "ΑρΛογαριασμού",
        "ΠερίοδοςΚατανάλωσης",
        "Τελευταία",
        "Προηγούμενη",
        "ΣυνΩΧΒ",
        "Ονοματεπώνυμο_Διεύθυνση",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return df


def _parse_consumption_periods(df: pd.DataFrame) -> pd.DataFrame:
    """Parse ΠερίοδοςΚατανάλωσης into start and end dates."""

    def parse_period(period_str):
        if pd.isna(period_str):
            return pd.NaT, pd.NaT

        try:
            # Format: dd.mm.yyyy-dd.mm.yyyy
            start_str, end_str = period_str.split("-")
            start_date = pd.to_datetime(start_str, format="%d.%m.%Y", dayfirst=True)
            end_date = pd.to_datetime(end_str, format="%d.%m.%Y", dayfirst=True)
            return start_date, end_date
        except Exception as e:
            logger.warning(f"Could not parse period: {period_str}, error: {e}")
            return pd.NaT, pd.NaT

    # Parse periods
    periods = df["ΠερίοδοςΚατανάλωσης"].apply(parse_period)
    df["start_date"] = [p[0] for p in periods]
    df["end_date"] = [p[1] for p in periods]

    # Calculate period days
    df["period_days"] = (df["end_date"] - df["start_date"]).dt.days

    # Filter out invalid periods (including NaT)
    invalid_mask = (
        (df["period_days"] <= 0) | df["start_date"].isna() | df["end_date"].isna()
    )
    invalid_periods = df[invalid_mask]
    if len(invalid_periods) > 0:
        logger.warning(
            f"Found {len(invalid_periods)} records with invalid periods (days <= 0 or NaT)"
        )
        df = df[~invalid_mask]

    return df


def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns to appropriate types."""

    # Convert meter readings to numeric (force float to handle NaN values)
    for col in ["Τελευταία", "Προηγούμενη", "ΣυνΩΧΒ", "ΣΩΧΒ"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

    # Convert service ID to string to preserve leading zeros
    df["ΑρΠαροχής"] = df["ΑρΠαροχής"].astype(str)
    df["ΑρΛογαριασμού"] = df["ΑρΛογαριασμού"].astype(str)

    return df


def compute_final(
    df: pd.DataFrame,
    year: int = 2023,
    class_map_path: Optional[str] = None,
    window_days: int = 60,
    target_span_days: int = 365,
) -> pd.DataFrame:
    """
    Compute the final dataset by grouping and calculating metrics for each service.

    Args:
        df: Phase-1 DataFrame
        year: Target year for calculations (default: 2023)
        class_map_path: Optional path to classification mapping CSV

    Returns:
        Final DataFrame with one row per service
    """
    logger.info(f"Computing final dataset for year {year}")

    # Parse periods and convert numeric columns if not already done
    if "start_date" not in df.columns:
        df = _parse_consumption_periods(df)
        df = _convert_numeric_columns(df)

    # Load classification mapping if provided
    class_mapping = _load_classification_mapping(class_map_path)

    # Group by service and compute metrics
    results = []

    for service_id, group in df.groupby("ΑρΠαροχής"):
        try:
            result = _compute_service_metrics(
                group,
                year,
                class_mapping,
                window_days=window_days,
                target_span_days=target_span_days,
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing service {service_id}: {e}")
            continue

    if not results:
        raise ValueError("No valid results generated")

    # Create final DataFrame
    final_df = pd.DataFrame(results)

    # Sort by service ID and assign sequential index
    final_df = final_df.sort_values("ΠΑΡΟΧΗ")
    final_df["Α/Α"] = range(1, len(final_df) + 1)

    # Reorder columns to match target schema
    target_columns = get_target_columns(year)
    final_df = final_df[target_columns]

    logger.info(f"Generated final dataset with {len(final_df)} services")

    return final_df


def _compute_service_metrics(
    group: pd.DataFrame,
    year: int,
    class_mapping: Dict,
    window_days: int = 60,
    target_span_days: int = 365,
) -> Dict:
    """Compute metrics for a single service."""

    # Sort by start date
    group = group.sort_values("start_date")

    # Find the window covering the target year
    window_start, window_end, initial_reading, final_reading = _find_consumption_window(
        group, year, window_days=window_days, target_span_days=target_span_days
    )

    # Calculate core metrics
    captured_days = (window_end - window_start).days
    captured_kwh = final_reading - initial_reading

    # Handle meter reset (final < initial)
    if captured_kwh < 0:
        logger.warning(
            f"Service {group['ΑρΠαροχής'].iloc[0]} has meter reset, using sum method"
        )
        captured_kwh = _calculate_sum_consumption(group, window_start, window_end)

    # Calculate daily consumption rate
    mean_per_day = captured_kwh / captured_days if captured_days > 0 else np.nan

    # Calculate days before/after target year
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31)

    days_before_year = (year_start - window_start).days
    days_after_year = (window_end - year_end).days

    # Calculate interpolated readings at year boundaries
    reading_at_year_01_01, reading_at_year_12_31 = _interpolate_readings(
        group,
        year_start,
        year_end,
        window_start,
        window_end,
        initial_reading,
        final_reading,
    )

    # Calculate year consumption as difference between interpolated readings
    consumption_year = (
        reading_at_year_12_31 - reading_at_year_01_01
        if not pd.isna(reading_at_year_12_31) and not pd.isna(reading_at_year_01_01)
        else np.nan
    )

    # Calculate consumption before year (prorated)
    consumption_before_year = (
        mean_per_day * days_before_year if not pd.isna(mean_per_day) else np.nan
    )

    # Calculate absolute reading at year start
    reading_at_year_01_01_abs = (
        abs(reading_at_year_01_01) if not pd.isna(reading_at_year_01_01) else np.nan
    )

    # Get service information
    service_id = group["ΑρΠαροχής"].iloc[0]
    account_id = group["ΑρΛογαριασμού"].iloc[0]
    site_name = group["Ονοματεπώνυμο_Διεύθυνση"].iloc[0]
    city = group["Πόλη"].iloc[0] if "Πόλη" in group.columns else ""

    # Clean site name
    clean_name = _clean_site_name(site_name)

    # Create filtered column combining name/address and city
    filtered_name = _create_filtered_name(clean_name, city)

    # Classify infrastructure
    infrastructure_flag, facility_type, subtype, sector = _classify_infrastructure(
        clean_name, group, class_mapping
    )

    return {
        "Α/Α": np.nan,  # Will be set later
        "ΠΑΡΟΧΗ": service_id,
        "ΑΡΙΘΜΟΣ ΣΥΜΒΟΛΑΙΟΥ ": account_id,
        "ΟΝΟΜΑ ": filtered_name,  # Combined name and city (replaces old ΟΝΟΜΑ)
        "ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)": infrastructure_flag,
        "ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ": facility_type,
        "ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ": window_start,
        "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ": initial_reading,
        "ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ": window_end,
        "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ": final_reading,
        "ΣΧΟΛΙΟ": "",
        f"ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/{year}": days_before_year,
        f"ΑΡ. ΗΜΕΡΩΝ ΜΕΤΑ ΤΙΣ 31/12/{year}": days_after_year,
        "ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ": captured_days,
        "ΑΡ. ΗΜΕΡΩΝ 2019": 365,
        "ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH": captured_kwh,
        "ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ.": mean_per_day,
        f"ΚΑΤΑΝΑΛΩΣΗ {year} KWH": consumption_year,
        f"ΚΑΤΑΝΑΛΩΣΗ ΗΜΕΡΩΝ ΠΡΙΝ ΤΗΣ 1.1.{year}": consumption_before_year,
        f"ΚΑΤΑΝΑΛΩΣΗ 1.1.{year}": reading_at_year_01_01,
        f"ΚΑΤΑΝΑΛΩΣΗ 1.1.{year}.1": reading_at_year_01_01_abs,
        f"ΚΑΤΑΝΑΛΩΣΗ 31.12.{year}": reading_at_year_12_31,
        "ΔΙΑΦΟΡΑ ΚΑΤΑΝΑΛΩΣΗΣ KWH": consumption_year,  # Duplicate as per sample
        "Unnamed: 25": sector,
    }


def _interpolate_readings(
    group: pd.DataFrame,
    year_start: datetime,
    year_end: datetime,
    window_start: datetime,
    window_end: datetime,
    initial_reading: float,
    final_reading: float,
) -> Tuple[float, float]:
    """
    Interpolate meter readings at year boundaries using linear interpolation.

    Args:
        group: Service data group
        year_start: Start of target year (1/1/{year})
        year_end: End of target year (31/12/{year})
        window_start: Start of consumption window
        window_end: End of consumption window
        initial_reading: Reading at window start
        final_reading: Reading at window end

    Returns:
        Tuple of (reading_at_year_start, reading_at_year_end)
    """
    # If target date is before or at window start, use initial reading
    if year_start <= window_start:
        reading_at_year_start = initial_reading
    # If target date is after or at window end, use final reading
    elif year_start >= window_end:
        reading_at_year_start = final_reading
    else:
        # Linear interpolation within the window
        total_days = (window_end - window_start).days
        days_from_start = (year_start - window_start).days
        if total_days > 0:
            interpolation_factor = days_from_start / total_days
            reading_at_year_start = (
                initial_reading
                + (final_reading - initial_reading) * interpolation_factor
            )
        else:
            reading_at_year_start = initial_reading

    # Same logic for year end
    if year_end <= window_start:
        reading_at_year_end = initial_reading
    elif year_end >= window_end:
        reading_at_year_end = final_reading
    else:
        # Linear interpolation within the window
        total_days = (window_end - window_start).days
        days_from_start = (year_end - window_start).days
        if total_days > 0:
            interpolation_factor = days_from_start / total_days
            reading_at_year_end = (
                initial_reading
                + (final_reading - initial_reading) * interpolation_factor
            )
        else:
            reading_at_year_end = initial_reading

    return reading_at_year_start, reading_at_year_end


def _find_consumption_window(
    group: pd.DataFrame, year: int, window_days: int = 60, target_span_days: int = 365
) -> Tuple[datetime, datetime, float, float]:
    """Find the consumption window covering the target year using settlement-based span selection with fallbacks."""

    from dei_extractor.logic.span_selection import Bill, select_year_span

    # Ensure deterministic order and reset index to map selections back
    group_sorted = group.sort_values("start_date").reset_index(drop=True)

    # Prepare settlement flag; if column missing, treat all as settlements to avoid empty candidate set
    has_settlement = "Εκαθαριστικός" in group_sorted.columns

    def to_bool(x) -> bool:
        if isinstance(x, bool):
            return x
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return False
        s = str(x).strip().lower()
        return s in {"true", "1", "yes", "y", "ναι", "nai"}

    bills: List[Bill] = []
    for idx, row in group_sorted.iterrows():
        start_ts = row["start_date"]
        end_ts = row["end_date"]
        if pd.isna(start_ts) or pd.isna(end_ts):
            continue
        is_settlement = to_bool(row["Εκαθαριστικός"]) if has_settlement else True
        bills.append(
            Bill(
                is_settlement=is_settlement,
                period_start=start_ts.date(),
                period_end=end_ts.date(),
                row_index=idx,
            )
        )

    # Try selection by settlement windows
    res = select_year_span(
        bills, year=year, window_days=window_days, target_span_days=target_span_days
    )

    # If successful, map back to rows and return readings
    if res.start is not None and res.end is not None:
        start_row = (
            group_sorted.iloc[res.start.row_index]
            if res.start.row_index is not None
            else group_sorted.iloc[0]
        )
        end_row = (
            group_sorted.iloc[res.end.row_index]
            if res.end.row_index is not None
            else group_sorted.iloc[-1]
        )
        window_start = pd.to_datetime(start_row["start_date"])
        window_end = pd.to_datetime(end_row["end_date"])
        initial_reading = (
            float(start_row["Προηγούμενη"])
            if "Προηγούμενη" in start_row
            else float("nan")
        )
        final_reading = (
            float(end_row["Τελευταία"]) if "Τελευταία" in end_row else float("nan")
        )
        return window_start, window_end, initial_reading, final_reading

    # Fallback to legacy heuristic if settlement selection not possible
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31)

    contains_start = group[
        (group["start_date"] <= year_start) & (group["end_date"] >= year_start)
    ]
    contains_end = group[
        (group["start_date"] <= year_end) & (group["end_date"] >= year_end)
    ]

    if len(contains_start) > 0:
        window_start_period = contains_start.sort_values("start_date").iloc[0]
        window_start = window_start_period["start_date"]
        initial_reading = window_start_period["Προηγούμενη"]
    else:
        preceding = group[group["end_date"] < year_start]
        if len(preceding) > 0:
            window_start_period = preceding.sort_values("end_date").iloc[-1]
            window_start = window_start_period["start_date"]
            initial_reading = window_start_period["Προηγούμενη"]
        else:
            window_start_period = group.sort_values("start_date").iloc[0]
            window_start = window_start_period["start_date"]
            initial_reading = window_start_period["Προηγούμενη"]

    if len(contains_end) > 0:
        window_end_period = contains_end.sort_values("end_date").iloc[0]
        window_end = window_end_period["end_date"]
        final_reading = window_end_period["Τελευταία"]
    else:
        following = group[group["start_date"] > year_end]
        if len(following) > 0:
            window_end_period = following.sort_values("start_date").iloc[0]
            window_end = window_end_period["end_date"]
            final_reading = window_end_period["Τελευταία"]
        else:
            window_end_period = group.sort_values("end_date").iloc[-1]
            window_end = window_end_period["end_date"]
            final_reading = window_end_period["Τελευταία"]

    return window_start, window_end, initial_reading, final_reading


def _calculate_sum_consumption(
    group: pd.DataFrame, window_start: datetime, window_end: datetime
) -> float:
    """Calculate total consumption by summing ΣυνΩΧΒ across the window."""

    # Filter periods within the window
    window_periods = group[
        (group["start_date"] >= window_start) & (group["end_date"] <= window_end)
    ]

    if len(window_periods) == 0:
        return 0.0

    # Sum consumption
    total_consumption = window_periods["ΣυνΩΧΒ"].sum()

    return total_consumption


def _clean_site_name(name: str) -> str:
    """Clean and normalize site name."""
    if pd.isna(name):
        return ""

    # Convert to string and uppercase
    name = str(name).upper()

    # Normalize spaces
    name = re.sub(r"\s+", " ", name).strip()

    # Remove duplicated words (simple approach)
    words = name.split()
    cleaned_words = []
    for word in words:
        if word not in cleaned_words or word not in ["ΔΗΜΟΣ", "ΚΟΙΝΟΤΗΤΑ"]:
            cleaned_words.append(word)

    return " ".join(cleaned_words)


def _create_filtered_name(name: str, city: str) -> str:
    """Create filtered column combining name/address and city."""
    if pd.isna(name):
        name = ""
    if pd.isna(city):
        city = ""

    # Convert to string and uppercase
    name = str(name).upper().strip()
    city = str(city).upper().strip()

    # If city is already in the name, just return the name
    if city and city in name:
        return name

    # Combine name and city
    if name and city:
        return f"{name} - {city}"
    elif name:
        return name
    elif city:
        return city
    else:
        return ""


def _classify_infrastructure(
    name: str, group: pd.DataFrame, class_mapping: Dict
) -> Tuple[str, str, str, str]:
    """Classify infrastructure type based on name and category."""

    # Determine facility type first
    facility_type = "ΛΟΙΠΑ"
    if "ΚατηγορίαΤιμολογίου" in group.columns:
        category = group["ΚατηγορίαΤιμολογίου"].iloc[0]
        if pd.notna(category):
            facility_type = str(category).upper()

    # CRITICAL: If ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ == "ΦΟΠ", then NEVER classify as infrastructure
    if facility_type == "ΦΟΠ":
        infrastructure_flag = "ΟΧΙ"
        subtype = "ΟΧΙ"
        sector = "ΛΟΙΠΕΣ ΥΠΟΔΟΜΕΣ"
    else:
        # Check for infrastructure keywords only for non-ΦΟΠ cases
        is_infrastructure = any(keyword in name for keyword in INFRASTRUCTURE_KEYWORDS)
        infrastructure_flag = "ΝΑΙ" if is_infrastructure else "ΟΧΙ"

        # Determine subtype
        subtype = "ΛΟΙΠΑ"
        if "ΑΝΤΛΙΟΣΤΑΣΙΟ" in name:
            subtype = "ΑΝΤΛΙΟΣΤΑΣΙΟ"
        elif is_infrastructure:
            subtype = "ΝΑΙ"
        else:
            subtype = "ΟΧΙ"

        # Determine sector
        sector = "ΛΟΙΠΕΣ ΥΠΟΔΟΜΕΣ"
        for keyword, sector_name in SECTOR_MAPPING.items():
            if keyword in name:
                sector = sector_name
                break

    # Apply custom mapping if provided (but ΦΟΠ overrides)
    if class_mapping and facility_type != "ΦΟΠ":
        for pattern, sub, buck in class_mapping:
            if pattern in name:
                subtype = sub
                sector = buck
                break

    return infrastructure_flag, facility_type, subtype, sector


def _load_classification_mapping(path: Optional[str]) -> List[Tuple[str, str, str]]:
    """Load custom classification mapping from CSV file."""
    if not path or not Path(path).exists():
        return []

    try:
        mapping_df = pd.read_csv(path)
        if len(mapping_df.columns) >= 3:
            return list(
                zip(mapping_df.iloc[:, 0], mapping_df.iloc[:, 1], mapping_df.iloc[:, 2])
            )
    except Exception as e:
        logger.warning(f"Could not load classification mapping from {path}: {e}")

    return []


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename specific columns to match the required format."""
    rename_map = {"ΚΑΤΑΝΑΛΩΣΗ 1.1.2023.1": "ΚΑΤΑΝΑΛΩΣΗ 1.1.2023 Πραγματικό"}
    return df.rename(columns=rename_map)


def format_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Format date columns to dd/mm/yyyy string format."""
    for col in ["ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ", "ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ "]:
        if col in df.columns:
            # Convert to datetime (if not already)
            df[col] = pd.to_datetime(df[col], errors="coerce")
            # Display as string dd/mm/yyyy
            df[col] = df[col].dt.strftime("%d/%m/%Y")
    return df


def write_final(
    df: pd.DataFrame, path: str, decimals_mode: str = "round", year: int = 2023
):
    """
    Write final dataset to Excel file with proper formatting and number formatting.

    Args:
        df: Final DataFrame
        path: Output file path
        decimals_mode: "round" (default) or "truncate" for 2-decimal formatting
    """
    from dei_extractor.utils.number_format import enforce_two_decimals

    logger.info(
        f"Writing final dataset to {path} with {decimals_mode} mode for 2-decimal formatting"
    )

    # 1. rename columns
    df = rename_columns(df)

    # 2. enforce numbers 2 decimals
    df = enforce_two_decimals(df, mode=decimals_mode)

    # 3. format dates
    df = format_dates(df)

    # 3. export with Excel formatting
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        # Write main data
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        # Format header
        header_format = workbook.add_format(
            {"bold": True, "text_wrap": True, "valign": "top", "border": 1}
        )

        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

        # Set column widths and apply number formatting
        numfmt_2dec = workbook.add_format({"num_format": "0.00"})
        numfmt_int = workbook.add_format({"num_format": "0"})
        for col_num, column in enumerate(df.columns):
            max_length = max(df[column].astype(str).map(len).max(), len(str(column)))
            if pd.api.types.is_numeric_dtype(df[column]):
                # Check if column has decimal values to determine format
                has_decimals = (
                    df[column]
                    .apply(
                        lambda x: not pd.isna(x) and x != int(x)
                        if isinstance(x, (int, float))
                        else False
                    )
                    .any()
                )
                if has_decimals:
                    # Apply 2-decimal format for columns with decimal values
                    worksheet.set_column(
                        col_num, col_num, min(max_length + 2, 50), numfmt_2dec
                    )
                else:
                    # Apply integer format for columns with only whole numbers
                    worksheet.set_column(
                        col_num, col_num, min(max_length + 2, 50), numfmt_int
                    )
            else:
                # Regular formatting for non-numeric columns
                worksheet.set_column(col_num, col_num, min(max_length + 2, 50))

        # Create metadata sheet
        _create_metadata_sheet(workbook, year)

    logger.info(f"Successfully wrote {len(df)} records to {path}")


def _create_metadata_sheet(workbook, year: int = 2023):
    """Create metadata sheet with column descriptions."""

    metadata = [
        ["Column", "Description", "Formula/Notes"],
        ["Α/Α", "Sequential index", "Auto-generated 1..N"],
        ["ΠΑΡΟΧΗ", "Service/Meter ID", "From ΑρΠαροχής"],
        ["ΑΡΙΘΜΟΣ ΣΥΜΒΟΛΑΙΟΥ ", "Account/Contract number", "From ΑρΛογαριασμού"],
        [
            "ΟΝΟΜΑ ",
            "Site name and address with city",
            "Combined Ονοματεπώνυμο_Διεύθυνση + Πόλη",
        ],
        [
            "ΚΤΗΡΙΟ - ΥΠΟΔΟΜΕΣ (ΝΑΙ / ΟΧΙ)",
            "Infrastructure flag",
            "Keyword-based classification",
        ],
        ["ΕΙΔΟΣ ΥΠΟΔΟΜΗΣ", "Facility type", "From ΚατηγορίαΤιμολογίου or inferred"],
        ["ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ", "Window start date", "Period containing 2023-01-01"],
        [
            "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΑΡΧΙΚΗ ΗΜΕΡΟΜΗΝΙΑ",
            "Initial meter reading",
            "Προηγούμενη at window start",
        ],
        ["ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ", "Window end date", "Period containing 2023-12-31"],
        [
            "ΚΑΤΑΓΡΑΦΗ ΣΤΗΝ ΤΕΛΙΚΗ ΗΜΕΡΟΜΗΝΙΑ ",
            "Final meter reading",
            "Τελευταία at window end",
        ],
        ["ΣΧΟΛΙΟ", "Comments", "Empty by default"],
        [
            f"ΑΡ. ΗΜΕΡΩΝ ΠΡΙΝ ΑΠΟ 1/1/{year}",
            f"Days before {year}",
            f"({year}-01-01 - window_start).days",
        ],
        [
            f"ΑΡ. ΗΜΕΡΩΝ ΜΕΤΑ ΤΙΣ 31/12/{year}",
            f"Days after {year}",
            f"(window_end - {year}-12-31).days",
        ],
        [
            "ΚΑΤΑΓΡΑΦΟΜΕΝΗ ΠΕΡΙΟΔΟΣ",
            "Captured period days",
            "(window_end - window_start).days",
        ],
        ["ΑΡ. ΗΜΕΡΩΝ 2019", "Days in 2019", "Constant 365"],
        [
            "ΚΑΤΑΝΑΛΩΣΗ ΚΑΤΑΓΡΑΦΟΜΕΝΗΣ ΠΕΡ. KWH",
            "Captured consumption",
            "final_reading - initial_reading",
        ],
        [
            "ΜΕΣΗ ΚΑΤΑΝΑΛΩΣΗ/ΗΜ.",
            "Average daily consumption",
            "captured_kwh / captured_days",
        ],
        [
            f"ΚΑΤΑΝΑΛΩΣΗ {year} KWH",
            f"{year} consumption (interpolated)",
            "reading_at_year_end - reading_at_year_start",
        ],
        [
            f"ΚΑΤΑΝΑΛΩΣΗ ΗΜΕΡΩΝ ΠΡΙΝ ΤΗΣ 1.1.{year}",
            f"Consumption before {year}",
            "mean_per_day * days_before_year",
        ],
        [
            f"ΚΑΤΑΝΑΛΩΣΗ 1.1.{year}",
            f"Reading at {year}-01-01 (interpolated)",
            "Linear interpolation from window readings",
        ],
        [
            f"ΚΑΤΑΝΑΛΩΣΗ 1.1.{year}.1",
            f"Absolute reading at {year}-01-01",
            "abs(reading_at_year_01_01)",
        ],
        [
            f"ΚΑΤΑΝΑΛΩΣΗ 31.12.{year}",
            f"Reading at {year}-12-31 (interpolated)",
            "Linear interpolation from window readings",
        ],
        [
            "ΔΙΑΦΟΡΑ ΚΑΤΑΝΑΛΩΣΗΣ KWH",
            "Consumption difference",
            "Duplicate of consumption_2023",
        ],
        ["Unnamed: 25", "Sector classification", "High-level sector bucket"],
    ]

    # Create metadata worksheet
    metadata_ws = workbook.add_worksheet("_meta")

    # Write metadata
    for row_num, row in enumerate(metadata):
        for col_num, value in enumerate(row):
            metadata_ws.write(row_num, col_num, value)

    # Format header
    header_format = workbook.add_format({"bold": True, "bg_color": "#D3D3D3"})
    metadata_ws.set_row(0, None, header_format)

    # Set column widths
    metadata_ws.set_column(0, 0, 30)  # Column name
    metadata_ws.set_column(1, 1, 50)  # Description
    metadata_ws.set_column(2, 2, 60)  # Formula/Notes
