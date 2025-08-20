#!/usr/bin/env python3
"""
Logging utilities for DEI Extractor.

This module provides logging utilities including colored console output,
file rotation, and execution time logging.
"""

import logging
import logging.handlers
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

from .config import Config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console logging."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


def setup_logging(
    config: Optional[Config] = None,
    log_file: Optional[Path] = None,
    log_level: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup logging configuration with both console and file handlers.

    Args:
        config: Configuration object
        log_file: Path to log file
        log_level: Logging level
        enable_console: Enable console logging
        enable_file: Enable file logging
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    if config is None:
        config = Config()

    if log_file is None:
        log_file = config.log_file

    if log_level is None:
        log_level = config.log_level

    # Create logger
    logger = logging.getLogger("dei_extractor")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        console_formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if enable_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Suppress third-party library logs
    logging.getLogger("pdfplumber").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pdf2image").setLevel(logging.WARNING)

    return logger


def get_logger(name: str = "dei_extractor") -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def log_method_call(self, method_name: str, **kwargs: Any) -> None:
        """Log method call with parameters."""
        self.logger.debug(f"Calling {method_name} with kwargs: {kwargs}")

    def log_method_result(self, method_name: str, result: Any) -> None:
        """Log method result."""
        self.logger.debug(f"{method_name} returned: {result}")


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time

        # Get logger from the class if it's a method
        if args and hasattr(args[0], "logger"):
            logger = args[0].logger
        else:
            logger = logging.getLogger(func.__module__)

        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result

    return wrapper


def log_error(func: Callable) -> Callable:
    """Decorator to log function errors."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get logger from the class if it's a method
            if args and hasattr(args[0], "logger"):
                logger = args[0].logger
            else:
                logger = logging.getLogger(func.__module__)

            logger.error(f"Error in {func.__name__}: {e}")
            raise

    return wrapper
