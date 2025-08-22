"""Pydantic models for request validation."""

from typing import Optional

from pydantic import BaseModel, Field


class ProcessingOptions(BaseModel):
    """Options for PDF processing."""

    apply_filter: bool = Field(
        default=False, description="Apply Εκαθαριστικός filtering to extracted data"
    )
    verbose: bool = Field(default=False, description="Enable verbose logging")
    language: str = Field(default="en", description="UI language (en or gr)")


class JobRequest(BaseModel):
    """Request model for job processing."""

    options: ProcessingOptions = Field(
        default_factory=ProcessingOptions, description="Processing options"
    )
