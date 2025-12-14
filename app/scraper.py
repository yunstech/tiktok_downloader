import asyncio
import random
import re
from typing import Optional, List, Tuple

from TikTokApi import TikTokApi
from TikTokApi.exceptions import EmptyResponseException

from app.models import VideoInfo, UserProfile
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


def extract_ms_token(raw: Optional[str]) -> Optional[str]:
    """
    settings.tiktok_cookie can be:
    - msToken value only
    - 'msToken=...; other=...'
    - a full Cookie header string
    We only want the msToken VALUE for TikTokApi(ms_tokens=[...])
    """
    if not raw:
        return None
    raw = raw.strip()
    m = re.search(r"msToken=([^;]+)", raw)
    return m.group(1).strip() if m else raw


class TikTokScraper:
    def __init__(self):
        self.api: Optional[TikTokApi] = None
        self._session_profile: Optional[Tuple[str, bool]] = None  # (browser, headless)

    def _context_options(self) -> dict:
        # IMPORTANT: make these consistent with your IP/proxy region
        # If you use a US proxy, set timezone_id accordingly.
        opts = {
            "viewport": {"width": 1280, "height": 720},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "locale": getattr(settings, "tiktok_locale", "id-ID"),
            "timezone_id": getattr(settings, "tiktok_timezone_id", "Asia/Jakarta"),
        }

        if settings.tiktok_proxy:
            # Playwright proxy expects {server, username?, password?}
            # server example: http://host:port  OR socks5://host:port
            opts["proxy"] = {"server": settings.tiktok_proxy}
            logger.info(f"Using proxy: {settings.tiktok_proxy}")

        return opts

    async def initialize(self):
        """
        Create sessions with a strong default (webkit + headful) and fallbacks.
        TikTokApi docs: browser can be 'firefox', 'chromium', 'webkit'. :contentReference[oaicite:1]{index=1}
        """
        ms_token = extract_ms_token(getattr(settings, "tiktok_cookie", None))
        ms_tokens = [ms_token] if ms_token else None

        # Strongest-first strategies (tune if needed)
        strategies: List[Tuple[str, bool]] = [
            ("webkit", False),
            ("chromium", False),
            ("webkit", True),
            ("chromium", True),
        ]

        last_err = None
        for browser, headless in strategies:
            try:
                self.api = TikTokApi()
                logger.info(f"Creating TikTok sessions (browser={browser}, headless={headless})")

                await self.api.create_sessions(
                    ms_tokens=ms_tokens,
                    num_sessions=getattr(settings, "tiktok_num_sessions", 2),
                    sleep_after=getattr(settings, "tiktok_sleep_after", 5),
                    headless=headless,
                    browser=browser,
                    context_options=self._context_options(),
                    enable_session_recovery=True,  # default True, keep explicit
                )

                self._session_profile = (browser, headless)
                logger.info("TikTok API initialized successfully")
                return
            except Exception as e:
                last_err = e
                logger.warning(f"Session init failed (browser={browser}, headless={headless}): {e}")

                try:
                    if self.api:
                        await self.api.close_sessions()
                except Exception:
                    pass

        raise RuntimeError(f"Failed to initialize TikTok API after strategies. Last error: {last_err}")

    async def close(self):
        if self.api:
            await self.api.close_sessions()
            logger.info("TikTok API sessions closed")

    async def _recover_sessions(self):
        """
        Rebuild sessions when TikTok starts returning empty bodies.
        """
        logger.warning("Recovering TikTok sessions...")
        try:
            await self.close()
        finally:
            await asyncio.sleep(2 + random.random())
            await self.initialize()

    async def get_user_profile(self, username: str) -> UserProfile:
        for attempt in range(1, 4):
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
                    video_count=stats.get("videoCount", 0),
                )

                logger.info(f"Retrieved profile for user: {username}")
                return profile

            except EmptyResponseException as e:
                logger.error(f"EmptyResponse on get_user_profile({username}) attempt {attempt}: {e}")
                await self._recover_sessions()
            except Exception as e:
                logger.error(f"Failed to get user profile for {username}: {e}")
                raise

        raise RuntimeError(f"Blocked: could not fetch profile for {username} after retries")

    async def scrape_user_videos(self, username: str, max_videos: Optional[int] = None) -> List[VideoInfo]:
        target = max_videos or getattr(settings, "tiktok_default_max_videos", 30)

        for attempt in range(1, 4):
            try:
                user = self.api.user(username)
                videos: List[VideoInfo] = []
                logger.info(f"Scraping up to {target} videos for user: {username}")

                async for video in user.videos(count=target):
                    v = video.as_dict
                    videos.append(
                        VideoInfo(
                            video_id=video.id,
                            description=v.get("desc", ""),
                            create_time=v.get("createTime", 0),
                            video_url=v.get("video", {}).get("downloadAddr", ""),
                            thumbnail_url=v.get("video", {}).get("cover", ""),
                            duration=v.get("video", {}).get("duration", 0),
                            view_count=v.get("stats", {}).get("playCount", 0),
                            like_count=v.get("stats", {}).get("diggCount", 0),
                            comment_count=v.get("stats", {}).get("commentCount", 0),
                            share_count=v.get("stats", {}).get("shareCount", 0),
                        )
                    )

                    # small jitter helps in practice
                    await asyncio.sleep(0.15 + random.random() * 0.25)

                logger.info(f"Scraped {len(videos)} videos for user: {username}")
                return videos

            except EmptyResponseException as e:
                logger.error(f"EmptyResponse on scrape_user_videos({username}) attempt {attempt}: {e}")
                await self._recover_sessions()
            except Exception as e:
                logger.error(f"Failed to scrape videos for {username}: {e}")
                raise

        raise RuntimeError(f"Blocked: could not fetch videos for {username} after retries")

    
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
