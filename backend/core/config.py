"""
Configuration management for the OCR application.
Centralized settings using Pydantic for validation and environment variable support.
"""

from pydantic_settings import BaseSettings
from typing import Set, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    PROJECT_NAME: str = "OCR API"
    VERSION: str = "1.0.0"
    
    # =============================================================================
    # OCR MODEL CONFIGURATION
    # =============================================================================
    
    # Main OCR Engine Selection
    DEPLOYED_OCR: str = "TrOCR"  # Options: "Qwen" or "TrOCR"
    
    # Qwen Vision Model Settings
    QWEN_VL_MODEL: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    DEVICE_MAP: str = "auto"
    TRUST_REMOTE_CODE: bool = True  
    LOW_CPU_MEM_USAGE: bool = True
    LOAD_IN_8BIT: bool = True
    LOAD_IN_4BIT: bool = False
        
    DEFAULT_LLM_PROMPT: str = """FORM IMAGE TO JSON - Extract ALL information from this form image and return ONLY a valid JSON object.
            - Do NOT return any commentary, description, example, or explanation—ONLY the JSON object.
            - The output MUST be a single, complete JSON object, only the assistance response no user prompt.
            - Include every field or element you can identify, preserving structure, grouping, and relationships.
            - Represent checkboxes/radios/dropdowns/tables/signatures/printed/handwritten/special elements/sections/empty/incomplete fields/validation/fine print as appropriate JSON keys/values.
            - Mark unclear or questionable values as "[UNCLEAR]".
            - If a field is empty, use null.
            - For lists, use JSON arrays.
            - For tables, use JSON arrays of objects (each object is a row).
            - For booleans (checkboxes, radios), use true/false.
            - For dates, use ISO format if possible.
            - For confidence, use a separate key per section: "confidence": 0.0 to 1.0."""
    QWEN_MAX_WORKERS: int = 1
    
    # TrOCR Model Settings
    DEFAULT_TROCR_MODEL: str = "trocr-large-stage1"
    TROCR_MODELS: dict = {"trocr-large-stage1": "microsoft/trocr-large-stage1"}
    SAVE_TROCR_TRAINING_DATA: bool = False
    MODEL_CACHE_DIR: str = "./models"
    TROCR_MAX_WORKERS: int = 1
    
    # PaddleOCR Settings
    PADDLE_OCR_MODEL: str = "ch_PP-OCRv3_det_infer"
    
    # =============================================================================
    # DATABASE & CACHE CONFIGURATION
    # =============================================================================
    
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # =============================================================================
    # SECURITY & AUTHENTICATION
    # =============================================================================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: list = ["*"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: list = ["*"]
    ALLOW_HEADERS: list = ["*"]
    
    # =============================================================================
    # FILE PROCESSING & VALIDATION
    # =============================================================================
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    ALLOWED_MIME_TYPES: Set[str] = {
        "image/jpeg", "image/jpg", "image/png", 
        "image/bmp", "image/tiff", "image/webp"
    }
    
    # =============================================================================
    # LOGGING & MONITORING
    # =============================================================================
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Monitoring & Health Checks
    ENABLE_METRICS: bool = True
    HEALTH_CHECK_INTERVAL: int = 30
    
    # =============================================================================
    # PERFORMANCE & RATE LIMITING
    # =============================================================================
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

# Global settings instance
settings = Settings()
