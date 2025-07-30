"""
Schema module exports for the OCR application.
All Pydantic models are organized by their functional domains.
"""

# Core data models
from .core import BoundingBox, DetectedTextRegion, ExtractedText

# Common response models
from .common import ApiErrorResponse

# OCR service responses
from .ocr_responses import TextDetectionResponse, TrOcrExtractionResponse, OcrJobResult

# OCR job management
from .ocr_jobs import OcrJobSubmissionResponse, OcrJobStatusResponse, OcrJobListResponse

# Form parsing service
from .form_parsing import (
    FormParsingResult,
    FormParsingJobSubmissionResponse,
    FormParsingJobStatusResponse
)

__all__ = [
    # Core data models
    "BoundingBox",
    "DetectedTextRegion", 
    "ExtractedText",
    
    # Common response models
    "ApiErrorResponse",
    
    # OCR service responses
    "TextDetectionResponse",
    "TrOcrExtractionResponse",
    "OcrJobResult",
    
    # OCR job management
    "OcrJobSubmissionResponse",
    "OcrJobStatusResponse", 
    "OcrJobListResponse",
    
    # Form parsing service
    "FormParsingResult",
    "FormParsingJobSubmissionResponse",
    "FormParsingJobStatusResponse",
]
