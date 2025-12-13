from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
from datetime import datetime
import json

from app.models import ScrapeRequest, ScrapeResponse, JobStatus
from app.redis_client import redis_client, get_redis, RedisClient
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app"""
    # Startup
    await redis_client.connect()
    logger.info("FastAPI application started")
    
    yield
    
    # Shutdown
    await redis_client.disconnect()
    logger.info("FastAPI application stopped")


app = FastAPI(
    title="TikTok Scraper & Downloader API",
    description="API for scraping and downloading TikTok videos",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TikTok Scraper & Downloader API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(redis: RedisClient = Depends(get_redis)):
    """Health check endpoint"""
    try:
        await redis.client.ping()
        return {
            "status": "healthy",
            "redis": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_user(
    request: ScrapeRequest,
    redis: RedisClient = Depends(get_redis)
):
    """Start scraping videos from a TikTok user"""
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job data
        job_data = {
            "job_id": job_id,
            "username": request.username,
            "max_videos": str(request.max_videos or "all"),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "total_videos": "0",
            "downloaded_videos": "0",
            "failed_videos": "0"
        }
        
        # Add job to Redis queue
        await redis.add_job(job_id, job_data)
        
        logger.info(f"Created scraping job {job_id} for user {request.username}")
        
        return ScrapeResponse(
            job_id=job_id,
            username=request.username,
            status="pending",
            message="Scraping job created successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to create scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    redis: RedisClient = Depends(get_redis)
):
    """Get the status of a scraping job"""
    try:
        # Get job data
        job_data = await redis.get_job(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get job statistics
        stats = await redis.get_job_stats(job_id)
        
        return JobStatus(
            job_id=job_id,
            username=job_data.get("username", ""),
            status=job_data.get("status", "unknown"),
            total_videos=int(job_data.get("total_videos", 0)),
            downloaded_videos=stats.get("completed", 0),
            failed_videos=stats.get("failed", 0),
            created_at=job_data.get("created_at", ""),
            updated_at=job_data.get("updated_at", ""),
            videos=[]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs")
async def list_jobs(redis: RedisClient = Depends(get_redis)):
    """List all jobs"""
    try:
        # Get all job keys
        keys = await redis.client.keys("job:*")
        jobs = []
        
        for key in keys:
            if ":videos" not in key and ":downloads" not in key:
                job_id = key.replace("job:", "")
                job_data = await redis.get_job(job_id)
                if job_data:
                    jobs.append({
                        "job_id": job_id,
                        "username": job_data.get("username", ""),
                        "status": job_data.get("status", "unknown"),
                        "created_at": job_data.get("created_at", "")
                    })
        
        return {"jobs": jobs}
    
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/job/{job_id}")
async def delete_job(
    job_id: str,
    redis: RedisClient = Depends(get_redis)
):
    """Delete a job and its associated data"""
    try:
        job_data = await redis.get_job(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete job and related keys
        await redis.client.delete(f"job:{job_id}")
        await redis.client.delete(f"job:{job_id}:videos")
        await redis.client.delete(f"job:{job_id}:downloads")
        
        logger.info(f"Deleted job {job_id}")
        
        return {"message": f"Job {job_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
