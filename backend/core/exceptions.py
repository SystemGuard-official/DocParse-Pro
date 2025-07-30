"""
Custom exceptions for the OCR application.
Provides specific exception types for different error scenarios.
"""

from typing import Optional


class OCRException(Exception):
    """Base exception for OCR-related errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ModelNotFoundError(OCRException):
    """Raised when a requested model is not found or available."""
    pass


class ModelLoadError(OCRException):
    """Raised when a model fails to load."""
    pass


class InvalidImageError(OCRException):
    """Raised when an image is invalid or unsupported."""
    pass


class ImageProcessingError(OCRException):
    """Raised when image processing fails."""
    pass


class JobNotFoundError(OCRException):
    """Raised when a job ID is not found."""
    pass


class JobProcessingError(OCRException):
    """Raised when job processing fails."""
    pass


class RedisConnectionError(OCRException):
    """Raised when Redis connection fails."""
    pass


class ConfigurationError(OCRException):
    """Raised when there's a configuration issue."""
    pass


class ValidationError(OCRException):
    """Raised when input validation fails."""
    pass


class RateLimitExceededError(OCRException):
    """Raised when rate limit is exceeded."""
    pass