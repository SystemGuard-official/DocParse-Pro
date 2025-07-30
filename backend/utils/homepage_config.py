"""
Homepage configuration and data structures for the OCR API.
Centralizes all homepage-related configuration to keep the main app.py clean.
"""

from typing import Dict, List, Any
from backend.core.config import settings


class HomepageConfig:
    """Configuration class for homepage content based on deployed OCR service."""
    
    @staticmethod
    def get_service_config(mode: str = None) -> Dict[str, Any]:
        """Get service configuration based on mode or DEPLOYED_OCR setting."""
        
        # Use provided mode or fall back to settings
        service_mode = mode or settings.DEPLOYED_OCR
        
        # Normalize mode to handle case sensitivity and variations
        if service_mode:
            service_mode = service_mode.strip().title()  # Convert to Title Case (e.g., "qwen" -> "Qwen")
        
        base_endpoints = [
            {"method": "GET", "path": "/api/v1/", "description": "API root with metadata", "color": "blue"},
            {"method": "GET", "path": "/api/v1/health", "description": "Health check endpoint", "color": "blue"},
            {"method": "GET", "path": "/api/v1/gpu/status", "description": "GPU resource status", "color": "blue"},
        ]
        
        if service_mode == 'Trocr' or service_mode == 'TrOCR' or service_mode == 'TROCR':
            return {
                "service_name": "TrOCR Text Recognition",
                "service_description": "Advanced text recognition using Microsoft's TrOCR model",
                "service_tagline": "Precise text extraction with state-of-the-art transformer models",
                "service_icon": "fas fa-text-height",
                "service_mode": "TrOCR",
                "primary_color": "blue",
                "accent_color": "indigo",
                "features": [
                    {"name": "Text Extraction", "icon": "fas fa-file-text", "desc": "Extract text from images with high accuracy using transformer models"},
                    {"name": "Multi-language Support", "icon": "fas fa-globe", "desc": "Support for multiple languages and scripts with specialized models"},
                    {"name": "Batch Processing", "icon": "fas fa-layer-group", "desc": "Process multiple images efficiently with queue management"}
                ],
                "service_endpoints": [
                    {"method": "POST", "path": "/api/v1/ocr", "description": "Submit OCR job to queue", "color": "emerald"},
                    {"method": "POST", "path": "/api/v1/ocr/priority", "description": "Submit high priority OCR job", "color": "amber"},
                    {"method": "GET", "path": "/api/v1/ocr/status/{job_id}", "description": "Get OCR job status/result", "color": "violet"},
                    {"method": "GET", "path": "/api/v1/ocr/queue/status", "description": "Get OCR queue status", "color": "cyan"},
                ],
                "curl_example": '''# Upload an image for OCR processing
curl -X POST "http://localhost:8000/api/v1/ocr" \\
     -H "Content-Type: multipart/form-data" \\
     -F "file=@your-image.jpg"''',
                "python_example": '''import requests

# Process image with OCR
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/ocr',
        files={'file': f}
    )
print(response.json())'''
            }
            
        elif service_mode == 'Qwen' or service_mode == 'QWEN':
            return {
                "service_name": "Qwen Vision Form Parser",
                "service_description": "Intelligent form parsing using Qwen Vision model",
                "service_tagline": "Advanced form understanding with AI-powered field extraction",
                "service_icon": "fas fa-file-invoice",
                "service_mode": "Qwen",
                "primary_color": "purple",
                "accent_color": "pink",
                "features": [
                    {"name": "Form Understanding", "icon": "fas fa-wpforms", "desc": "Understand and parse complex form structures with AI intelligence"},
                    {"name": "Field Extraction", "icon": "fas fa-search", "desc": "Extract specific fields and values automatically with high precision"},
                    {"name": "Structured Output", "icon": "fas fa-sitemap", "desc": "Get structured JSON output for easy integration and processing"}
                ],
                "service_endpoints": [
                    {"method": "POST", "path": "/api/v1/parse", "description": "Submit form parsing job", "color": "emerald"},
                    {"method": "POST", "path": "/api/v1/parse/priority", "description": "Submit priority parsing job", "color": "amber"},
                    {"method": "GET", "path": "/api/v1/parse/status/{job_id}", "description": "Get parsing job status/result", "color": "violet"},
                    {"method": "GET", "path": "/api/v1/parse/queue/status", "description": "Get forms queue status", "color": "cyan"},
                ],
                "curl_example": '''# Upload a form for parsing
curl -X POST "http://localhost:8000/api/v1/parse" \\
     -H "Content-Type: multipart/form-data" \\
     -F "file=@form-image.jpg" \\
     -F "llm_prompt=Extract all fields from this form"''',
                "python_example": '''import requests

# Parse form document
with open('form.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/parse',
        files={'file': f},
        data={'llm_prompt': 'Extract all fields'}
    )
print(response.json())'''
            }
            
        elif service_mode == 'Hybrid' or service_mode == 'HYBRID' or service_mode == 'Both' or service_mode == 'both':
            return {
                "service_name": "OCR & Form Parsing Suite",
                "service_description": "Complete solution for text recognition and form parsing",
                "service_tagline": "Unified platform for both text extraction and form understanding",
                "service_icon": "fas fa-eye",
                "service_mode": "Hybrid",
                "primary_color": "teal",
                "accent_color": "orange",
                "features": [
                    {"name": "Text Recognition", "icon": "fas fa-file-text", "desc": "Extract text from any image or document with TrOCR precision"},
                    {"name": "Form Parsing", "icon": "fas fa-wpforms", "desc": "Parse and understand form structures with Qwen intelligence"},
                    {"name": "Flexible Processing", "icon": "fas fa-cogs", "desc": "Choose between TrOCR and Qwen models based on your needs"}
                ],
                "service_endpoints": [
                    {"method": "POST", "path": "/api/v1/ocr", "description": "Submit OCR job", "color": "emerald"},
                    {"method": "POST", "path": "/api/v1/parse", "description": "Submit form parsing job", "color": "amber"},
                    {"method": "GET", "path": "/api/v1/{service}/status/{job_id}", "description": "Get job status (ocr or parse)", "color": "violet"},
                ],
                "curl_example": '''# OCR Processing
curl -X POST "http://localhost:8000/api/v1/ocr" \\
     -H "Content-Type: multipart/form-data" \\
     -F "file=@image.jpg"

# Form Parsing  
curl -X POST "http://localhost:8000/api/v1/parse" \\
     -F "file=@form.jpg" -F "llm_prompt=Extract fields"''',
                "python_example": '''import requests

# OCR Processing
with open('image.jpg', 'rb') as f:
    ocr_response = requests.post(
        'http://localhost:8000/api/v1/ocr',
        files={'file': f}
    )

# Form Parsing
with open('form.jpg', 'rb') as f:
    parse_response = requests.post(
        'http://localhost:8000/api/v1/parse',
        files={'file': f},
        data={'llm_prompt': 'Extract all fields'}
    )'''
            }
        else:
            # Default fallback case
            return {
                "service_name": "OCR & Form Parsing Suite",
                "service_description": "Complete solution for text recognition and form parsing",
                "service_tagline": "Unified platform for both text extraction and form understanding",
                "service_icon": "fas fa-eye",
                "service_mode": "Hybrid",
                "primary_color": "teal",
                "accent_color": "orange",
                "features": [
                    {"name": "Text Recognition", "icon": "fas fa-file-text", "desc": "Extract text from any image or document with TrOCR precision"},
                    {"name": "Form Parsing", "icon": "fas fa-wpforms", "desc": "Parse and understand form structures with Qwen intelligence"},
                    {"name": "Flexible Processing", "icon": "fas fa-cogs", "desc": "Choose between TrOCR and Qwen models based on your needs"}
                ],
                "service_endpoints": [
                    {"method": "POST", "path": "/api/v1/ocr", "description": "Submit OCR job", "color": "emerald"},
                    {"method": "POST", "path": "/api/v1/parse", "description": "Submit form parsing job", "color": "amber"},
                    {"method": "GET", "path": "/api/v1/{service}/status/{job_id}", "description": "Get job status (ocr or parse)", "color": "violet"},
                ],
                "curl_example": '''# OCR Processing
curl -X POST "http://localhost:8000/api/v1/ocr" \\
     -H "Content-Type: multipart/form-data" \\
     -F "file=@image.jpg"

# Form Parsing  
curl -X POST "http://localhost:8000/api/v1/parse" \\
     -F "file=@form.jpg" -F "llm_prompt=Extract fields"''',
                "python_example": '''import requests

# OCR Processing
with open('image.jpg', 'rb') as f:
    ocr_response = requests.post(
        'http://localhost:8000/api/v1/ocr',
        files={'file': f}
    )

# Form Parsing
with open('form.jpg', 'rb') as f:
    parse_response = requests.post(
        'http://localhost:8000/api/v1/parse',
        files={'file': f},
        data={'llm_prompt': 'Extract all fields'}
    )'''
            }
    
    @staticmethod
    def get_base_endpoints() -> List[Dict[str, str]]:
        """Get base system endpoints that are always available."""
        return [
            {"method": "GET", "path": "/api/v1/", "description": "API root with metadata", "color": "slate"},
            {"method": "GET", "path": "/api/v1/health", "description": "Health check endpoint", "color": "slate"},
            {"method": "GET", "path": "/api/v1/gpu/status", "description": "GPU resource status", "color": "slate"},
        ]
