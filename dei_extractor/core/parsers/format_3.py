#!/usr/bin/env python3
"""
Format 3 parser for ΔΕΗ bills.

This parser handles the third layout format of DEI bills, detecting and extracting
structured data from PDF text using regex patterns and text normalization.
"""

import re
from typing import Any, Dict, Optional

from ..utils.text import (
    extract_text,
    normalize_text,
    parse_date_ddmmyyyy,
    to_digits,
    to_number_eu,
)


def detect(text: str) -> bool:
    """
    Detect if the text matches format 3 layout.

    Heuristics: any two of the following must match:
    - Presence of label 'ΑΡΙΘΜΟΣ ΠΑΡΟΧΗΣ'
    - Presence of 'ΗΜΕΡΟΜΗΝΙΑ ΕΚΔΟΣΗΣ'
    - Presence of 'ΠΕΡΙΟΔΟΣ ΚΑΤΑΝΑΛΩΣΗΣ'
    - Presence of 'A/A ΛΟΓΑΡΙΑΣΜΟΥ' or 'Α/Α ΛΟΓΑΡΙΑΣΜΟΥ'

    Args:
        text: Normalized text from PDF

    Returns:
        True if format 3 is detected, False otherwise
    """
    if not text:
        return False

    # Normalize text for detection
    normalized = normalize_text(text)

    # Detection patterns
    patterns = [
        r"ΑΡΙΘΜΟΣ\s+ΠΑΡΟΧΗΣ",
        r"ΗΜΕΡΟΜΗΝΙΑ\s+ΕΚΔΟΣΗΣ",
        r"ΠΕΡΙΟΔΟΣ\s+ΚΑΤΑΝΑΛΩΣΗΣ",
        r"A/?A\s+ΛΟΓΑΡΙΑΣΜΟΥ",
    ]

    matches = 0
    for pattern in patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            matches += 1

    # Return True if at least 2 patterns match
    return matches >= 2


def _gx(text: str, pattern: str) -> Optional[re.Match]:
    """Helper function for regex search with IGNORECASE flag."""
    return re.search(pattern, text, re.IGNORECASE)


def parse(pdf_bytes: bytes, source_file: Optional[str] = None) -> Dict:
    """
    Parse format 3 PDF and extract structured data.

    Args:
        pdf_bytes: PDF file content as bytes
        source_file: Optional source file path for tracking

    Returns:
        Dictionary with extracted data fields
    """
    # Extract and normalize text
    raw_text = extract_text(pdf_bytes)
    text = normalize_text(raw_text)

    # Initialize result dictionary
    out: Dict[str, Any] = {"format": "format_3"}

    # --- ΑΡΙΘΜΟΣ ΠΑΡΟΧΗΣ (robust across newlines, spaces, hyphens)
    # Ψάχνουμε για το δεύτερο "ΑΡΙΘΜΟΣ ΠΑΡΟΧΗΣ" που έχει τον αριθμό
    supply_matches = re.findall(
        r"ΑΡΙΘΜΟΣ\s+ΠΑΡΟΧΗΣ\s+([0-9][0-9\-\s]+)", text, re.IGNORECASE
    )
    if supply_matches:
        # Πάρε τον τελευταίο match (που είναι ο σωστός)
        pretty = re.sub(r"\s+", " ", supply_matches[-1]).strip()
        out["supply_number"] = {"pretty": pretty, "normalized": to_digits(pretty)}

    # --- Extract table data with complex regex
    table_match = re.search(
        r"A/A.*?ΛΟΓΑΡΙΑΣΜΟΥ.*?ΗΜΕΡΟΜΗΝΙΑ.*?ΕΚΔΟΣΗΣ.*?ΠΕΡΙΟΔΟΣ.*?ΚΑΤΑΝΑΛΩΣΗΣ.*?ΗΜΕΡΕΣ.*?ΣΤΟΙΧΕΙΑ.*?ΠΕΛΑΤΗ.*?ΑΡΙΘΜΟΣ.*?ΠΑΡΟΧΗΣ.*?(\d+).*?(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4}).*?(\d+).*?(\d+\s+\d+\s+\d+\s+\d+).*?(\d+\s+\d+\s+\d+\s+-\s+\d+\s+\d+)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if table_match:
        # A/A ΛΟΓΑΡΙΑΣΜΟΥ
        out["account_number"] = table_match.group(1).strip()

        # ΗΜΕΡΟΜΗΝΙΑ ΕΚΔΟΣΗΣ
        out["issue_date"] = parse_date_ddmmyyyy(table_match.group(2))

        # ΠΕΡΙΟΔΟΣ ΚΑΤΑΝΑΛΩΣΗΣ
        out["period_from"] = parse_date_ddmmyyyy(table_match.group(3))
        out["period_to"] = parse_date_ddmmyyyy(table_match.group(4))

    # --- ΟΝΟΜ/ΜΟ - Δ/ΝΣΗ ΕΠΙΔΟΣΗΣ (πάρ' τα επόμενα 1-3 non-empty lines)
    m = _gx(text, r"ΟΝΟΜ/ΜΟ\s*-\s*Δ/ΝΣΗ\s+ΕΠΙΔΟΣΗΣ\s*\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)")
    if m:
        out["recipient_name"] = m.group(1).strip()
        out["recipient_address_line1"] = m.group(2).strip()
        out["recipient_postcode_city"] = m.group(3).strip()
        # derive city (π.χ. "17235 ΔΑΦΝΗ" -> "ΔΑΦΝΗ")
        parts = out["recipient_postcode_city"].split()
        if len(parts) >= 2:
            out["city"] = " ".join(parts[1:])

    # --- kWh: Σύνολο Κατανάλωσης Ενεργών (kWh)  ❗ ΑΥΤΟ είναι το total
    # Pattern για "11.103,52 Ενεργών (kWh)" - το σύνολο κατανάλωσης
    m = _gx(text, r"([0-9\.\,]+)\s*Ενεργ\w*\s*\(kWh\)")
    if m:
        out["kwh_total"] = to_number_eu(m.group(1))
        out["total_kwh_consumption"] = to_number_eu(
            m.group(1)
        )  # Same value for simplified export

    # --- Προαιρετικά: Ημέρας / Νύκτας (αν βρεθούν)
    m = _gx(text, r"Απορροφ\w+\s+Ημέρας\s*[:\-]?\s*([0-9\.\,]+)")
    if m:
        out["kwh_day"] = to_number_eu(m.group(1))

    m = _gx(text, r"Απορροφ\w+\s+Νύκτας\s*[:\-]?\s*([0-9\.\,]+)")
    if m:
        out["kwh_night"] = to_number_eu(m.group(1))

    # --- Κατηγορία / Υποκατηγορία (αν υπάρχουν στο κείμενο)
    m = _gx(text, r"Κατηγορία\s*Τιμολογίου[:\s]+([A-Z0-9\.\- ]+)")
    if m:
        out["tariff_category"] = m.group(1).strip()

    m = _gx(text, r"Υποκατηγορία[:\s]+([A-Z0-9\.\- ]+)")
    if m:
        out["tariff_subcategory"] = m.group(1).strip()

    # --- Εκκαθαριστικός
    out["is_clearing"] = bool(_gx(text, r"\bΕΚΚΑΘΑΡΙΣΤΙΚΟΣ\b"))

    # --- Fallback patterns for total kWh consumption if not found above
    if not out.get("kwh_total"):
        total_consumption_patterns = [
            r"ΣΥΝΟΛΟ\s+ΚΑΤΑΝΑΛΩΣΗΣ[:\s]+([0-9\.\,]+)\s*kWh",
            r"ΣΥΝΟΛΟ\s+ΚΑΤΑΝΑΛΩΣΗΣ[:\s]+([0-9\.\,]+)",
            r"ΚΑΤΑΝΑΛΩΣΗ[:\s]+([0-9\.\,]+)\s*kWh",
            r"ΣΥΝΟΛΟ[:\s]+([0-9\.\,]+)\s*kWh",
            r"kWh[:\s]+([0-9\.\,]+)",
            r"([0-9\.\,]+)\s*kWh",
        ]

        for pattern in total_consumption_patterns:
            match = _gx(text, pattern)
            if match:
                out["total_kwh_consumption"] = to_number_eu(match.group(1))
                break

    return out
