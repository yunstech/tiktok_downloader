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
        """Initialize TikTok API with Playwright with enhanced bot detection bypass"""
        try:
            ms_tokens = [settings.tiktok_cookie] if settings.tiktok_cookie else None
            self.api = TikTokApi()
            
            # Enhanced context options to mimic real browser
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "color_scheme": "light",
                "device_scale_factor": 1.0,
                "has_touch": False,
                "java_script_enabled": True,
                "bypass_csp": False,
                "is_mobile": False,
                # Add extra HTTP headers to mimic real browser
                "extra_http_headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                }
            }
            
            # Add proxy if configured
            if settings.tiktok_proxy:
                proxy_parts = settings.tiktok_proxy.split("://")
                if len(proxy_parts) == 2:
                    context_options["proxy"] = {
                        "server": settings.tiktok_proxy
                    }
                    logger.info(f"Using proxy: {settings.tiktok_proxy}")
            
            # Log initialization details
            logger.info(f"Initializing TikTok API (headless={settings.tiktok_headless})")
            if ms_tokens:
                logger.info("Using TikTok session cookie (ms_token)")
            else:
                logger.warning("⚠️  No TIKTOK_COOKIE set - bot detection more likely!")
                logger.warning("💡 Get cookie from browser: DevTools > Application > Cookies > tiktok.com > copy 'sessionid' or 'msToken'")
            
            # Use configurable headless mode (False is better for avoiding detection)
            await self.api.create_sessions(
                ms_tokens=ms_tokens,
                num_sessions=1,
                sleep_after=3,  # Wait 3 seconds after session creation
                headless=settings.tiktok_headless,
                browser="chromium",  # chromium is most stable
                context_options=context_options,
                suppress_resource_load_types=["image", "media", "font"],  # Speed up by blocking unnecessary resources
            )
            
            logger.info("✅ TikTok API initialized successfully")
            if not settings.tiktok_headless:
                logger.info("🖥️  Running in headed mode - browser window will be visible")
        except Exception as e:
            logger.error(f"Failed to initialize TikTok API: {e}")
            raise
    
    async def close(self):
        """Close TikTok API sessions"""
        if self.api:
            await self.api.close_sessions()
            logger.info("TikTok API sessions closed")
    
    async def get_user_profile(self, username: str, retry_count: int = 0) -> UserProfile:
        """Get user profile information with retry logic"""
        max_retries = 2
        try:
            user = self.api.user(username)
            user_data = await user.info()
            
            # Check if we got empty data (bot detection)
            if not user_data or not user_data.get("user"):
                raise RuntimeError("TikTok returned empty user data - likely bot detection")
            
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
            
            logger.info(f"✅ Retrieved profile for user: @{username} ({profile.nickname}) - {profile.follower_count:,} followers, {profile.video_count} videos")
            return profile
        
        except Exception as e:
            error_msg = str(e).lower()
            # Detect bot detection errors
            if any(keyword in error_msg for keyword in ['empty response', 'empty', 'detecting', 'bot', 'blocked', 'captcha']):
                if retry_count < max_retries:
                    wait_time = (retry_count + 1) * 5  # 5s, 10s delays
                    logger.warning(f"⚠️  Bot detection for {username} (attempt {retry_count + 1}/{max_retries + 1})")
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    return await self.get_user_profile(username, retry_count + 1)
                else:
                    logger.error(f"❌ Bot detection error for {username} after {max_retries + 1} attempts: {e}")
                    raise RuntimeError(f"TikTok bot detection: {e}")
            
            logger.error(f"Failed to get user profile for {username}: {e}")
            raise
    
    async def scrape_user_videos(
        self, 
        username: str, 
        max_videos: Optional[int] = None,
        retry_count: int = 0
    ) -> List[VideoInfo]:
        """Scrape all videos from a user's profile with retry logic"""
        max_retries = 2
        try:
            user = self.api.user(username)
            videos = []
            count = 0
            
            logger.info(f"🎬 Starting to scrape videos for user: @{username} (max: {max_videos or 'all'})")
            
            # Add a small delay before fetching videos to appear more human-like
            await asyncio.sleep(2)
            
            async for video in user.videos(count=max_videos or 9999):
                try:
                    # Check if video data is valid
                    if not video or not video.id:
                        logger.warning("⚠️  Received empty video data - possible bot detection")
                        continue
                    
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
                    
                    # Log progress every 10 videos
                    if count % 10 == 0:
                        logger.info(f"📊 Progress: {count} videos scraped...")
                    
                    if max_videos and count >= max_videos:
                        logger.info(f"✅ Reached max videos limit ({max_videos})")
                        break
                    
                    # Small delay between videos to avoid rate limiting
                    await asyncio.sleep(0.3)
                
                except Exception as e:
                    logger.error(f"❌ Failed to parse video: {e}")
                    continue
            
            if len(videos) == 0:
                raise RuntimeError("TikTok returned 0 videos - likely bot detection or empty profile")
            
            logger.info(f"✅ Successfully scraped {len(videos)} videos for user: @{username}")
            return videos
        
        except Exception as e:
            error_msg = str(e).lower()
            # Detect bot detection errors
            if any(keyword in error_msg for keyword in ['empty response', 'empty', 'detecting', 'bot', 'blocked', 'captcha', '0 videos']):
                if retry_count < max_retries:
                    wait_time = (retry_count + 1) * 5  # 5s, 10s delays
                    logger.warning(f"⚠️  Bot detection while scraping {username} (attempt {retry_count + 1}/{max_retries + 1})")
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    return await self.scrape_user_videos(username, max_videos, retry_count + 1)
                else:
                    logger.error(f"❌ Bot detection error while scraping {username} after {max_retries + 1} attempts: {e}")
                    raise RuntimeError(f"TikTok bot detection: {e}")
            
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
