"""
OCR job management schemas.
These handle job submission, status tracking, and job listing for OCR operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Union
from .ocr_responses import OcrJobResult


class OcrJobSubmissionResponse(BaseModel):
    """Response model for OCR job submission"""
    success: bool = Field(..., description="Whether the job submission was successful")
    job_id: str = Field(..., description="Unique identifier for the submitted job")
    message: str = Field(..., description="Response message")


class OcrJobStatusResponse(BaseModel):
    """Response model for OCR job status queries"""
    success: bool = Field(..., description="Whether the job status retrieval was successful")
    status: str = Field(..., description="Current status of the job (pending, processing, completed, error)")
    message: str = Field(..., description="Response message")
    progress: Optional[int] = Field(None, description="Progress percentage of the job (0-100)")
    result: Union[OcrJobResult, None] = Field(None, description="Result of the OCR job if completed")


class OcrJobListResponse(BaseModel):
    """Response model for listing all OCR jobs"""
    success: bool = Field(..., description="Whether the operation was successful")
    jobs: List[dict] = Field(..., description="List of all OCR jobs with their statuses and errors")
