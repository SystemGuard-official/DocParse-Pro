import torch
from fastapi import APIRouter
from backend.core.gpu_manager import gpu_manager, log_gpu_memory
from backend.services.metadata_service import get_api_info
from backend.schemas.gpu_status import GPUStatusResponse, GPUMemoryInfo, GPUStats

router = APIRouter(tags=["API V1 Metadata"])


@router.get("/", summary="API Root", response_model=dict)
async def read_root():
    return get_api_info()


@router.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}


@router.get("/gpu/status", summary="Get GPU resource status", response_model=GPUStatusResponse)
async def get_gpu_status():
    """
    Get current GPU resource allocation status including CUDA availability
    """
    try:
        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        cuda_device_count = torch.cuda.device_count() if cuda_available else 0

        # Get GPU memory info if CUDA is available
        memory_info = None
        if cuda_available:
            mem = log_gpu_memory("GPU status check")
            if isinstance(mem, dict):
                memory_info = GPUMemoryInfo(**mem)

        # Get GPU manager stats
        gpu_stats_dict = gpu_manager.get_stats()

        # Convert dict to GPUStats object
        gpu_stats = GPUStats(**gpu_stats_dict)

        return GPUStatusResponse(
            success=True,
            cuda_available=cuda_available,
            cuda_device_count=cuda_device_count,
            memory_info=memory_info,
            gpu_status=gpu_stats,
            message=f"CUDA: {'Available' if cuda_available else 'Not Available'}",
            error_detail=None
        )
    except Exception as e:
        return GPUStatusResponse(
            success=False,
            cuda_available=False,
            cuda_device_count=0,
            memory_info=None,
            gpu_status={}, # type: ignore
            message="Failed to get GPU status",
            error_detail=str(e)
        )
