"""
API v1 router configuration.
Combines all v1 endpoints into a single router.
"""

from fastapi import APIRouter
from backend.core.config import settings


from backend.api.v1.endpoints.system import router as root_router

# Create the main v1 router
api_router = APIRouter(prefix='/v1')

api_router.include_router(root_router)

if settings.DEPLOYED_OCR == 'TrOCR':
    from backend.api.v1.endpoints.text_extraction import router as ocr_router
    api_router.include_router(ocr_router)

if settings.DEPLOYED_OCR == 'Qwen':
    from backend.api.v1.endpoints.form_parsing import router as forms_router
    api_router.include_router(forms_router)
