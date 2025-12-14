import os
import asyncio
import httpx
import aiofiles
from pathlib import Path
from typing import Optional
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class VideoDownloader:
    def __init__(self):
        self.download_path = Path(settings.download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    async def download_video(
        self, 
        video_url: str, 
        video_id: str, 
        username: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Download a video from URL and save to disk"""
        try:
            # Create user-specific directory
            user_dir = self.download_path / username
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{video_id}.mp4"
            filepath = user_dir / filename
            
            # Skip if already downloaded
            if filepath.exists():
                file_size = filepath.stat().st_size
                logger.info(f"♻️ Video {video_id} already exists ({file_size:,} bytes), skipping download")
                return str(filepath)
            
            logger.info(f"📥 Starting download: {video_id} → {filepath}")
            
            # Download video
            async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
                async with client.stream("GET", video_url) as response:
                    response.raise_for_status()
                    
                    # Get total size if available
                    total_size = int(response.headers.get("content-length", 0))
                    total_mb = total_size / (1024 * 1024) if total_size > 0 else 0
                    downloaded = 0
                    
                    logger.info(f"📊 Video {video_id} size: {total_mb:.2f} MB")
                    
                    # Write to file
                    async with aiofiles.open(filepath, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Report progress
                            if progress_callback and total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                await progress_callback(video_id, progress)
            
            final_size = filepath.stat().st_size
            logger.info(f"✅ Downloaded {video_id}: {final_size:,} bytes → {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Failed to download video {video_id}: {e}")
            raise
    
    async def get_video_info(self, filepath: str) -> dict:
        """Get information about a downloaded video"""
        path = Path(filepath)
        if not path.exists():
            return {}
        
        return {
            "filename": path.name,
            "size": path.stat().st_size,
            "path": str(path)
        }
    
    def cleanup_old_downloads(self, days: int = 7):
        """Remove downloads older than specified days"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (days * 86400)  # days to seconds
        
        for filepath in self.download_path.rglob("*.mp4"):
            if filepath.stat().st_mtime < cutoff_time:
                filepath.unlink()
                logger.info(f"Removed old download: {filepath}")


async def main():
    """Test downloader functionality"""
    downloader = VideoDownloader()
    
    # Test download
    test_url = "https://example.com/video.mp4"  # Replace with actual URL
    filepath = await downloader.download_video(test_url, "test_video", "test_user")
    print(f"Downloaded to: {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
