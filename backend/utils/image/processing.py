"""
Image processing utilities.
Handles image manipulation and processing operations.
"""

import io
from typing import Dict, Tuple
from PIL import Image

from backend.utils.logging.setup import logger


def crop_image(image_bytes: bytes, bbox: Dict[str, int]) -> bytes:
    """Crop image using bounding box coordinates."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Extract coordinates
        x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
        
        # Validate coordinates
        if x1 >= x2 or y1 >= y2:
            raise ValueError("Invalid bounding box coordinates")
        
        if x1 < 0 or y1 < 0 or x2 > image.width or y2 > image.height:
            raise ValueError("Bounding box coordinates out of image bounds")
        
        # Crop image
        cropped_image = image.crop((x1, y1, x2, y2))
        
        # Save to bytes
        output_buffer = io.BytesIO()
        cropped_image.save(output_buffer, format='PNG')
        return output_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Failed to crop image: {e}")
        raise


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Convert PIL Image to bytes."""
    output_buffer = io.BytesIO()
    image.save(output_buffer, format=format)
    return output_buffer.getvalue()


def enhance_image_for_ocr(image: Image.Image) -> Image.Image:
    """Apply image enhancements for better OCR results."""
    try:
        # Convert to grayscale for better OCR
        if image.mode != "L":
            image = image.convert("L")
        
        # Apply contrast enhancement if needed
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)  # Slightly increase contrast
        
        return image
        
    except Exception as e:
        logger.warning(f"Failed to enhance image: {e}")
        return image  # Return original if enhancement fails


def calculate_image_hash(image: Image.Image) -> str:
    """Calculate a hash for image deduplication."""
    import hashlib
    
    # Convert image to bytes for hashing
    image_bytes = image_to_bytes(image)
    return hashlib.md5(image_bytes).hexdigest()


def get_dominant_colors(image: Image.Image, num_colors: int = 3) -> list:
    """Get dominant colors in the image."""
    try:
        # Resize image for faster processing
        small_image = image.resize((50, 50))
        
        # Get colors
        colors = small_image.getcolors(maxcolors=256*256*256)
        if colors:
            # Sort by frequency and get top colors
            colors.sort(key=lambda x: x[0], reverse=True)
            return [color[1] for color in colors[:num_colors]]
        
        return []
        
    except Exception as e:
        logger.warning(f"Failed to get dominant colors: {e}")
        return []