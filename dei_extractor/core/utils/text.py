#!/usr/bin/env python3
"""
Text extraction and normalization utilities for DEI PDF processing.

This module provides text extraction functions using PyMuPDF and pdfminer.six,
along with text normalization and parsing utilities for Greek text processing.
"""

import re
from datetime import datetime
from typing import Optional

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text

    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False


def extract_text_pymupdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Extracted text as string

    Raises:
        ImportError: If PyMuPDF is not available
        Exception: If text extraction fails
    """
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF (fitz) is not available")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"PyMuPDF text extraction failed: {e}")


def extract_text_pdfminer(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using pdfminer.six.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Extracted text as string

    Raises:
        ImportError: If pdfminer.six is not available
        Exception: If text extraction fails
    """
    if not PDFMINER_AVAILABLE:
        raise ImportError("pdfminer.six is not available")

    try:
        from io import BytesIO

        text = pdfminer_extract_text(BytesIO(pdf_bytes))
        return text
    except Exception as e:
        raise Exception(f"pdfminer text extraction failed: {e}")


def extract_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes, trying PyMuPDF first, then pdfminer.six as fallback.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Extracted text as string

    Raises:
        Exception: If both extraction methods fail
    """
    # Try PyMuPDF first
    if PYMUPDF_AVAILABLE:
        try:
            return extract_text_pymupdf(pdf_bytes)
        except Exception:
            pass  # Fall through to pdfminer

    # Fallback to pdfminer
    if PDFMINER_AVAILABLE:
        try:
            return extract_text_pdfminer(pdf_bytes)
        except Exception:
            pass

    # If both fail, raise an error
    available_methods = []
    if PYMUPDF_AVAILABLE:
        available_methods.append("PyMuPDF")
    if PDFMINER_AVAILABLE:
        available_methods.append("pdfminer.six")

    if not available_methods:
        raise Exception("Neither PyMuPDF nor pdfminer.six is available")
    else:
        raise Exception(
            f"Text extraction failed with all available methods: {', '.join(available_methods)}"
        )


def normalize_text(s: str) -> str:
    """
    Normalize text by converting Windows newlines to Unix, collapsing multiple spaces,
    keeping Greek uppercase letters intact, and stripping trailing spaces per line.

    Args:
        s: Input text string

    Returns:
        Normalized text string
    """
    if not s:
        return ""

    # Convert Windows newlines to Unix
    text = s.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple spaces to single space
    text = re.sub(r" +", " ", text)

    # Strip trailing spaces per line
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    text = "\n".join(lines)

    return text.strip()


def to_number_eu(s: str) -> Optional[float]:
    """
    Convert European number format to float.
    Accepts strings like '9.854,00', '5285,6', '1.234' (comma decimal, dot thousands).

    Args:
        s: Input string with European number format

    Returns:
        Float value or None if parsing fails
    """
    if not s:
        return None

    # Remove spaces
    s = s.replace(" ", "")

    # Handle empty string
    if not s:
        return None

    try:
        # If there's a comma, treat it as decimal separator
        if "," in s:
            # Remove thousands separators (dots before comma)
            parts = s.split(",")
            if len(parts) == 2:
                integer_part = parts[0].replace(".", "")
                decimal_part = parts[1]
                return float(f"{integer_part}.{decimal_part}")
            else:
                # Multiple commas - treat as thousands separators
                return float(s.replace(",", ""))
        else:
            # No comma - treat dots as thousands separators
            return float(s.replace(".", ""))
    except (ValueError, IndexError):
        return None


def to_digits(s: str) -> str:
    """
    Extract only digits from a string.

    Args:
        s: Input string

    Returns:
        String containing only digits
    """
    if not s:
        return ""
    return re.sub(r"[^0-9]", "", str(s))


def parse_date_ddmmyyyy(s: str) -> Optional[str]:
    """
    Parse date string in DD/MM/YYYY or DD.MM.YYYY format to ISO YYYY-MM-DD.

    Args:
        s: Date string in DD/MM/YYYY or DD.MM.YYYY format

    Returns:
        ISO date string (YYYY-MM-DD) or None if parsing fails
    """
    if not s:
        return None

    s = s.strip()

    # Try DD/MM/YYYY format
    try:
        date_obj = datetime.strptime(s, "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try DD.MM.YYYY format
    try:
        date_obj = datetime.strptime(s, "%d.%m.%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        pass

    return None
