"""
Image validation utilities.
Handles image file validation and processing.
"""

import io
from typing import Set
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile

from backend.core.config import settings
from backend.core.exceptions import InvalidImageError, ValidationError
from backend.utils.logging.setup import logger

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file."""
    
    # Check content type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise ValidationError("Invalid file type. Please upload an image file.")
    
    # Check if MIME type is allowed
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        allowed = ", ".join(settings.ALLOWED_MIME_TYPES)
        raise ValidationError(f"Unsupported image type. Allowed types: {allowed}")
    
    # Check file extension
    if file.filename:
        file_ext = f".{file.filename.split('.')[-1].lower()}"
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise ValidationError(f"Unsupported file extension. Allowed extensions: {allowed}")


def validate_image_bytes(image_bytes: bytes) -> None:
    """Validate image bytes."""
    
    if len(image_bytes) == 0:
        raise ValidationError("Empty file uploaded")
    
    if len(image_bytes) > settings.MAX_FILE_SIZE:
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationError(f"File too large. Maximum size: {max_size_mb:.1f}MB")


def load_image(image_bytes: bytes) -> Image.Image:
    """Load image from bytes with validation."""
    try:
        validate_image_bytes(image_bytes)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB to ensure compatibility
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
        
    except UnidentifiedImageError:
        raise InvalidImageError("Invalid or corrupted image format")
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        raise InvalidImageError(f"Image processing error: {str(e)}")


def get_image_info(image: Image.Image) -> dict:
    """Get basic image information."""
    return {
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format,
        "size_bytes": len(image.tobytes()) if hasattr(image, 'tobytes') else None
    }


def resize_image(image: Image.Image, max_width: int = 2048, max_height: int = 2048) -> Image.Image:
    """Resize image if it exceeds maximum dimensions."""
    if image.width <= max_width and image.height <= max_height:
        return image
    
    # Calculate new dimensions maintaining aspect ratio
    ratio = min(max_width / image.width, max_height / image.height)
    new_width = int(image.width * ratio)
    new_height = int(image.height * ratio)
    
    logger.info(f"Resizing image from {image.width}x{image.height} to {new_width}x{new_height}")
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
