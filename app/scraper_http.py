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
    
    async def _fetch_videos_via_api(
        self, 
        sec_uid: str, 
        cursor: int = 0, 
        count: int = 30
    ) -> tuple[List[Dict], int, bool]:
        """
        Fetch videos using TikTok's internal API
        Returns: (videos, cursor, has_more)
        """
        try:
            # Try the newer API endpoint format
            api_url = f"https://www.tiktok.com/api/user/posts"
            
            params = {
                "secUid": sec_uid,
                "count": str(count),
                "cursor": str(cursor),
            }
            
            # Add additional headers that TikTok might expect
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": f"https://www.tiktok.com/@user",
                "X-Requested-With": "XMLHttpRequest",
            }
            
            logger.info(f"[HTTP Scraper] Calling TikTok API: {api_url} (cursor={cursor}, count={count})")
            
            response = await self.client.get(api_url, params=params, headers=headers)
            
            # Log response details for debugging
            logger.info(f"[HTTP Scraper] API response status: {response.status_code}")
            
            if response.status_code == 400:
                logger.warning(f"[HTTP Scraper] API returned 400 Bad Request - TikTok may have changed their API")
                logger.warning(f"[HTTP Scraper] Response text: {response.text[:500]}")
                return [], 0, False
            
            response.raise_for_status()
            
            data = response.json()
            
            # Try different response structures
            videos = []
            has_more = False
            next_cursor = 0
            
            # Structure 1: Direct itemList
            if "itemList" in data:
                videos = data["itemList"]
                has_more = data.get("hasMore", False)
                next_cursor = data.get("cursor", 0)
            # Structure 2: Nested in data
            elif "data" in data:
                videos = data["data"].get("itemList", data["data"].get("items", []))
                has_more = data["data"].get("hasMore", False)
                next_cursor = data["data"].get("cursor", 0)
            
            logger.info(f"[HTTP Scraper] API returned {len(videos)} videos, hasMore={has_more}, nextCursor={next_cursor}")
            
            return videos, next_cursor, has_more
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[HTTP Scraper] API HTTP error {e.response.status_code}: {e}")
            if e.response.status_code == 400:
                logger.warning("[HTTP Scraper] TikTok API returned 400 - This endpoint may not work without proper authentication")
                logger.warning("[HTTP Scraper] Recommendation: Use a valid TIKTOK_COOKIE or try the Playwright scraper")
            return [], 0, False
        except Exception as e:
            logger.error(f"[HTTP Scraper] Failed to fetch videos via API: {e}")
            return [], 0, False

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
            
            # Get user's secUid for API calls
            sec_uid = None
            try:
                user_detail = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]
                sec_uid = user_detail["userInfo"]["user"]["secUid"]
                logger.info(f"[HTTP Scraper] Found secUid: {sec_uid}")
            except (KeyError, TypeError) as e:
                logger.warning(f"[HTTP Scraper] Could not extract secUid: {e}")
            
            # Try multiple paths to find videos in HTML
            video_list = []
            
            # Try path 1: webapp.user-detail.itemList
            try:
                user_detail = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]
                logger.info(f"[HTTP Scraper] webapp.user-detail keys: {list(user_detail.keys())}")
                video_list = user_detail.get("itemList", [])
                if video_list:
                    logger.info(f"[HTTP Scraper] Found {len(video_list)} videos in webapp.user-detail.itemList")
                else:
                    logger.warning("[HTTP Scraper] Path 1 (webapp.user-detail.itemList) is empty")
            except (KeyError, TypeError) as e:
                logger.warning(f"[HTTP Scraper] Path 1 (webapp.user-detail) error: {e}")
            
            # Try path 2: webapp.user-detail.items (alternative path)
            if not video_list:
                try:
                    user_detail = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]
                    video_list = user_detail.get("items", [])
                    if video_list:
                        logger.info(f"[HTTP Scraper] Found {len(video_list)} videos in webapp.user-detail.items")
                    else:
                        logger.warning("[HTTP Scraper] Path 2 (webapp.user-detail.items) is empty")
                except (KeyError, TypeError) as e:
                    logger.warning(f"[HTTP Scraper] Path 2 error: {e}")
            
            # Try path 3: webapp.video-detail
            if not video_list:
                try:
                    video_detail = data["__DEFAULT_SCOPE__"].get("webapp.video-detail", {})
                    if video_detail and "itemInfo" in video_detail:
                        video_list = [video_detail["itemInfo"]["itemStruct"]]
                        logger.info(f"[HTTP Scraper] Found {len(video_list)} videos in webapp.video-detail")
                except (KeyError, TypeError) as e:
                    logger.warning(f"[HTTP Scraper] Path 3 (webapp.video-detail) not found: {e}")
            
            # If no videos found in HTML, try the API approach
            if not video_list and sec_uid:
                logger.info("[HTTP Scraper] No videos in HTML, attempting to fetch via API...")
                cursor = 0
                has_more = True
                videos_to_fetch = max_videos if max_videos else 100  # Fetch up to 100 if no limit
                
                while has_more and len(video_list) < videos_to_fetch:
                    api_videos, cursor, has_more = await self._fetch_videos_via_api(
                        sec_uid, 
                        cursor=cursor,
                        count=min(30, videos_to_fetch - len(video_list))
                    )
                    
                    if not api_videos:
                        break
                    
                    video_list.extend(api_videos)
                    logger.info(f"[HTTP Scraper] Total videos fetched from API: {len(video_list)}")
                    
                    if max_videos and len(video_list) >= max_videos:
                        video_list = video_list[:max_videos]
                        break
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
            
            # If still no videos, log the available keys for debugging
            if not video_list:
                try:
                    default_scope = data.get("__DEFAULT_SCOPE__", {})
                    available_keys = list(default_scope.keys())
                    logger.warning(f"[HTTP Scraper] No videos found. Available keys: {available_keys[:10]}")
                    
                    # Try to find any key with 'video' or 'item' in it
                    video_keys = [k for k in available_keys if 'video' in k.lower() or 'item' in k.lower()]
                    if video_keys:
                        logger.info(f"[HTTP Scraper] Found potential video keys: {video_keys}")
                    
                    # Dump the full structure to a file for analysis
                    import os
                    debug_dir = "downloads/.debug"
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_file = os.path.join(debug_dir, f"{username}_json_structure.json")
                    
                    with open(debug_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"[HTTP Scraper] 📁 Saved full JSON structure to: {debug_file}")
                    logger.info(f"[HTTP Scraper] You can examine this file to understand TikTok's data structure")
                except Exception as e:
                    logger.error(f"[HTTP Scraper] Error exploring data structure: {e}")
            
            videos = []
            count = 0
            
            if video_list:
                logger.info(f"[HTTP Scraper] Starting to parse {len(video_list)} videos...")
            else:
                logger.warning("[HTTP Scraper] No videos found to parse")
            
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
            
            if len(videos) == 0:
                logger.warning(f"[HTTP Scraper] ⚠️ No videos scraped for @{username}")
                logger.warning("[HTTP Scraper] This could mean:")
                logger.warning("[HTTP Scraper]   1. User has no videos or account is private")
                logger.warning("[HTTP Scraper]   2. TikTok is blocking the request (try adding a valid cookie)")
                logger.warning("[HTTP Scraper]   3. TikTok has changed their data structure")
                logger.warning("[HTTP Scraper] Suggestions:")
                logger.warning("[HTTP Scraper]   - Add a valid TIKTOK_COOKIE to .env")
                logger.warning("[HTTP Scraper]   - Use a residential proxy")
                logger.warning("[HTTP Scraper]   - Try the Playwright scraper instead")
            else:
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
