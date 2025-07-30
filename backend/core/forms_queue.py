import asyncio
from typing import Dict, Any, Set
from datetime import datetime
from backend.utils.logging.setup import logger
from backend.services.redis_job_manager import set_job_status
from backend.core.gpu_manager import gpu_manager
from backend.core.config import settings

# Import Qwen service conditionally to avoid loading model if not needed
try:
    from backend.services.qwen_vision_service import qwen_parser, clear_gpu_memory
    logger.info("Qwen vision service imported successfully")
except Exception as e:
    logger.warning(f"Qwen vision service not available: {e}")
    qwen_parser = None
    
    def clear_gpu_memory():
        """Dummy function when service is not available"""
        pass


class InProcessFormsQueue:
    """
    In-process queue for form parsing jobs that runs within FastAPI
    Supports configurable number of parallel workers
    """
    
    def __init__(self, max_workers: int = 1):
        self.queue = asyncio.Queue()
        self.priority_queue = asyncio.Queue()
        self.max_workers = max_workers
        self.worker_tasks = []
        self.active_jobs: Set[str] = set()
        self._lock = asyncio.Lock()
        
    async def start_worker(self):
        """Start the background workers within FastAPI"""
        async with self._lock:
            # Start workers up to max_workers limit
            active_workers = len([task for task in self.worker_tasks if not task.done()])
            workers_to_start = self.max_workers - active_workers
            
            for i in range(workers_to_start):
                worker_id = len(self.worker_tasks)
                task = asyncio.create_task(self._worker_loop(worker_id))
                self.worker_tasks.append(task)
                logger.info(f"Forms queue worker {worker_id} started")
    
    async def stop_worker(self):
        """Stop all background workers"""
        async with self._lock:
            for task in self.worker_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            self.worker_tasks.clear()
            logger.info("All forms queue workers stopped")
    
    async def submit_job(self, filename: str, image_bytes: bytes, llm_prompt: str, job_id: str, priority: bool = False):
        """Submit a form parsing job to the queue"""
        job_data = {
            "filename": filename,
            "image_bytes": image_bytes,
            "llm_prompt": llm_prompt,
            "job_id": job_id,
            "submitted_at": datetime.now()
        }
        
        if priority:
            await self.priority_queue.put(job_data)
            logger.info(f"Priority form parsing job {job_id} added to queue")
        else:
            await self.queue.put(job_data)
            logger.info(f"Form parsing job {job_id} added to queue")
        
        # Start worker if not running
        await self.start_worker()
    
    async def _worker_loop(self, worker_id: int):
        """Main worker loop that processes form parsing jobs one by one"""
        logger.info(f"Forms worker {worker_id} loop started")
        
        while True:
            try:
                # Check priority queue first
                job_data = None
                try:
                    # Try to get from priority queue first (non-blocking)
                    job_data = self.priority_queue.get_nowait()
                    logger.info(f"Worker {worker_id} processing priority form parsing job")
                except asyncio.QueueEmpty:
                    try:
                        # If no priority jobs, get from regular queue (non-blocking)
                        job_data = self.queue.get_nowait()
                    except asyncio.QueueEmpty:
                        # No jobs available, wait a bit and try again
                        await asyncio.sleep(1)
                        continue
                
                if job_data:
                    await self._process_job(job_data, worker_id)
                    
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_id} loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_job(self, job_data: Dict[str, Any], worker_id: int):
        """Process a single form parsing job"""
        job_id = job_data["job_id"]
        filename = job_data["filename"]
        image_bytes = job_data["image_bytes"]
        llm_prompt = job_data["llm_prompt"]
        
        gpu_acquired = False
        
        try:
            # Add job to active jobs set
            self.active_jobs.add(job_id)
            
            logger.info(f"Worker {worker_id} starting form parsing for job {job_id}")
            
            # Wait for GPU access with worker ID for tracking
            gpu_acquired = await gpu_manager.wait_for_gpu("forms_queue", worker_id=worker_id, timeout=300.0)  # 5 minute timeout
            if not gpu_acquired:
                raise Exception(f"Could not acquire GPU access within timeout period for worker {worker_id}")
            
            # Clear GPU memory before starting job
            clear_gpu_memory()
            
            set_job_status(job_id, "processing", progress=1)
            
            # Check if qwen_parser is available
            if qwen_parser is None:
                raise Exception("Qwen vision service not available - GPU required")
            
            logger.info(f"Worker {worker_id} starting inference for job {job_id}")
            
            # Run form parsing in a thread to avoid blocking the event loop
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                qwen_parser.parse_form_complete, 
                filename, 
                image_bytes, 
                llm_prompt
            )
            
            # Update status to completed
            set_job_status(job_id, "completed", result=result.model_dump(), progress=100)
            logger.info(f"Worker {worker_id} completed form parsing job {job_id} successfully")
            
        except Exception as e:
            logger.error(f"Worker {worker_id} - Form parsing job {job_id} failed: {str(e)}")
            set_job_status(job_id, "error", error=str(e))
            
        finally:
            # Remove job from active jobs set
            self.active_jobs.discard(job_id)
            
            # Clear GPU memory after job completion/failure
            try:
                clear_gpu_memory()
            except Exception as cleanup_error:
                logger.warning(f"Failed to clear GPU memory after job {job_id}: {cleanup_error}")
            
            # Release GPU access
            if gpu_acquired:
                await gpu_manager.release_gpu("forms_queue", worker_id=worker_id)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "active_jobs": len(self.active_jobs),
            "max_workers": self.max_workers,
            "current_jobs": list(self.active_jobs),
            "queue_size": self.queue.qsize(),
            "priority_queue_size": self.priority_queue.qsize(),
            "total_pending": self.queue.qsize() + self.priority_queue.qsize()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the queue worker"""
        active_workers = len([task for task in self.worker_tasks if not task.done()])
        is_healthy = active_workers > 0
        
        # Check if qwen_parser is available
        parser_available = qwen_parser is not None
        
        # Get GPU manager stats
        gpu_stats = gpu_manager.get_stats()
        
        return {
            "status": "healthy" if (is_healthy and parser_available) else "unhealthy",
            "active_workers": active_workers,
            "max_workers": self.max_workers,
            "workers_running": is_healthy,
            "parser_available": parser_available,
            "queue_size": self.queue.qsize(),
            "priority_queue_size": self.priority_queue.qsize(),
            "gpu_manager": gpu_stats
        }


# Global instance - configure the number of parallel workers here
# Using 1 worker for stable performance and memory management
# Single worker ensures reliable GPU memory usage and processing
forms_queue = InProcessFormsQueue(max_workers=settings.QWEN_MAX_WORKERS)
