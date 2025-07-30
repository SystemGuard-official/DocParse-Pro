"""
OCR service response models.
These handle responses from various OCR processing endpoints.
"""

from pydantic import BaseModel, Field
from typing import List
from .core import DetectedTextRegion, ExtractedText


class TextDetectionResponse(BaseModel):
    """Response model for text detection endpoints"""
    success: bool = Field(..., description="Whether the operation was successful")
    metadata: dict = Field(..., description="Metadata information about the input image")
    execution_time: float = Field(..., description="Time taken for processing in seconds")
    message: str = Field(..., description="Response message")
    detections: List[DetectedTextRegion] = Field(..., description="List of detected text regions")
    total_detections: int = Field(..., description="Total number of detections")


class TrOcrExtractionResponse(BaseModel):
    """Response model for TrOCR text extraction endpoints"""
    success: bool = Field(..., description="Whether the OCR operation was successful")
    message: str = Field(..., description="Response message")
    model: str = Field(..., description="OCR model used for processing")
    filename: str = Field(..., description="Name of the uploaded file")
    file_size_kb: float = Field(..., description="Size of the file in kilobytes")
    execution_time: float = Field(..., description="Time taken to process the image in seconds")
    extracted_text: str = Field(..., description="Extracted text from the image")


class OcrJobResult(BaseModel):
    """Complete OCR job result with full text extraction"""
    success: bool = Field(..., description="Whether the operation was successful")
    filename: str = Field(..., description="Name of the uploaded file")
    metadata: dict = Field(..., description="Metadata information about the input image")
    text_detection_duration: float = Field(..., description="Time taken for text detection in seconds")
    overall_processing_time: float = Field(..., description="Total time taken for processing in seconds")
    message: str = Field(..., description="Response message")
    detections: List[ExtractedText] = Field(..., description="List of extracted text regions")
    total_detections: int = Field(..., description="Total number of detections")
