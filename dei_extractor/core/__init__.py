"""
Core functionality for DEI Extractor.

This module contains the main business logic for PDF extraction and data filtering.
"""

from .extractor import DEIExtractorEnhanced
from .filter import FilterEkatharistikos

__all__ = ["DEIExtractorEnhanced", "FilterEkatharistikos"]
