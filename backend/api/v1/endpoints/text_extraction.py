import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List

from backend.schemas import OcrJobSubmissionResponse, OcrJobStatusResponse, OcrJobResult
from backend.utils.image.validation import validate_image_file
from backend.utils.logging.setup import logger
from backend.services.trocr_service import trocr_model_manager
from backend.services.redis_job_manager import set_job_status, get_job_status
from backend.core.ocr_queue import ocr_queue
from backend.core.gpu_manager import gpu_manager


router = APIRouter(tags=["OCR"], prefix="/ocr")

@router.post('', summary="Submit OCR job to queue", response_model=OcrJobSubmissionResponse)
async def submit_ocr_job(file: UploadFile = File(...)):
    """
    Submit OCR job to in-process queue for sequential processing
    """
    try:
        validate_image_file(file)
        image_bytes = await file.read()
        filename = file.filename or "uploaded_image"
        job_id = str(uuid.uuid4())
        
        # Set initial status
        set_job_status(job_id, "pending", progress=0)
        
        # Submit to in-process queue
        await ocr_queue.submit_job(filename, image_bytes, job_id, priority=False)
        
        logger.info(f"OCR job {job_id} submitted to queue")
        
        return OcrJobSubmissionResponse(
            success=True,
            job_id=job_id,
            message="Job submitted to queue. Files will be processed one by one. Poll for status using job_id."
        )
    except Exception as e:
        logger.error(f"Error submitting OCR job: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid request", "error_detail": str(e)}
        )

@router.post('/priority', summary="Submit high priority OCR job", response_model=OcrJobSubmissionResponse)
async def submit_priority_ocr_job(file: UploadFile = File(...)):
    """
    Submit high priority OCR job to queue
    """
    try:
        validate_image_file(file)
        image_bytes = await file.read()
        filename = file.filename or "uploaded_image"
        job_id = str(uuid.uuid4())
        
        # Set initial status
        set_job_status(job_id, "pending", progress=0)
        
        # Submit to priority queue
        await ocr_queue.submit_job(filename, image_bytes, job_id, priority=True)
        
        logger.info(f"Priority OCR job {job_id} submitted to queue")
        
        return OcrJobSubmissionResponse(
            success=True,
            job_id=job_id,
            message="Priority job submitted to queue. Poll for status using job_id."
        )
    except Exception as e:
        logger.error(f"Error submitting priority OCR job: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid request", "error_detail": str(e)}
        )

@router.get('/status/{job_id}', summary="Get OCR job status/result", response_model=OcrJobStatusResponse)
async def get_ocr_job_status_api(job_id: str):
    job = get_job_status(job_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Job ID not found"}
        )
    if job["status"] == "pending":
        return OcrJobStatusResponse(
            success=True,
            status="pending",
            message="Job is still processing",
            progress=job.get("progress", 0),
            result=None,
        )
    elif job["status"] == "processing":
        return OcrJobStatusResponse(
            success=True,
            status="processing",
            message="Job is still processing",
            progress=job.get("progress", 0),
            result=None,
        )
    elif job["status"] == "completed":
        return OcrJobStatusResponse(
            success=True,
            status="completed",
            message="Job completed successfully",
            progress=100,
            result=OcrJobResult(**job["result"]),
        )
    # error
    return OcrJobStatusResponse(
        success=False,
        status="error",
        message="Job failed",
        progress=job.get("progress", 0),
        result=None,
    )


@router.get("/queue/status", summary="Get queue status")
async def get_queue_status():
    """
    Get current queue status and worker information
    """
    try:
        # Get queue info from in-process queue
        queue_info = ocr_queue.get_queue_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "queue_info": queue_info,
                "message": "Queue status retrieved successfully"
            }
        )
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to get queue status",
                "error_detail": str(e)
            }
        )

# @router.post("/extract", response_model=TrOcrExtractionResponse, summary="Run OCR on an image")
# async def perform_ocr(
#     file: UploadFile = File(...),
#     model_data: dict = Depends(trocr_model_manager.get_model_and_processor),
# ):
#     try:
#         validate_image_file(file)
#         filename = file.filename if file.filename is not None else "uploaded_image"
#         image_bytes = await file.read()
#         return trocr_model_manager.run_ocr_on_file(image_bytes, filename, model_data)
#     except HTTPException as e:
#         logger.error(f"Error in perform_ocr: {str(e)}")
#         error_response = ApiErrorResponse(
#             success=False,
#             message="Internal server error during text detection",
#             error_detail=str(e)
#         )
#         return JSONResponse(
#             status_code=500,
#             content=error_response.model_dump()
#         )

# @router.post("/extract/default", response_model=TrOcrExtractionResponse, summary="Run OCR using default model")
# async def perform_ocr_default(file: UploadFile = File(...)):
#     try:
#         validate_image_file(file)
#         filename = file.filename if file.filename is not None else "uploaded_image"
#         image_bytes = await file.read()
#         return trocr_model_manager.run_ocr_default(image_bytes, filename)
#     except HTTPException as e:
#         logger.error(f"Error in perform_ocr_default: {str(e)}")
#         error_response = ApiErrorResponse(
#             success=False,
#             message="Internal server error during text detection",
#             error_detail=str(e)
#         )
#         return JSONResponse(
#             status_code=500,
#             content=error_response.model_dump()
#         )
        

# @router.post("/detect", response_model=TextDetectionResponse, summary="Detect text with bounding boxes")
# async def detect_text_bbox(
#     file: UploadFile = File(..., description="Image file (PNG, JPG, JPEG)")
# ) -> Union[TextDetectionResponse, JSONResponse]:
#     try:
#         validate_image_file(file)
#         image_bytes = await file.read()
#         return paddle_ocr_service.detect_bbox_logic(image_bytes)
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error in text detection endpoint: {str(e)}")
#         error_response = ApiErrorResponse(
#             success=False,
#             message="Internal server error during text detection",
#             error_detail=str(e)
#         )
#         return JSONResponse(
#             status_code=500,
#             content=error_response.model_dump()
#         )
