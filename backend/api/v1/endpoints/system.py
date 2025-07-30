from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.core.gpu_manager import gpu_manager
from backend.services.metadata_service import get_api_info

router = APIRouter(tags=["API V1 Metadata"])

@router.get("/", summary="API Root", response_model=dict)
async def read_root():
    return get_api_info()

@router.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}


@router.get("/gpu/status", summary="Get GPU resource status")
async def get_gpu_status():
    """
    Get current GPU resource allocation status
    """
    try:
        gpu_stats = gpu_manager.get_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "gpu_status": gpu_stats,
                "message": f"GPU: {gpu_stats['active_count']}/{gpu_stats['max_concurrent']} workers active"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to get GPU status",
                "error_detail": str(e)
            }
        )
