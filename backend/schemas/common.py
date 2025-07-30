"""
Common response models used across different services.
These provide standardized response formats for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ApiErrorResponse(BaseModel):
    """Standard error response model for all API endpoints"""
    success: bool = Field(False, description="Always false for error responses")
    message: str = Field(..., description="Human-readable error message")
    error_detail: Optional[str] = Field(None, description="Detailed technical error information")
