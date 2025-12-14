import asyncio
from datetime import datetime
from app.redis_client import RedisClient
from app.scraper_unified import UnifiedTikTokScraper
from app.downloader import VideoDownloader
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class Worker:
    def __init__(self):
        self.redis = RedisClient()
        self.scraper = UnifiedTikTokScraper()  # Use unified scraper with fallback
        self.downloader = VideoDownloader()
        self.running = False
    
    async def start(self):
        """Start the worker"""
        try:
            await self.redis.connect()
            await self.scraper.initialize()
            self.running = True
            
            logger.info("Worker started successfully")
            
            # Run both scraping and downloading workers concurrently
            await asyncio.gather(
                self.scrape_worker(),
                self.download_worker()
            )
        
        except Exception as e:
            logger.error(f"Worker failed to start: {e}")
            raise
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        await self.scraper.close()
        await self.redis.disconnect()
        logger.info("Worker stopped")
    
    async def scrape_worker(self):
        """Worker to process scraping jobs"""
        logger.info("Scrape worker started")
        
        while self.running:
            try:
                # Get next job from queue
                job_id = await self.redis.get_next_job()
                
                if not job_id:
                    continue
                
                logger.info(f"Processing scraping job: {job_id}")
                
                # Get job data
                job_data = await self.redis.get_job(job_id)
                username = job_data.get("username")
                max_videos = job_data.get("max_videos")
                
                if max_videos and max_videos != "all":
                    max_videos = int(max_videos)
                else:
                    max_videos = None
                
                # Update job status
                await self.redis.update_job(job_id, {
                    "status": "scraping",
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                try:
                    # Scrape user profile
                    profile = await self.scraper.get_user_profile(username)
                    logger.info(f"Found profile: {profile.nickname} (@{username})")
                    
                    # Scrape videos
                    videos = await self.scraper.scrape_user_videos(username, max_videos)
                    logger.info(f"Scraped {len(videos)} videos for {username}")
                    
                    # Add videos to download queue
                    for video in videos:
                        video_data = {
                            "video_id": video.video_id,
                            "video_url": video.video_url,
                            "description": video.description,
                            "username": username
                        }
                        await self.redis.add_video_to_download(job_id, video_data)
                    
                    # Update job status
                    await self.redis.update_job(job_id, {
                        "status": "downloading",
                        "total_videos": str(len(videos)),
                        "updated_at": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"Successfully processed scraping job: {job_id}")
                
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to scrape videos for job {job_id}: {e}")
                    
                    # Provide helpful error message
                    if "bot" in error_msg.lower() or "empty response" in error_msg.lower():
                        error_msg = (
                            "TikTok detected bot activity. Please add TIKTOK_COOKIE to .env file. "
                            "See GET_COOKIE.md for instructions."
                        )
                    
                    await self.redis.update_job(job_id, {
                        "status": "failed",
                        "error": error_msg,
                        "updated_at": datetime.utcnow().isoformat()
                    })
                    
                    # Notify user via bot
                    try:
                        chat_id_str = await self.redis.client.hget("job_chat_mapping", job_id)
                        if chat_id_str:
                            from telegram import Bot
                            bot = Bot(token=settings.telegram_bot_token)
                            await bot.send_message(
                                chat_id=int(chat_id_str),
                                text=(
                                    f"❌ *Job Failed*\n\n"
                                    f"🆔 Job ID: `{job_id}`\n"
                                    f"👤 User: `{username}`\n\n"
                                    f"⚠️ Error: {error_msg}\n\n"
                                    f"💡 *Solution:*\n"
                                    f"Add your TikTok session cookie to bypass detection.\n"
                                    f"See the documentation for details."
                                ),
                                parse_mode="Markdown"
                            )
                    except Exception as notify_error:
                        logger.error(f"Failed to notify user about error: {notify_error}")
            
            except Exception as e:
                logger.error(f"Error in scrape worker: {e}")
                await asyncio.sleep(5)
    
    async def download_worker(self):
        """Worker to process video downloads"""
        logger.info("Download worker started")
        
        # Create semaphore for concurrent downloads
        semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        
        while self.running:
            try:
                # Get next download from queue
                job_id, video_id = await self.redis.get_next_download()
                
                if not job_id or not video_id:
                    continue
                
                # Process download with concurrency limit
                asyncio.create_task(
                    self.process_download(job_id, video_id, semaphore)
                )
            
            except Exception as e:
                logger.error(f"Error in download worker: {e}")
                await asyncio.sleep(5)
    
    async def process_download(self, job_id: str, video_id: str, semaphore: asyncio.Semaphore):
        """Process a single video download"""
        async with semaphore:
            try:
                logger.info(f"Downloading video {video_id} for job {job_id}")
                
                # Get video data
                videos = await self.redis.client.hgetall(f"job:{job_id}:videos")
                video_data_str = videos.get(video_id)
                
                if not video_data_str:
                    logger.error(f"Video data not found for {video_id}")
                    return
                
                # Parse video data
                import ast
                video_data = ast.literal_eval(video_data_str)
                video_url = video_data.get("video_url")
                username = video_data.get("username")
                
                # Check if video is already downloaded
                if await self.redis.is_video_downloaded(video_id):
                    logger.info(f"Video {video_id} already downloaded, reusing existing file")
                    filepath = await self.redis.get_video_filepath(video_id)
                    
                    if not filepath:
                        logger.warning(f"Downloaded video {video_id} has no filepath, re-downloading")
                    else:
                        # Update status to completed (reused)
                        await self.redis.update_download_status(
                            job_id, video_id, "completed", 
                            progress=100, 
                            file_path=filepath,
                            reused=True
                        )
                        logger.info(f"Reusing existing download for video {video_id}")
                        
                        # Add to pending videos for batch sending
                        await self.redis.add_pending_video(job_id, video_id, filepath)
                        
                        # Check if we should send a batch
                        pending_count = await self.redis.get_pending_video_count(job_id)
                        if pending_count >= 5:
                            await self.redis.client.lpush("send_videos_queue", job_id)
                            logger.info(f"Queued batch send for job {job_id}")
                        
                        # Continue to check job completion
                        stats = await self.redis.get_job_stats(job_id)
                        job_data = await self.redis.get_job(job_id)
                        total = int(job_data.get("total_videos", 0))
                        
                        if stats["completed"] + stats["failed"] >= total:
                            await self.redis.update_job(job_id, {
                                "status": "completed",
                                "updated_at": datetime.utcnow().isoformat(),
                                "downloaded_videos": str(stats["completed"]),
                                "failed_videos": str(stats["failed"])
                            })
                            logger.info(f"Job {job_id} completed")
                            
                            remaining_count = await self.redis.get_pending_video_count(job_id)
                            if remaining_count > 0:
                                await self.redis.client.lpush("send_videos_queue", job_id)
                                logger.info(f"Queued final batch send for job {job_id}")
                        return
                
                # Update status to downloading
                await self.redis.update_download_status(
                    job_id, video_id, "downloading", progress=0
                )
                
                # Progress callback
                async def progress_callback(vid, progress):
                    await self.redis.update_download_status(
                        job_id, vid, "downloading", progress=progress
                    )
                
                # Download video
                filepath = await self.downloader.download_video(
                    video_url, video_id, username, progress_callback
                )
                
                # Mark video as downloaded globally
                await self.redis.mark_video_downloaded(video_id, filepath)
                
                # Update status to completed
                await self.redis.update_download_status(
                    job_id, video_id, "completed", 
                    progress=100, 
                    file_path=filepath
                )
                
                logger.info(f"Successfully downloaded video {video_id}")
                
                # Add to pending videos for batch sending
                await self.redis.add_pending_video(job_id, video_id, filepath)
                
                # Check if we should send a batch
                pending_count = await self.redis.get_pending_video_count(job_id)
                if pending_count >= 5:
                    # Notify bot to send videos
                    await self.redis.client.lpush("send_videos_queue", job_id)
                    logger.info(f"Queued batch send for job {job_id}")
                
                # Check if all downloads are complete
                stats = await self.redis.get_job_stats(job_id)
                job_data = await self.redis.get_job(job_id)
                total = int(job_data.get("total_videos", 0))
                
                if stats["completed"] + stats["failed"] >= total:
                    await self.redis.update_job(job_id, {
                        "status": "completed",
                        "updated_at": datetime.utcnow().isoformat(),
                        "downloaded_videos": str(stats["completed"]),
                        "failed_videos": str(stats["failed"])
                    })
                    logger.info(f"Job {job_id} completed")
                    
                    # Send remaining videos if any
                    remaining_count = await self.redis.get_pending_video_count(job_id)
                    if remaining_count > 0:
                        await self.redis.client.lpush("send_videos_queue", job_id)
                        logger.info(f"Queued final batch send for job {job_id}")
            
            except Exception as e:
                logger.error(f"Failed to download video {video_id}: {e}")
                await self.redis.update_download_status(
                    job_id, video_id, "failed", error=str(e)
                )


async def main():
    """Main entry point for the worker"""
    worker = Worker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
