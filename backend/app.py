from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.v1.router import v1_api_router
from backend.core.config import settings
from backend.utils.logging.setup import logger

forms_queue = None
ocr_queue = None

# Conditionally import queues based on DEPLOYED_OCR setting
if settings.DEPLOYED_OCR == 'TrOCR':
    from backend.core.ocr_queue import ocr_queue
elif settings.DEPLOYED_OCR == 'Qwen':
    from backend.core.forms_queue import forms_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start/stop the queue workers"""
    # Startup
    if ocr_queue is not None:
        logger.info("Starting OCR queue worker...")
        await ocr_queue.start_worker()
    
    if forms_queue is not None:
        logger.info("Starting Forms queue worker...")
        await forms_queue.start_worker()
    
    yield
    
    # Shutdown
    if ocr_queue is not None:
        logger.info("Stopping OCR queue worker...")
        await ocr_queue.stop_worker()
    
    if forms_queue is not None:
        logger.info("Stopping Forms queue worker...")
        await forms_queue.stop_worker()


app = FastAPI(
    title=f"OCR API - {settings.DEPLOYED_OCR} Mode", 
    version=settings.VERSION, 
    description=f"API for {'Optical Character Recognition using TrOCR' if settings.DEPLOYED_OCR == 'TrOCR' else 'Form Parsing using Qwen Vision' if settings.DEPLOYED_OCR == 'Qwen' else 'OCR and Form Parsing'} with in-process queues",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS
)

app.include_router(v1_api_router)
