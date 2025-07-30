"""
Form parsing service schemas.
These handle form parsing operations, job management, and results.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union


class FormParsingResult(BaseModel):
    """Result model for form parsing operations"""
    success: bool = Field(..., description="Whether parsing was successful")
    metadata: Dict[str, Any] = Field(..., description="Image metadata")
    filename: str = Field(..., description="Filename of the image")
    execution_time: float = Field(..., description="Time taken to parse in seconds")
    data: Union[dict, None, Any] = Field(..., description="Parsed form data (JSON object)")


class FormParsingJobSubmissionResponse(BaseModel):
    """Response model for form parsing job submission"""
    success: bool = Field(..., description="Whether the job submission was successful")
    job_id: str = Field(..., description="Unique identifier for the submitted job")
    message: str = Field(..., description="Response message")


class FormParsingJobStatusResponse(BaseModel):
    """Response model for form parsing job status queries"""
    success: bool = Field(..., description="Whether the job status retrieval was successful")
    status: str = Field(..., description="Current status of the job (pending, processing, completed, error)")
    message: str = Field(..., description="Response message")
    result: Union[FormParsingResult, None] = Field(
        None,
        description="Result of the form parsing job if completed (contains parsed form data and metadata)"
    )
