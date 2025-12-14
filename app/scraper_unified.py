"""
Unified TikTok Scraper with automatic fallback.
Tries Playwright-based scraper first, falls back to HTTP scraper if needed.
"""
import asyncio
from typing import Optional, List

from app.models import VideoInfo, UserProfile
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class UnifiedTikTokScraper:
    """
    Unified scraper that tries Playwright first, falls back to HTTP method.
    """
    
    def __init__(self):
        self.playwright_scraper = None
        self.http_scraper = None
        self.current_method = None  # 'playwright' or 'http'
        
    async def initialize(self):
        """Initialize scrapers - try Playwright first, fallback to HTTP"""
        # Try both methods, prefer Playwright but don't fail if it doesn't work
        playwright_error = None
        
        try:
            # Try Playwright first with timeout
            logger.info("Attempting to initialize Playwright scraper...")
            from app.scraper import TikTokScraper
            self.playwright_scraper = TikTokScraper()
            
            # Use asyncio.wait_for to timeout if initialization takes too long
            await asyncio.wait_for(
                self.playwright_scraper.initialize(),
                timeout=30.0  # 30 second timeout
            )
            
            self.current_method = 'playwright'
            logger.info("✓ Playwright scraper initialized successfully")
            
        except asyncio.TimeoutError:
            playwright_error = "Playwright initialization timed out after 30s"
            logger.warning(f"Playwright scraper failed: {playwright_error}")
        except Exception as e:
            playwright_error = str(e)
            logger.warning(f"Playwright scraper failed to initialize: {e}")
            
        # If Playwright failed, try HTTP scraper
        if playwright_error:
            logger.info("Falling back to HTTP scraper...")
            
            try:
                # Fallback to HTTP scraper
                from app.scraper_http import TikTokHTTPScraper
                self.http_scraper = TikTokHTTPScraper()
                await self.http_scraper.initialize()
                self.current_method = 'http'
                logger.info("✓ HTTP scraper initialized successfully (fallback mode)")
                
            except Exception as http_error:
                logger.error(f"HTTP scraper also failed: {http_error}")
                raise RuntimeError(f"Failed to initialize any scraper method. Playwright: {playwright_error}, HTTP: {http_error}")
    
    async def close(self):
        """Close all scrapers"""
        if self.playwright_scraper:
            try:
                await self.playwright_scraper.close()
            except Exception as e:
                logger.warning(f"Error closing Playwright scraper: {e}")
                
        if self.http_scraper:
            try:
                await self.http_scraper.close()
            except Exception as e:
                logger.warning(f"Error closing HTTP scraper: {e}")
    
    async def _try_with_fallback(self, operation_name: str, playwright_func, http_func):
        """
        Try an operation with Playwright, fallback to HTTP if needed.
        
        Args:
            operation_name: Name of the operation for logging
            playwright_func: Async function to try with Playwright
            http_func: Async function to try with HTTP scraper
        """
        # If already using HTTP, skip Playwright
        if self.current_method == 'http':
            logger.debug(f"{operation_name}: Using HTTP scraper (already in fallback mode)")
            return await http_func()
        
        # Try Playwright first
        try:
            logger.debug(f"{operation_name}: Trying Playwright scraper")
            return await playwright_func()
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a detection/blocking error or RuntimeError from retries
            is_blocked = any(keyword in error_msg for keyword in [
                'empty response', 'blocked', 'captcha', 'bot', 
                'timeout', 'connection', 'not available', 'could not fetch',
                'after retries', 'detecting you'
            ])
            
            if is_blocked:
                logger.warning(f"{operation_name}: Playwright blocked/failed, switching to HTTP scraper")
                logger.info(f"Playwright error: {e}")
                
                # Initialize HTTP scraper if not already
                if not self.http_scraper:
                    logger.info("Initializing HTTP scraper as fallback...")
                    from app.scraper_http import TikTokHTTPScraper
                    self.http_scraper = TikTokHTTPScraper()
                    await self.http_scraper.initialize()
                
                # Switch to HTTP mode
                self.current_method = 'http'
                logger.info(f"✓ Switched to HTTP scraper for {operation_name}")
                
                # Try with HTTP
                return await http_func()
            else:
                # Non-blocking error, re-raise
                raise
    
    async def get_user_profile(self, username: str) -> UserProfile:
        """Get user profile - tries Playwright first, falls back to HTTP"""
        
        async def playwright_method():
            if not self.playwright_scraper:
                raise RuntimeError("Playwright scraper not initialized")
            return await self.playwright_scraper.get_user_profile(username)
        
        async def http_method():
            if not self.http_scraper:
                from app.scraper_http import TikTokHTTPScraper
                self.http_scraper = TikTokHTTPScraper()
                await self.http_scraper.initialize()
            return await self.http_scraper.get_user_profile(username)
        
        return await self._try_with_fallback(
            f"get_user_profile({username})",
            playwright_method,
            http_method
        )
    
    async def scrape_user_videos(
        self, 
        username: str, 
        max_videos: Optional[int] = None
    ) -> List[VideoInfo]:
        """Scrape user videos - tries Playwright first, falls back to HTTP"""
        
        async def playwright_method():
            if not self.playwright_scraper:
                raise RuntimeError("Playwright scraper not initialized")
            return await self.playwright_scraper.scrape_user_videos(username, max_videos)
        
        async def http_method():
            if not self.http_scraper:
                from app.scraper_http import TikTokHTTPScraper
                self.http_scraper = TikTokHTTPScraper()
                await self.http_scraper.initialize()
            return await self.http_scraper.scrape_user_videos(username, max_videos)
        
        return await self._try_with_fallback(
            f"scrape_user_videos({username}, max={max_videos})",
            playwright_method,
            http_method
        )
    
    async def get_video_download_url(self, video_id: str) -> str:
        """Get video download URL"""
        if self.current_method == 'playwright' and self.playwright_scraper:
            try:
                return await self.playwright_scraper.get_video_download_url(video_id)
            except Exception as e:
                logger.warning(f"Playwright get_video_download_url failed: {e}")
        
        # HTTP scraper doesn't have this method, would need to implement
        # For now, raise not implemented
        raise NotImplementedError("HTTP scraper doesn't support get_video_download_url yet")


async def main():
    """Test unified scraper"""
    scraper = UnifiedTikTokScraper()
    try:
        await scraper.initialize()
        print(f"✓ Initialized with method: {scraper.current_method}")
        
        # Test with a username
        username = "tiktok"
        print(f"\nFetching profile for @{username}...")
        profile = await scraper.get_user_profile(username)
        print(f"✓ Profile: {profile.nickname} ({profile.follower_count:,} followers)")
        
        print(f"\nFetching videos...")
        videos = await scraper.scrape_user_videos(username, max_videos=3)
        print(f"✓ Found {len(videos)} videos")
        for i, video in enumerate(videos, 1):
            print(f"  {i}. {video.video_id}: {video.description[:50]}...")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
        print("\n✓ Closed")


if __name__ == "__main__":
    asyncio.run(main())
