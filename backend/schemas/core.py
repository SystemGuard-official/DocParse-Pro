"""
Core data models for the OCR application.
These are the fundamental building blocks used across different services.
"""

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for text regions"""
    x1: int = Field(..., description="Left X coordinate")
    y1: int = Field(..., description="Top Y coordinate")
    x2: int = Field(..., description="Right X coordinate")
    y2: int = Field(..., description="Bottom Y coordinate")


class DetectedTextRegion(BaseModel):
    """Text detection result with bounding box dimensions"""
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")
    width: int = Field(..., description="Width of the bounding box")
    height: int = Field(..., description="Height of the bounding box")


class ExtractedText(BaseModel):
    """Text extraction result with bounding box and text content"""
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")
    width: int = Field(..., description="Width of the bounding box")
    height: int = Field(..., description="Height of the bounding box")
    text: str = Field(..., description="Detected text content")
