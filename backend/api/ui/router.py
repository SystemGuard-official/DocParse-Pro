"""
API v1 router configuration.
Combines all v1 endpoints into a single router.
"""

from fastapi import APIRouter
from backend.core.config import settings


from backend.api.ui.endpoints.homepage import router as root_router

# Create the main v1 router
ui_router = APIRouter()

ui_router.include_router(root_router)
