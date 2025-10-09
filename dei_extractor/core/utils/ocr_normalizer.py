#!/usr/bin/env python3
"""
OCR Text Normalization utilities for DEI Extractor.

This module provides functions to clean and normalize OCR-extracted text
to improve pattern matching for DEI invoices.
"""

import re
import unicodedata


def normalize_greek_text(text: str) -> str:
    """
    Normalize Greek OCR text by removing accents and fixing common OCR errors.

    Args:
        text: Raw OCR text

    Returns:
        Normalized text suitable for pattern matching
    """
    if not text:
        return text

    # Remove accents and diacritics from Greek characters
    # NFD = decompose characters, then filter out combining marks
    nfd_text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in nfd_text if unicodedata.category(char) != "Mn")

    # Normalize to NFC (composed form)
    text = unicodedata.normalize("NFC", text)

    # Common OCR errors in Greek text
    ocr_fixes = {
        "Ἠ": "Η",  # Eta with dasia
        "ἠ": "η",
        "Ἀ": "Α",  # Alpha with dasia
        "ἀ": "α",
        "Ὀ": "Ο",  # Omicron with dasia
        "ὀ": "ο",
        "ῆ": "η",
        "ῇ": "η",
        "ά": "α",
        "έ": "ε",
        "ή": "η",
        "ί": "ι",
        "ό": "ο",
        "ύ": "υ",
        "ώ": "ω",
        "Ά": "Α",
        "Έ": "Ε",
        "Ή": "Η",
        "Ί": "Ι",
        "Ό": "Ο",
        "Ύ": "Υ",
        "Ώ": "Ω",
        # Common misrecognized characters
        "2QXB": "ΣΩΧΒ",
        "Luv": "Συν",
        ".QXB": "ΩΧΒ",
        "Ἡμ": "Ημ",
        "Ἠκδοσης": "Εκδοσης",
        "Ἐκδοσης": "Εκδοσης",
    }

    for old, new in ocr_fixes.items():
        text = text.replace(old, new)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text


def fix_common_ocr_errors(text: str) -> str:
    """
    Fix common OCR errors specific to DEI invoices.

    Args:
        text: OCR text with potential errors

    Returns:
        Text with common errors fixed
    """
    if not text:
        return text

    # Fix date formats - dates without slashes
    # Pattern: Find sequences of digits that look like dates
    def fix_corrupted_dates(text):
        """Fix dates that appear without slashes in OCR output."""

        # Find potential date sequences: 10-digit sequences that look like 1ddmmyyyy
        # Example: 19760272019 -> 19/06/2019
        def fix_10digit_date(match):
            digits = match.group(0)
            if len(digits) == 10:
                # Try to extract ddmmyyyy from position 1-8
                return f"{digits[1:3]}/{digits[3:5]}/{digits[5:9]}"
            return digits

        # Replace 10-digit sequences between account number and period
        text = re.sub(r"\d{10}(?=\s+\d{2}[-\.]\d{2})", fix_10digit_date, text)

        # Fix 8-digit dates (ddmmyyyy)
        def fix_8digit_date(match):
            digits = match.group(0)
            return f"{digits[0:2]}/{digits[2:4]}/{digits[4:8]}"

        # Replace 8-digit sequences between account number and period (if not already fixed)
        text = re.sub(r"(?<=\d{12}\s)\d{8}(?=\s+\d{2}[-\.])", fix_8digit_date, text)

        return text

    text = fix_corrupted_dates(text)

    # Fix mixed period formats: 15-12-2018 -> 15.12.2018
    def normalize_period_dates(match):
        period = match.group(0)
        # Replace - with . in dates
        period = re.sub(r"(\d{2})-(\d{2})-(\d{4})", r"\1.\2.\3", period)
        return period

    text = re.sub(
        r"\d{2}[-\.]\d{2}[-\.]\d{4}\s*-\s*\d{2}[-\.]\d{2}[-\.]\d{4}",
        normalize_period_dates,
        text,
    )

    # Fix common numeric/letter confusions
    fixes = [
        # 0 vs O
        (r"\b0(?=[A-ZΑ-Ω])", "Ο"),  # 0 before letter -> O
        (r"(?<=[A-ZΑ-Ω])0\b", "Ο"),  # 0 after letter -> O
        # 1 vs I
        (r"(?<=[A-ZΑ-Ω])1(?=[A-ZΑ-Ω])", "Ι"),  # 1 between letters -> I
        # Common Greek word fixes
        (r"Ἡμ\.?\s*Ἠκδοσης", "Ημ. Εκδοσης"),
        (r"Αρ\.?\s*Παροχῆς", "Αρ.Παροχης"),
        (r"Αρ\.?\s*Λογαρ\.?", "Αρ.Λογαρ."),
        (r"Περίοδος\s+Κατανάλώσης", "Περιοδος Καταναλωσης"),
        (r"πιµολόγιο", "Τιμολογιο"),
        (r"NHpony", "Προηγ."),
        (r"πελευτ\.?", "Τελευτ."),
        (r"Ημερα", "Ημέρα"),
    ]

    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def preprocess_ocr_lines(lines: list[str]) -> list[str]:
    """
    Preprocess OCR lines for better pattern matching.

    Args:
        lines: List of OCR text lines

    Returns:
        Cleaned and normalized lines
    """
    processed_lines = []

    for line in lines:
        # Normalize Greek text
        line = normalize_greek_text(line)

        # Fix common OCR errors
        line = fix_common_ocr_errors(line)

        # Skip empty lines
        if line.strip():
            processed_lines.append(line)

    return processed_lines
