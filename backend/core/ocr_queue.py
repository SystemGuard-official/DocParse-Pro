import asyncio
from typing import Dict, Optional, Any, Set
from datetime import datetime
from backend.utils.logging.setup import logger
from backend.services.ocr_pipeline_service import full_ocr_logic
from backend.services.redis_job_manager import set_job_status, get_job_status
from backend.core.gpu_manager import gpu_manager
from backend.core.config import settings


class InProcessOCRQueue:
    """
    In-process queue for OCR jobs that runs within FastAPI
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
                logger.info(f"OCR queue worker {worker_id} started")
    
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
            logger.info("All OCR queue workers stopped")
    
    async def submit_job(self, filename: str, image_bytes: bytes, job_id: str, priority: bool = False):
        """Submit a job to the queue"""
        job_data = {
            "filename": filename,
            "image_bytes": image_bytes,
            "job_id": job_id,
            "submitted_at": datetime.now()
        }
        
        if priority:
            await self.priority_queue.put(job_data)
            logger.info(f"Priority OCR job {job_id} added to queue")
        else:
            await self.queue.put(job_data)
            logger.info(f"OCR job {job_id} added to queue")
        
        # Start worker if not running
        await self.start_worker()
    
    async def _worker_loop(self, worker_id: int):
        """Main worker loop that processes jobs one by one"""
        logger.info(f"OCR worker {worker_id} loop started")
        
        while True:
            try:
                # Check priority queue first
                job_data = None
                try:
                    # Try to get from priority queue first (non-blocking)
                    job_data = self.priority_queue.get_nowait()
                    logger.info(f"Worker {worker_id} processing priority job")
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
        """Process a single OCR job"""
        job_id = job_data["job_id"]
        filename = job_data["filename"]
        image_bytes = job_data["image_bytes"]
        
        gpu_acquired = False
        
        try:
            # Add job to active jobs set
            self.active_jobs.add(job_id)
            
            logger.info(f"Worker {worker_id} starting OCR processing for job {job_id}")
            
            # Wait for GPU access with timeout
            gpu_acquired = await gpu_manager.wait_for_gpu("ocr_queue", timeout=300.0)  # 5 minute timeout
            if not gpu_acquired:
                raise Exception("Could not acquire GPU access within timeout period")
            
            set_job_status(job_id, "processing", progress=1)
            
            # Run OCR in a thread to avoid blocking the event loop
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                full_ocr_logic, 
                filename, 
                image_bytes, 
                job_id
            )
            
            # Update status to completed
            set_job_status(job_id, "completed", result=result.model_dump(), progress=100)
            logger.info(f"Worker {worker_id} completed OCR job {job_id} successfully")
            
        except Exception as e:
            logger.error(f"Worker {worker_id} - OCR job {job_id} failed: {str(e)}")
            set_job_status(job_id, "error", error=str(e))
            
        finally:
            # Remove job from active jobs set
            self.active_jobs.discard(job_id)
            
            # Release GPU access
            if gpu_acquired:
                await gpu_manager.release_gpu("ocr_queue")
    
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
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "active_workers": active_workers,
            "max_workers": self.max_workers,
            "workers_running": is_healthy,
            "queue_size": self.queue.qsize(),
            "priority_queue_size": self.priority_queue.qsize()
        }


# Global instance - configure the number of parallel workers here
ocr_queue = InProcessOCRQueue(max_workers=settings.TROCR_MAX_WORKERS)
