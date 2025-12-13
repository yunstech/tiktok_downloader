import redis.asyncio as redis
from app.config import get_settings
from app.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


class RedisClient:
    def __init__(self):
        self.client: redis.Redis = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")
    
    async def add_job(self, job_id: str, job_data: dict):
        """Add a scraping job to the queue"""
        await self.client.hset(f"job:{job_id}", mapping=job_data)
        await self.client.lpush("job_queue", job_id)
        logger.info(f"Added job {job_id} to queue")
    
    async def add_pending_video(self, job_id: str, video_id: str, filepath: str):
        """Add video to pending send list"""
        await self.client.lpush(f"job:{job_id}:pending_videos", f"{video_id}:{filepath}")
    
    async def get_pending_videos(self, job_id: str, count: int = 5) -> list:
        """Get pending videos for sending"""
        videos = []
        for _ in range(count):
            result = await self.client.rpop(f"job:{job_id}:pending_videos")
            if result:
                videos.append(result)
            else:
                break
        return videos
    
    async def get_pending_video_count(self, job_id: str) -> int:
        """Get count of pending videos"""
        return await self.client.llen(f"job:{job_id}:pending_videos")
    
    async def is_video_sent(self, chat_id: int, video_id: str) -> bool:
        """Check if video has been sent to user"""
        return await self.client.sismember(f"user:{chat_id}:sent_videos", video_id)
    
    async def mark_video_sent(self, chat_id: int, video_id: str):
        """Mark video as sent to user"""
        await self.client.sadd(f"user:{chat_id}:sent_videos", video_id)
        logger.info(f"Marked video {video_id} as sent to user {chat_id}")
    
    async def is_video_downloaded(self, video_id: str) -> bool:
        """Check if video has been downloaded globally"""
        return await self.client.sismember("downloaded_videos", video_id)
    
    async def mark_video_downloaded(self, video_id: str, filepath: str):
        """Mark video as downloaded globally"""
        await self.client.sadd("downloaded_videos", video_id)
        await self.client.hset("video_files", video_id, filepath)
        logger.info(f"Marked video {video_id} as downloaded")
    
    async def get_video_filepath(self, video_id: str) -> str:
        """Get filepath for a previously downloaded video"""
        return await self.client.hget("video_files", video_id)
    
    async def get_job(self, job_id: str) -> dict:
        """Get job data"""
        return await self.client.hgetall(f"job:{job_id}")
    
    async def update_job(self, job_id: str, updates: dict):
        """Update job data"""
        await self.client.hset(f"job:{job_id}", mapping=updates)
    
    async def get_next_job(self) -> str:
        """Get next job from queue (blocking)"""
        result = await self.client.brpop("job_queue", timeout=5)
        if result:
            return result[1]
        return None
    
    async def add_video_to_download(self, job_id: str, video_data: dict):
        """Add video to download queue"""
        video_id = video_data["video_id"]
        await self.client.hset(f"job:{job_id}:videos", video_id, str(video_data))
        await self.client.lpush("download_queue", f"{job_id}:{video_id}")
        logger.info(f"Added video {video_id} to download queue")
    
    async def get_next_download(self) -> tuple:
        """Get next download from queue"""
        result = await self.client.brpop("download_queue", timeout=5)
        if result:
            job_id, video_id = result[1].split(":", 1)
            return job_id, video_id
        return None, None
    
    async def update_download_status(self, job_id: str, video_id: str, status: str, **kwargs):
        """Update download status for a video"""
        await self.client.hset(
            f"job:{job_id}:downloads",
            video_id,
            str({"status": status, **kwargs})
        )
    
    async def get_job_stats(self, job_id: str) -> dict:
        """Get job statistics"""
        downloads = await self.client.hgetall(f"job:{job_id}:downloads")
        total = len(downloads)
        completed = sum(1 for v in downloads.values() if '"status": "completed"' in v)
        failed = sum(1 for v in downloads.values() if '"status": "failed"' in v)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": total - completed - failed
        }


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    return redis_client
