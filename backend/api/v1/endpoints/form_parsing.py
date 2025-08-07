from typing import Optional
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

from backend.schemas import FormParsingJobSubmissionResponse, FormParsingJobStatusResponse, FormParsingResult
from backend.utils.image.validation import validate_image_file
from backend.services.redis_job_manager import set_job_status, get_job_status
from backend.core.forms_queue import forms_queue
from backend.core.config import settings

router = APIRouter(tags=["Form Parsing"], prefix="/parse")

@router.post("", summary="Submit form parsing job", response_model=FormParsingJobSubmissionResponse)
async def submit_form_parse_job(
    file: UploadFile = File(...),
    llm_prompt: str = Form(default="")
):
    try:
        validate_image_file(file)
        image_bytes = await file.read()
        filename = file.filename
        job_id = str(uuid.uuid4())
        set_job_status(job_id, "pending")
        
        if not llm_prompt:
            llm_prompt = settings.DEFAULT_LLM_PROMPT
        else:
            llm_prompt = " ".join(line.strip() for line in llm_prompt.splitlines() if line.strip())
            
        # Submit job to the forms queue instead of background tasks
        await forms_queue.submit_job(filename, image_bytes, llm_prompt, job_id)
        
        return FormParsingJobSubmissionResponse(
            success=True,
            job_id=job_id,
            message="Form parse job submitted. Poll for status using job_id.",
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid request", "error_detail": str(e)}
        )


@router.get("/status/{job_id}", summary="Get form parse job status/result", response_model=FormParsingJobStatusResponse)
async def get_form_parse_job_status_api(job_id: str):
    job = get_job_status(job_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Job ID not found"}
        )
    if job["status"] == "pending":
        return FormParsingJobStatusResponse(
            success=True,
            status="pending",
            message="Job is still processing",
            result=None,
        )
    elif job["status"] == "processing":
        return FormParsingJobStatusResponse(
            success=True,
            status="processing",
            message="Job is still processing",
            result=None,
        )
    elif job["status"] == "completed":
        return FormParsingJobStatusResponse(
            success=True,
            status="completed",
            message="Job completed successfully",
            result=FormParsingResult(**job["result"]),
        )
    # error
    error_message = job.get('error', 'Unknown error occurred')
    # Handle case where error might not be a string
    if isinstance(error_message, dict):
        error_message = str(error_message)
    elif error_message is None:
        error_message = 'Job failed with unknown error'
    
    return FormParsingJobStatusResponse(
        success=False,
        status="error",
        message=str(error_message),
        result=None,
    )

@router.get("/queue/status", summary="Get forms queue status")
async def get_forms_queue_status():
    """
    Get current forms queue status and worker information
    """
    try:
        # Get queue info from in-process queue
        queue_info = forms_queue.get_queue_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "queue_info": queue_info,
                "message": "Forms queue status retrieved successfully"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to get forms queue status",
                "error_detail": str(e)
            }
        )

