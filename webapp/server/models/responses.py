"""Pydantic models for response validation."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok", description="Service status")
    version: str = Field(description="Service version")
    ocr_available: bool = Field(description="Whether OCR is available")


class JobStatus(BaseModel):
    """Job processing status."""

    success: bool = Field(description="Whether processing was successful")
    message: str = Field(description="Status message")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    output_files: List[str] = Field(
        default_factory=list, description="Generated output files"
    )
    output_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Output summary"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error message")
    details: Optional[str] = Field(default=None, description="Error details")
