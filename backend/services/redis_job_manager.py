import redis
import json 
from backend.core.config import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)


def set_job_status(job_id: str, status: str, result=None, error=None, progress: int = 0):
    data = {
        "status": status,
        "result": result,
        "error": error,
        "progress": progress
    }
    redis_client.set(job_id, json.dumps(data))

def get_job_status(job_id: str):
    job_data = redis_client.get(job_id)
    if job_data is None:
        return None
    return json.loads(job_data) # type:ignore
