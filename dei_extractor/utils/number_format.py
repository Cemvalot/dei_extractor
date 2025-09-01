from __future__ import annotations

import re
from typing import Union

import numpy as np
import pandas as pd

_DECIMAL_LIKE_RE = re.compile(
    r"^\s*[-+]?(\d{1,3}(\.\d{3})+|\d+)([.,]\d+)?\s*$|^\s*[-+]?\d+\.\d+\s*$|^\s*[-+]?\d{1,3}(\.\d{3})*\s*$"
)


def _to_number_series(s: pd.Series) -> pd.Series:
    """
    Convert a potentially string-formatted numeric series (Greek style, commas) to float.
    Rules:
      - If value contains comma as decimal separator, remove thousands dots and replace comma with dot.
      - If value contains only dot as decimal, parse normally.
      - Non-parsable values remain as-is.
    """
    if s.dtype.kind in "biufc":  # already numeric
        return s.astype(float)

    def _coerce(x):
        if x is None:
            return x
        xs = str(x).strip()
        if xs == "" or xs.lower() == "nan":
            return np.nan

        # Check for Greek format first (before regex)
        if "," in xs:
            # Greek format with comma: 1.234,56 -> 1234.56
            xs = xs.replace(".", "")
            xs = xs.replace(",", ".")
            try:
                return float(xs)
            except Exception:
                return x
        elif "." in xs and len(xs.split(".")) >= 2:
            # Check if it looks like Greek thousands separator (groups of 3 digits)
            parts = xs.split(".")
            # Only treat as Greek if all parts are 3 digits or less AND no part has more than 3 digits
            if (
                len(parts) > 1
                and all(len(part) <= 3 for part in parts)
                and not any(len(part) > 3 for part in parts)
                and
                # Additional check: if last part is 2 digits, it's likely decimal, not thousands
                len(parts[-1]) != 2
            ):
                xs = xs.replace(".", "")
                try:
                    return float(xs)
                except Exception:
                    return x

        # Check for standard decimal format
        if not _DECIMAL_LIKE_RE.match(xs):
            return x  # leave as-is if clearly non-numeric text

        # Standard decimal format
        try:
            return float(xs)
        except Exception:
            return x

    # Apply coercion and preserve original values for non-numeric
    result = s.map(_coerce)

    # Only convert to numeric if most values are actually numeric
    numeric_count = sum(
        1 for x in result if isinstance(x, (int, float)) and not pd.isna(x)
    )
    if numeric_count > len(result) * 0.5:  # More than 50% are numeric
        # Convert only the numeric values, preserve others
        numeric_result = pd.to_numeric(result, errors="coerce")
        # Restore original non-numeric values
        for i, orig_val in enumerate(result):
            if not isinstance(orig_val, (int, float)) or pd.isna(orig_val):
                numeric_result.iloc[i] = orig_val
        return numeric_result
    else:
        return result


def enforce_two_decimals(df: pd.DataFrame, mode: str = "round") -> pd.DataFrame:
    """
    Convert numeric-like columns to float and enforce 2 decimal places.
    Only format numbers that already have decimal places - don't add .00 to whole numbers.

    Args:
        df: DataFrame to process
        mode: "round" (default) or "truncate"
            - round: pandas round(2)
            - truncate: cut off beyond 2 decimals (e.g., 10.319 -> 10.31)

    Returns:
        DataFrame with numeric columns formatted appropriately
    """
    # convert object-like columns that are numeric strings into floats
    for col in df.columns:
        df[col] = _to_number_series(df[col])

    # find numeric columns
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not num_cols:
        return df

    # Process each numeric column
    for col in num_cols:
        series = df[col].astype(float)

        # Check if the original values had decimal places
        original_has_decimals = []
        for val in df[col]:
            if pd.isna(val):
                original_has_decimals.append(False)
            else:
                # Check if the original string representation had decimal places
                str_val = str(val)
                original_has_decimals.append("." in str_val or "," in str_val)

        # Only format to 2 decimals if the original had decimal places
        for i, (val, had_decimals) in enumerate(zip(series, original_has_decimals)):
            if pd.isna(val):
                continue
            if had_decimals:
                if mode == "truncate":
                    df.loc[df.index[i], col] = np.trunc(val * 100) / 100
                else:
                    df.loc[df.index[i], col] = round(val, 2)
            # If no decimals in original, keep as integer (no .00)

    return df


def to_excel_2decimals(
    df: pd.DataFrame, path: str, sheet_name: str = "Sheet1", **excel_writer_kwargs
) -> None:
    """
    Write Excel with numeric columns displayed as 0.00 in the file.

    Args:
        df: DataFrame to export
        path: Output file path
        sheet_name: Sheet name (default: "Sheet1")
        **excel_writer_kwargs: Additional arguments for pd.ExcelWriter
    """
    with pd.ExcelWriter(path, engine="xlsxwriter", **excel_writer_kwargs) as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        wb = writer.book
        ws = writer.sheets[sheet_name]
        numfmt = wb.add_format({"num_format": "0.00"})
        for idx, col in enumerate(df.columns):
            if pd.api.types.is_numeric_dtype(df[col]):
                # apply number format to the whole numeric column
                ws.set_column(idx, idx, None, numfmt)
