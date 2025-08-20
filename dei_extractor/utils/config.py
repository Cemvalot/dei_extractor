#!/usr/bin/env python3
"""
Configuration management for DEI Extractor.

This module provides configuration management functionality for the DEI Extractor,
including loading configuration from files and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Configuration class for DEI Extractor."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize configuration with default values or provided kwargs."""
        # Default configuration values
        self.log_level = kwargs.get("log_level", "INFO")
        self.log_file = Path(kwargs.get("log_file", "logs/dei_extractor.log"))
        self.output_dir = Path(kwargs.get("output_dir", "output"))
        self.temp_dir = Path(kwargs.get("temp_dir", "temp"))
        self.max_file_size = kwargs.get("max_file_size", 10 * 1024 * 1024)  # 10MB
        self.backup_count = kwargs.get("backup_count", 5)
        self.encoding = kwargs.get("encoding", "utf-8")
        self.confidence_threshold = kwargs.get("confidence_threshold", 0.9)
        self.enable_ocr = kwargs.get("enable_ocr", True)
        self.ocr_language = kwargs.get("ocr_language", "ell")
        self.tesseract_config = kwargs.get("tesseract_config", "--psm 6")
        self.max_workers = kwargs.get("max_workers", 4)
        self.chunk_size = kwargs.get("chunk_size", 1000)
        self.timeout = kwargs.get("timeout", 300)  # 5 minutes
        self.retry_attempts = kwargs.get("retry_attempts", 3)
        self.retry_delay = kwargs.get("retry_delay", 1)  # 1 second

        # Override with environment variables if present
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "DEI_LOG_LEVEL": "log_level",
            "DEI_LOG_FILE": "log_file",
            "DEI_OUTPUT_DIR": "output_dir",
            "DEI_TEMP_DIR": "temp_dir",
            "DEI_MAX_FILE_SIZE": "max_file_size",
            "DEI_BACKUP_COUNT": "backup_count",
            "DEI_ENCODING": "encoding",
            "DEI_CONFIDENCE_THRESHOLD": "confidence_threshold",
            "DEI_ENABLE_OCR": "enable_ocr",
            "DEI_OCR_LANGUAGE": "ocr_language",
            "DEI_TESSERACT_CONFIG": "tesseract_config",
            "DEI_MAX_WORKERS": "max_workers",
            "DEI_CHUNK_SIZE": "chunk_size",
            "DEI_TIMEOUT": "timeout",
            "DEI_RETRY_ATTEMPTS": "retry_attempts",
            "DEI_RETRY_DELAY": "retry_delay",
        }

        for env_var, attr_name in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                if attr_name in [
                    "max_file_size",
                    "backup_count",
                    "max_workers",
                    "chunk_size",
                    "timeout",
                    "retry_attempts",
                    "retry_delay",
                ]:
                    setattr(self, attr_name, int(value))
                elif attr_name in ["confidence_threshold"]:
                    setattr(self, attr_name, float(value))
                elif attr_name in ["enable_ocr"]:
                    setattr(self, attr_name, value.lower() in ("true", "1", "yes"))
                elif attr_name in ["log_file", "output_dir", "temp_dir"]:
                    setattr(self, attr_name, Path(value))
                else:
                    setattr(self, attr_name, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "log_level": self.log_level,
            "log_file": str(self.log_file),
            "output_dir": str(self.output_dir),
            "temp_dir": str(self.temp_dir),
            "max_file_size": self.max_file_size,
            "backup_count": self.backup_count,
            "encoding": self.encoding,
            "confidence_threshold": self.confidence_threshold,
            "enable_ocr": self.enable_ocr,
            "ocr_language": self.ocr_language,
            "tesseract_config": self.tesseract_config,
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
        }

    def save(self, file_path: Path) -> None:
        """Save configuration to YAML file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def load(cls, file_path: Path) -> "Config":
        """Load configuration from YAML file."""
        if not file_path.exists():
            return cls()

        with open(file_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        return cls(**config_data)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or return default configuration."""
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            config = Config.load(config_file)
            return config.to_dict()

    # Return default configuration
    config = Config()
    return config.to_dict()
