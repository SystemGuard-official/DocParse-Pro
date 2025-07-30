from backend.core.config import settings

# app = FastAPI(
#     title=f"OCR API - {settings.DEPLOYED_OCR} Mode", 
#     version="1.0", 
#     description=f"API for {'Optical Character Recognition using TrOCR' if settings.DEPLOYED_OCR == 'TrOCR' else 'Form Parsing using Qwen Vision' if settings.DEPLOYED_OCR == 'Qwen' else 'OCR and Form Parsing'} with in-process queues",
#     lifespan=lifespan
# )


from backend.core.config import settings

# app = FastAPI(
#     title=f"OCR API - {settings.DEPLOYED_OCR} Mode", 
#     version="1.0", 
#     description=f"API for {'Optical Character Recognition using TrOCR' if settings.DEPLOYED_OCR == 'TrOCR' else 'Form Parsing using Qwen Vision' if settings.DEPLOYED_OCR == 'Qwen' else 'OCR and Form Parsing'} with in-process queues",
#     lifespan=lifespan
# )


def get_api_info():
    base_info = {
        "api": f"OCR API - {settings.DEPLOYED_OCR} Mode",
        "version": settings.VERSION,
        "deployed_service": settings.DEPLOYED_OCR,
    }
    
    if settings.DEPLOYED_OCR == 'TrOCR':
        base_info.update({
            "description": "This API provides endpoints for TrOCR-based OCR (text extraction) and PaddleOCR-based text detection using queue-based processing.",
            "endpoints": {
                "/api/v1/ (GET)": {
                    "description": "Get available TrOCR models.",
                    "response": ["List of model names"]
                },
                "/api/v1/ (POST)": {
                    "description": "Submit OCR job to queue for processing.",
                    "parameters": {
                        "file": "Image file (form-data, required)",
                    },
                    "response": {
                        "success": "Boolean indicating submission status",
                        "job_id": "Unique job identifier for polling",
                        "message": "Status message"
                    }
                },
                "/api/v1/priority (POST)": {
                    "description": "Submit high priority OCR job to queue.",
                    "parameters": {
                        "file": "Image file (form-data, required)"
                    },
                    "response": {
                        "success": "Boolean indicating submission status",
                        "job_id": "Unique job identifier for polling",
                        "message": "Status message"
                    }
                },
                "/api/v1/status/{job_id} (GET)": {
                    "description": "Get OCR job status and results.",
                    "parameters": {
                        "job_id": "Job ID from submission"
                    },
                    "response": {
                        "success": "Boolean indicating completion status",
                        "status": "pending/processing/completed/error",
                        "message": "Status message",
                        "result": "OCR results when completed"
                    }
                },
                "/api/v1/queue/status (GET)": {
                    "description": "Get current queue status and worker information.",
                    "response": {
                        "success": "Boolean",
                        "queue_info": "Current queue statistics",
                        "message": "Status message"
                    }
                },
               
            }
        })
    elif settings.DEPLOYED_OCR == 'Qwen':
        base_info.update({
            "description": "This API provides endpoints for Qwen Vision-based form parsing and document analysis using queue-based processing.",
            "endpoints": {
                "/api/v1/parse (POST)": {
                    "description": "Submit form parsing job to queue for processing.",
                    "parameters": {
                        "file": "Image file (form-data, required)",
                        "llm_prompt": "Custom LLM prompt for parsing (optional, uses default if not provided)"
                    },
                    "response": {
                        "success": "Boolean indicating submission status",
                        "job_id": "Unique job identifier for polling",
                        "message": "Status message"
                    }
                },
                "/api/v1/parse/priority (POST)": {
                    "description": "Submit high priority form parsing job to queue.",
                    "parameters": {
                        "file": "Image file (form-data, required)",
                        "llm_prompt": "Custom LLM prompt for parsing (optional)"
                    },
                    "response": {
                        "success": "Boolean indicating submission status",
                        "job_id": "Unique job identifier for polling",
                        "message": "Status message"
                    }
                },
                "/api/v1/parse/status/{job_id} (GET)": {
                    "description": "Get form parsing job status and results.",
                    "parameters": {
                        "job_id": "Job ID from submission"
                    },
                    "response": {
                        "success": "Boolean indicating completion status",
                        "status": "pending/processing/completed/error",
                        "message": "Status message",
                        "result": "Form parsing results when completed (JSON format)"
                    }
                },
                "/api/v1/parse/queue/status (GET)": {
                    "description": "Get current forms queue status and worker information.",
                    "response": {
                        "success": "Boolean",
                        "queue_info": "Current queue statistics",
                        "message": "Status message"
                    }
                }
            }
        })
    else:
        base_info.update({
            "description": "This API provides endpoints for both TrOCR-based OCR and Qwen Vision-based form parsing with queue-based processing.",
            "note": "Both OCR and Form Parsing endpoints are available",
            "endpoints": "See individual service documentation for TrOCR and Qwen endpoints"
        })
    
    # Add common endpoints
    base_info["common_endpoints"] = {
        "/health (GET)": {
            "description": "Overall API health check endpoint",
            "response": {"status": "ok"}
        },
        "/api/v1/ (GET)": {
            "description": "Get this API information",
            "response": "API documentation and available endpoints"
        }
    }
    
    return base_info
