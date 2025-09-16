#!/usr/bin/env python3
"""
XLSX exporter for DEI PDF data.

This module provides functions to export parsed DEI data to XLSX format
with standardized column headers and data mapping.
"""

import re
from typing import Dict, List, Optional

import pandas as pd

from ..utils.text import to_digits

# Standardized column headers in exact order (18 columns as specified)
COLUMNS = [
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

# Format_3 specific columns - only the fields requested by user
FORMAT_3_COLUMNS = [
    "Εκαθαριστικός",
    "ΑρΠαροχής",
    "ΑρΛογαριασμού",
    "ΗμΈκδοσης",
    "ΠερίοδοςΚατανάλωσης",
    "Συνολο_kWh_Καταναλωσης",
]


def row_from_payload(payload: Dict, source_file: str) -> Dict:
    """
    Convert a parsed payload to a row dictionary with standardized column mapping.

    Args:
        payload: Parsed data dictionary from format_3 parser
        source_file: Source file path

    Returns:
        Dictionary with standardized column names and values
    """

    # Helper function to get supply number group
    def get_supply_group():
        supply_number = payload.get("supply_number", {})
        if isinstance(supply_number, dict):
            pretty = supply_number.get("pretty", "")
            if pretty:
                # Take first digit block before space/hyphen
                parts = re.split(r"[\s\-]", pretty)
                if parts:
                    return to_digits(parts[0])
            normalized = supply_number.get("normalized", "")
            if normalized:
                return normalized[0] if normalized else ""
        return ""

    # Helper function to get city from recipient data
    def get_city():
        city = payload.get("city")
        if city:
            return city

        postcode_city = payload.get("recipient_postcode_city", "")
        if postcode_city:
            parts = postcode_city.split(" ", 1)
            if len(parts) > 1:
                return parts[1]
        return ""

    # Helper function to get name and address
    def get_name_address():
        name = payload.get("recipient_name", "")
        address = payload.get("recipient_address_line1", "")
        parts = [part for part in [name, address] if part]
        return ", ".join(parts)

    # Build the row dictionary
    row = {
        "ΑρΠαροχής": payload.get("supply_number", {}).get("normalized")
        or to_digits(payload.get("supply_number", "")),
        "ΑρΠαρχ_Ομάδα": get_supply_group(),
        "ΑρΛογαριασμού": payload.get("account_number"),
        "ΗμΈκδοσης": payload.get("issue_date"),
        "ΠερίοδοςΚατανάλωσης": f"{payload.get('period_from', '')}-{payload.get('period_to', '')}",
        "Ονοματεπώνυμο_Διεύθυνση": get_name_address(),
        "Πόλη": get_city(),
        "Τελευταία": payload.get("reading_last"),
        "Προηγούμενη": payload.get("reading_prev"),
        "ΣΩΧΒ": payload.get("kwh_night"),
        "ΣυνΩΧΒ": payload.get("kwh_total"),
        "ΚατηγορίαΤιμολογίου": payload.get("tariff_category"),
        "Υποκατηγορία": payload.get("tariff_subcategory"),
        "Εκαθαριστικός": "ΝΑΙ" if payload.get("is_clearing") else "ΟΧΙ",
        "source_file": source_file,
        "ΠερίοδοςΚατανάλωσης_Αρχική": payload.get("period_from"),
        "ΠερίοδοςΚατανάλωσης_Τελική": payload.get("period_to"),
        "raw_code": payload.get("account_number")
        or payload.get("supply_number", {}).get("pretty"),
        "raw_label": payload.get("format"),
    }

    return row


def row_from_format_3_payload(payload: Dict, source_file: str) -> Dict:
    """
    Convert a format_3 payload to a simplified row with only requested fields.

    Args:
        payload: Parsed data dictionary from format_3 parser
        source_file: Source file path

    Returns:
        Dictionary with only the requested format_3 fields
    """
    row = {
        "Εκαθαριστικός": "ΝΑΙ" if payload.get("is_clearing") else "ΟΧΙ",
        "ΑρΠαροχής": payload.get("supply_number", {}).get("normalized")
        or to_digits(payload.get("supply_number", "")),
        "ΑρΛογαριασμού": payload.get("account_number"),
        "ΗμΈκδοσης": payload.get("issue_date"),
        "ΠερίοδοςΚατανάλωσης": f"{payload.get('period_from', '')}-{payload.get('period_to', '')}",
        "Συνολο_kWh_Καταναλωσης": payload.get("total_kwh_consumption"),
    }

    return row


def to_xlsx(payloads: List[Dict], source_files: List[str], out_path: str) -> str:
    """
    Export parsed payloads to XLSX file with standardized columns.

    Args:
        payloads: List of parsed data dictionaries
        source_files: List of corresponding source file paths
        out_path: Output file path for XLSX file

    Returns:
        Output file path

    Raises:
        ValueError: If payloads and source_files lists have different lengths
        Exception: If XLSX creation fails
    """
    if len(payloads) != len(source_files):
        raise ValueError("payloads and source_files lists must have the same length")

    # Build rows from payloads
    rows = []
    for payload, source_file in zip(payloads, source_files):
        row = row_from_payload(payload, source_file)
        rows.append(row)

    # Create DataFrame with exact column order
    df = pd.DataFrame(rows, columns=COLUMNS)

    # Write to XLSX
    try:
        df.to_excel(out_path, index=False, engine="openpyxl")
        return out_path
    except Exception as e:
        raise Exception(f"Failed to create XLSX file: {e}")


def to_format_3_xlsx(
    payloads: List[Dict], source_files: List[str], out_path: str
) -> str:
    """
    Export format_3 payloads to XLSX file with simplified columns.

    Args:
        payloads: List of format_3 parsed data dictionaries
        source_files: List of corresponding source file paths
        out_path: Output file path for XLSX file

    Returns:
        Output file path

    Raises:
        ValueError: If payloads and source_files lists have different lengths
        Exception: If XLSX creation fails
    """
    if len(payloads) != len(source_files):
        raise ValueError("payloads and source_files lists must have the same length")

    # Build rows from payloads using format_3 specific mapping
    rows = []
    for payload, source_file in zip(payloads, source_files):
        row = row_from_format_3_payload(payload, source_file)
        rows.append(row)

    # Create DataFrame with format_3 specific columns
    df = pd.DataFrame(rows, columns=FORMAT_3_COLUMNS)

    # Write to XLSX
    try:
        df.to_excel(out_path, index=False, engine="openpyxl")
        return out_path
    except Exception as e:
        raise Exception(f"Failed to create format_3 XLSX file: {e}")
