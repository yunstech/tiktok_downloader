"""
Alternative TikTok Scraper using HTTP requests
Based on Scrapfly approach - scrapes hidden JSON data from HTML
"""

import asyncio
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import jmespath

from app.models import VideoInfo, UserProfile
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class TikTokHTTPScraper:
    """Alternative scraper using HTTP requests instead of Playwright"""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    async def initialize(self):
        """Initialize HTTP client"""
        try:
            # Add cookie if provided
            cookies = {}
            if settings.tiktok_cookie:
                cookies["sessionid"] = settings.tiktok_cookie
                logger.info("Using TikTok session cookie")
            
            # Configure client parameters
            client_params = {
                "headers": self.headers,
                "cookies": cookies,
                "follow_redirects": True,
                "timeout": 30.0
            }
            
            # Add proxy if provided (httpx uses 'proxy' not 'proxies')
            if settings.tiktok_proxy:
                client_params["proxy"] = settings.tiktok_proxy
                logger.info(f"Using proxy: {settings.tiktok_proxy}")
            
            self.client = httpx.AsyncClient(**client_params)
            logger.info("HTTP scraper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize HTTP scraper: {e}")
            raise
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("HTTP scraper closed")
    
    def extract_json_data(self, html: str) -> Dict:
        """Extract JSON data from TikTok's hidden script tag"""
        try:
            # Find the script tag with __UNIVERSAL_DATA_FOR_REHYDRATION__
            soup = BeautifulSoup(html, 'html.parser')
            script = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
            
            if not script:
                raise ValueError("Could not find data script in HTML")
            
            data = json.loads(script.string)
            return data
        except Exception as e:
            logger.error(f"Failed to extract JSON data: {e}")
            raise
    
    async def get_user_profile(self, username: str) -> UserProfile:
        """Get user profile information"""
        try:
            url = f"https://www.tiktok.com/@{username}"
            logger.info(f"[HTTP Scraper] Fetching profile: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            logger.info(f"[HTTP Scraper] Got response: {response.status_code}, Content-Length: {len(response.text)}")
            
            # Extract data from hidden JSON
            logger.info(f"[HTTP Scraper] Extracting JSON data from HTML...")
            data = self.extract_json_data(response.text)
            user_data = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]
            
            # Parse with JMESPath
            user_info = user_data.get("user", {})
            stats = user_data.get("stats", {})
            
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
            
            logger.info(f"[HTTP Scraper] ✓ Retrieved profile: @{username} ({profile.nickname}) - {profile.follower_count:,} followers, {profile.video_count} videos")
            return profile
        
        except Exception as e:
            logger.error(f"Failed to get user profile for {username}: {e}")
            raise
    
    async def scrape_user_videos(
        self, 
        username: str, 
        max_videos: Optional[int] = None
    ) -> List[VideoInfo]:
        """Scrape videos from a user's profile"""
        try:
            url = f"https://www.tiktok.com/@{username}"
            logger.info(f"[HTTP Scraper] Scraping videos from: {url}")
            if max_videos:
                logger.info(f"[HTTP Scraper] Max videos to scrape: {max_videos}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            logger.info(f"[HTTP Scraper] Got response: {response.status_code}")
            
            # Extract data
            logger.info(f"[HTTP Scraper] Extracting video data from HTML...")
            data = self.extract_json_data(response.text)
            
            # Try to get video list from user detail
            try:
                video_list = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]["itemList"]
                logger.info(f"[HTTP Scraper] Found {len(video_list)} videos in user detail")
            except KeyError:
                logger.warning("[HTTP Scraper] No videos found in user detail, trying alternative method")
                video_list = []
            
            videos = []
            count = 0
            
            logger.info(f"[HTTP Scraper] Starting to parse videos...")
            for video_data in video_list:
                try:
                    # Parse video data
                    video_info = VideoInfo(
                        video_id=video_data.get("id", ""),
                        description=video_data.get("desc", ""),
                        create_time=video_data.get("createTime", 0),
                        video_url=video_data.get("video", {}).get("downloadAddr", ""),
                        thumbnail_url=video_data.get("video", {}).get("cover", ""),
                        duration=video_data.get("video", {}).get("duration", 0),
                        view_count=video_data.get("stats", {}).get("playCount", 0),
                        like_count=video_data.get("stats", {}).get("diggCount", 0),
                        comment_count=video_data.get("stats", {}).get("commentCount", 0),
                        share_count=video_data.get("stats", {}).get("shareCount", 0)
                    )
                    
                    videos.append(video_info)
                    count += 1
                    
                    if max_videos and count >= max_videos:
                        logger.info(f"[HTTP Scraper] Reached max videos limit ({max_videos})")
                        break
                    
                    desc_preview = video_info.description[:50] if video_info.description else "No description"
                    logger.info(f"[HTTP Scraper] ✓ Video {count}/{len(video_list)}: {video_info.video_id} - {desc_preview}... ({video_info.view_count:,} views)")
                
                except Exception as e:
                    logger.error(f"[HTTP Scraper] Failed to parse video: {e}")
                    continue
            
            logger.info(f"[HTTP Scraper] ✓ Successfully scraped {len(videos)} videos for user: @{username}")
            return videos
        
        except Exception as e:
            logger.error(f"Failed to scrape videos for {username}: {e}")
            raise


async def main():
    """Test HTTP scraper"""
    scraper = TikTokHTTPScraper()
    try:
        await scraper.initialize()
        
        # Test scraping
        username = "tiktok"
        profile = await scraper.get_user_profile(username)
        print(f"Profile: {profile}")
        
        videos = await scraper.scrape_user_videos(username, max_videos=5)
        print(f"Found {len(videos)} videos")
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
