#!/usr/bin/env python3
"""
Validation utilities for DEI Extractor.

This module provides validation functions for various data types and formats
used in the DEI extraction process.
"""

import csv
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        """Initialize validation error."""
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_pdf_file(file_path: Union[str, Path]) -> bool:
    """Validate that a file is a valid PDF."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValidationError(f"File is not a PDF: {file_path}")

    # Check file size (max 50MB)
    if file_path.stat().st_size > 50 * 1024 * 1024:
        raise ValidationError(f"File too large: {file_path}")

    # Check if file is readable
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            if header != b"%PDF":
                raise ValidationError(f"Invalid PDF header: {file_path}")
    except Exception as e:
        raise ValidationError(f"Cannot read PDF file: {file_path} - {e}")

    return True


def validate_csv_file(file_path: Union[str, Path]) -> bool:
    """Validate that a file is a valid CSV."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    if file_path.suffix.lower() != ".csv":
        raise ValidationError(f"File is not a CSV: {file_path}")

    # Check if file is readable and contains valid CSV data
    try:
        df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows to validate
        if df.empty:
            raise ValidationError(f"CSV file is empty: {file_path}")
    except Exception as e:
        raise ValidationError(f"Cannot read CSV file: {file_path} - {e}")

    return True


def validate_excel_file(file_path: Union[str, Path]) -> bool:
    """Validate that a file is a valid Excel file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    if file_path.suffix.lower() not in [".xlsx", ".xls"]:
        raise ValidationError(f"File is not an Excel file: {file_path}")

    # Check if file is readable and contains valid Excel data
    try:
        df = pd.read_excel(file_path, nrows=5)  # Read first 5 rows to validate
        if df.empty:
            raise ValidationError(f"Excel file is empty: {file_path}")
    except Exception as e:
        raise ValidationError(f"Cannot read Excel file: {file_path} - {e}")

    return True


def validate_dataframe(
    df: pd.DataFrame, required_columns: Optional[List[str]] = None
) -> bool:
    """Validate DataFrame structure and content."""
    if df is None:
        raise ValidationError("DataFrame is None")

    if df.empty:
        raise ValidationError("DataFrame is empty")

    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"Missing required columns: {missing_columns}")

    return True


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration dictionary."""
    required_keys = ["log_level", "output_dir"]

    for key in required_keys:
        if key not in config:
            raise ValidationError(f"Missing required config key: {key}")

    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.get("log_level", "").upper() not in valid_log_levels:
        raise ValidationError(f"Invalid log level: {config.get('log_level')}")

    # Validate output directory
    output_dir = config.get("output_dir")
    if output_dir:
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValidationError(f"Cannot create output directory: {e}")

    return True


def validate_file_path(file_path: Union[str, Path], must_exist: bool = True) -> bool:
    """Validate file path."""
    file_path = Path(file_path)

    if must_exist and not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    if file_path.exists() and not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    return True


def validate_directory_path(
    dir_path: Union[str, Path], must_exist: bool = True
) -> bool:
    """Validate directory path."""
    dir_path = Path(dir_path)

    if must_exist and not dir_path.exists():
        raise ValidationError(f"Directory does not exist: {dir_path}")

    if dir_path.exists() and not dir_path.is_dir():
        raise ValidationError(f"Path is not a directory: {dir_path}")

    return True
