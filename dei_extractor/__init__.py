"""
DEI Extractor Package

A comprehensive Python package for extracting and processing DEI
(Public Power Corporation) PDF invoice data with advanced parsing,
filtering, and data validation capabilities.

Author: DEI Extractor Team
Version: 3.0.0
License: MIT
"""

__version__ = "3.0.0"
__author__ = "DEI Extractor Team"
__email__ = "team@dei-extractor.com"

from .core.extractor import DEIExtractorEnhanced
from .core.filter import FilterEkatharistikos
from .utils.config import Config
from .utils.logger import setup_logging

__all__ = [
    "DEIExtractorEnhanced",
    "FilterEkatharistikos",
    "Config",
    "setup_logging",
    "__version__",
    "__author__",
    "__email__",
]
