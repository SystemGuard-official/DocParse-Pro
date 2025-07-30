from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class GPUMemoryInfo(BaseModel):
    # You can expand this based on the structure of memory_info returned by log_gpu_memory
    total: Optional[int]
    used: Optional[int]
    free: Optional[int]
    # Add more fields as needed

class GPUStats(BaseModel):
    users: List[str]
    active_users: int
    max_users: int
    gpu_available: bool
    cuda_enabled: bool
    gpu_memory: Optional[GPUMemoryInfo]

class GPUStatusResponse(BaseModel):
    success: bool
    cuda_available: bool
    cuda_device_count: int
    memory_info: Optional[GPUMemoryInfo]
    gpu_status: GPUStats
    message: str
    error_detail: Optional[str] = None
