import asyncio
import os
import json
from typing import Optional, List
from datetime import datetime
from TikTokApi import TikTokApi
from app.models import VideoInfo, UserProfile
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class TikTokScraper:
    def __init__(self):
        self.api: Optional[TikTokApi] = None
    
    async def initialize(self):
        """Initialize TikTok API with Playwright"""
        try:
            ms_tokens = [settings.tiktok_cookie] if settings.tiktok_cookie else None
            self.api = TikTokApi()
            
            # Prepare context options
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "locale": "en-US",
                "timezone_id": "America/New_York"
            }
            
            # Add proxy if configured
            if settings.tiktok_proxy:
                proxy_parts = settings.tiktok_proxy.split("://")
                if len(proxy_parts) == 2:
                    context_options["proxy"] = {
                        "server": settings.tiktok_proxy
                    }
                    logger.info(f"Using proxy: {settings.tiktok_proxy}")
            
            # Use configurable headless mode
            logger.info(f"Initializing TikTok API (headless={settings.tiktok_headless})")
            
            await self.api.create_sessions(
                ms_tokens=ms_tokens,
                num_sessions=1,
                sleep_after=3,
                headless=settings.tiktok_headless,
                browser="chromium",
                context_options=context_options
            )
            logger.info("TikTok API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TikTok API: {e}")
            raise
    
    async def close(self):
        """Close TikTok API sessions"""
        if self.api:
            await self.api.close_sessions()
            logger.info("TikTok API sessions closed")
    
    async def get_user_profile(self, username: str) -> UserProfile:
        """Get user profile information"""
        try:
            user = self.api.user(username)
            user_data = await user.info()
            
            stats = user_data.get("stats", {})
            user_info = user_data.get("user", {})
            
            profile = UserProfile(
                username=username,
                user_id=user_info.get("id", ""),
                nickname=user_info.get("nickname", username),
                avatar_url=user_info.get("avatarLarger", ""),
                bio=user_info.get("signature", ""),
                follower_count=stats.get("followerCount", 0),
                following_count=stats.get("followingCount", 0),
                video_count=stats.get("videoCount", 0)
            )
            
            logger.info(f"Retrieved profile for user: {username}")
            return profile
        
        except Exception as e:
            logger.error(f"Failed to get user profile for {username}: {e}")
            raise
    
    async def scrape_user_videos(
        self, 
        username: str, 
        max_videos: Optional[int] = None
    ) -> List[VideoInfo]:
        """Scrape all videos from a user's profile"""
        try:
            user = self.api.user(username)
            videos = []
            count = 0
            
            logger.info(f"Starting to scrape videos for user: {username}")
            
            async for video in user.videos(count=max_videos or 9999):
                try:
                    video_info = VideoInfo(
                        video_id=video.id,
                        description=video.as_dict.get("desc", ""),
                        create_time=video.as_dict.get("createTime", 0),
                        video_url=video.as_dict.get("video", {}).get("downloadAddr", ""),
                        thumbnail_url=video.as_dict.get("video", {}).get("cover", ""),
                        duration=video.as_dict.get("video", {}).get("duration", 0),
                        view_count=video.as_dict.get("stats", {}).get("playCount", 0),
                        like_count=video.as_dict.get("stats", {}).get("diggCount", 0),
                        comment_count=video.as_dict.get("stats", {}).get("commentCount", 0),
                        share_count=video.as_dict.get("stats", {}).get("shareCount", 0)
                    )
                    
                    videos.append(video_info)
                    count += 1
                    
                    if max_videos and count >= max_videos:
                        break
                    
                    logger.info(f"Scraped video {count}: {video_info.video_id}")
                
                except Exception as e:
                    logger.error(f"Failed to scrape video: {e}")
                    continue
            
            logger.info(f"Scraped {len(videos)} videos for user: {username}")
            return videos
        
        except Exception as e:
            logger.error(f"Failed to scrape videos for {username}: {e}")
            raise
    
    async def get_video_download_url(self, video_id: str) -> str:
        """Get direct download URL for a video"""
        try:
            video = self.api.video(id=video_id)
            video_data = await video.info()
            download_url = video_data.get("video", {}).get("downloadAddr", "")
            
            if not download_url:
                raise ValueError(f"No download URL found for video: {video_id}")
            
            return download_url
        
        except Exception as e:
            logger.error(f"Failed to get download URL for video {video_id}: {e}")
            raise


async def main():
    """Test scraper functionality"""
    scraper = TikTokScraper()
    try:
        await scraper.initialize()
        
        # Test scraping
        username = "tiktok"  # Replace with actual username
        profile = await scraper.get_user_profile(username)
        print(f"Profile: {profile}")
        
        videos = await scraper.scrape_user_videos(username, max_videos=5)
        print(f"Found {len(videos)} videos")
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
