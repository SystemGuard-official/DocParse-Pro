import asyncio
import torch
from typing import Optional
from backend.utils.logging.setup import logger


def log_gpu_memory(context: str = ""):
    """Log current GPU memory usage"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        free = total - allocated
        logger.info(f"{context} - GPU Memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved, {free:.2f}GB free, {total:.2f}GB total")
        return {"allocated": allocated, "reserved": reserved, "free": free, "total": total}
    else:
        logger.warning(f"{context} - CUDA not available")
        return None


class GPUResourceManager:
    """
    Shared GPU resource manager with support for controlled concurrent access
    """
    
    def __init__(self, max_concurrent_users: int = 1):
        self._lock = asyncio.Lock()
        self._current_users: set = set()
        self._max_concurrent = max_concurrent_users
        self._memory_threshold = 12.0
        
    async def acquire_gpu(self, service_name: str, worker_id: int = None) -> bool:
        """
        Acquire GPU access for a service worker
        Returns True if successfully acquired, False if at capacity
        """
        user_id = f"{service_name}_worker_{worker_id}" if worker_id is not None else service_name
        
        async with self._lock:
            # Check if we're at capacity
            if len(self._current_users) >= self._max_concurrent:
                logger.warning(f"GPU access denied to {user_id}, at max capacity ({self._max_concurrent})")
                return False
            
            # Check GPU memory usage
            memory_info = log_gpu_memory(f"GPU check for {user_id}")
            if memory_info and memory_info["allocated"] > self._memory_threshold:
                logger.warning(f"GPU access denied to {user_id}, memory usage too high: {memory_info['allocated']:.2f}GB")
                return False
            
            self._current_users.add(user_id)
            log_gpu_memory(f"GPU acquired by {user_id}")
            logger.info(f"Active GPU users: {len(self._current_users)}/{self._max_concurrent}")
            return True
    
    async def release_gpu(self, service_name: str, worker_id: int = None):
        """
        Release GPU access for a service worker
        """
        user_id = f"{service_name}_worker_{worker_id}" if worker_id is not None else service_name
        
        async with self._lock:
            if user_id in self._current_users:
                self._current_users.remove(user_id)
                log_gpu_memory(f"GPU released by {user_id}")
                logger.info(f"Active GPU users: {len(self._current_users)}/{self._max_concurrent}")
            else:
                logger.warning(f"GPU release attempt by {user_id}, but not in active users")
    
    def get_current_users(self) -> set:
        """Get the set of current GPU users"""
        return self._current_users.copy()
    
    def get_stats(self) -> dict:
        """Get GPU manager statistics"""
        # Check CUDA availability and get memory info
        cuda_available = torch.cuda.is_available()
        memory_info = log_gpu_memory("GPU stats check") if cuda_available else None
        
        return {
            "users": list(self._current_users),
            "active_users": len(self._current_users),
            "max_users": self._max_concurrent,
            "gpu_available": len(self._current_users) < self._max_concurrent,
            "cuda_enabled": cuda_available,
            "gpu_memory": memory_info
        }
    
    async def wait_for_gpu(self, service_name: str, worker_id: int = None, timeout: float = 300.0) -> bool:
        """
        Wait for GPU to become available with timeout
        Returns True if GPU was acquired, False if timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if await self.acquire_gpu(service_name, worker_id):
                return True
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                user_id = f"{service_name}_worker_{worker_id}" if worker_id is not None else service_name
                logger.error(f"GPU acquisition timeout for {user_id}")
                return False
            
            # Wait a bit before trying again
            await asyncio.sleep(2)  # Increased wait time for multiple workers

gpu_manager = GPUResourceManager(max_concurrent_users=1)
