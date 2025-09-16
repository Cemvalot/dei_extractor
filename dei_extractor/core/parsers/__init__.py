"""
DEI PDF parsers package.

This package contains format-specific parsers for different DEI PDF layouts.
"""

from .format_3 import detect, parse

__all__ = ["detect", "parse"]
