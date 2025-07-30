import uuid
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

from backend.schemas import FormParsingJobSubmissionResponse, FormParsingJobStatusResponse, FormParsingResult
from backend.utils.image.validation import validate_image_file
from backend.services.redis_job_manager import set_job_status, get_job_status
from backend.core.forms_queue import forms_queue
from backend.core.gpu_manager import gpu_manager
from backend.core.config import settings

router = APIRouter(tags=["Form Parsing"], prefix="/parse")

@router.post("", summary="Submit form parsing job", response_model=FormParsingJobSubmissionResponse)
async def submit_form_parse_job(
    file: UploadFile = File(...),
    llm_prompt: str = Form("")
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

@router.post("/priority", summary="Submit priority form parsing job", response_model=FormParsingJobSubmissionResponse)
async def submit_priority_form_parse_job(
    file: UploadFile = File(...),
    llm_prompt: str = Form("")
):
    """
    Submit high priority form parsing job to queue
    """
    try:
        validate_image_file(file)
        image_bytes = await file.read()
        filename = file.filename
        job_id = str(uuid.uuid4())
        set_job_status(job_id, "pending")
        
        if not llm_prompt:
            llm_prompt = """FORM IMAGE TO JSON - Extract ALL information from this form image and return ONLY a valid JSON object.
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
        else:
            llm_prompt = " ".join(line.strip() for line in llm_prompt.splitlines() if line.strip())
            
        # Submit priority job to the forms queue
        await forms_queue.submit_job(filename, image_bytes, llm_prompt, job_id, priority=True)
        
        return FormParsingJobSubmissionResponse(
            success=True,
            job_id=job_id,
            message="Priority form parse job submitted. Poll for status using job_id.",
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
    return FormParsingJobStatusResponse(
        success=False,
        status="error",
        message=job['error'],
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

