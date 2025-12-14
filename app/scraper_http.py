"""
Alternative TikTok Scraper using HTTP requests
- Extracts embedded JSON state from HTML (__UNIVERSAL_DATA_FOR_REHYDRATION__ / SIGI_STATE)
- Tries multiple safe paths to get videos (HTML state first; API as last resort)
- Adds robust cookie parsing (supports full "a=b; c=d" cookie strings)
- Adds a fallback that extracts /@user/video/<id> links from HTML (when list is not provided)
"""

import asyncio
import json
import os
import re
from typing import Optional, List, Dict, Tuple, Any

import httpx
from bs4 import BeautifulSoup

from app.models import VideoInfo, UserProfile
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class TikTokHTTPScraper:
    """Alternative scraper using HTTP requests instead of Playwright."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

        # Keep headers browser-like but not overly custom.
        # NOTE: Avoid forcing Accept-Encoding; let httpx handle it.
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    # ---------------------------
    # Init / Close
    # ---------------------------

    def _parse_cookie(self, raw: str) -> Dict[str, str]:
        """
        Supports:
        - sessionid value only (e.g. "abc123")
        - full cookie header string (e.g. "sessionid=abc; tt_webid_v2=...; ...")
        - quoted strings (removes surrounding quotes)
        """
        raw = (raw or "").strip()
        if not raw:
            return {}
        
        # Remove surrounding quotes if present (common mistake in .env files)
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            raw = raw[1:-1].strip()
            logger.info("[HTTP Scraper] Removed quotes from cookie string")

        if ";" in raw and "=" in raw:
            cookies: Dict[str, str] = {}
            parts = [p.strip() for p in raw.split(";") if "=" in p]
            for p in parts:
                k, v = p.split("=", 1)
                cookies[k.strip()] = v.strip()
            return cookies

        # assume it's sessionid value
        return {"sessionid": raw}

    async def initialize(self):
        """Initialize HTTP client."""
        try:
            cookies: Dict[str, str] = {}
            if settings.tiktok_cookie:
                cookies = self._parse_cookie(settings.tiktok_cookie)
                
                # Log important cookies
                important = ["sessionid", "sessionid_ss", "msToken", "tt_chain_token", "sid_tt"]
                found = [k for k in important if k in cookies]
                missing = [k for k in important if k not in cookies]
                
                logger.info(f"[HTTP Scraper] Using {len(cookies)} TikTok cookies")
                logger.info(f"[HTTP Scraper] ✅ Important cookies found: {', '.join(found) if found else 'NONE'}")
                if missing:
                    logger.warning(f"[HTTP Scraper] ⚠️  Missing important cookies: {', '.join(missing)}")

            client_params: Dict[str, Any] = {
                "headers": self.headers,
                "cookies": cookies,
                "follow_redirects": True,
                "timeout": 30.0,
            }

            # httpx uses "proxy" for a single proxy URL
            if getattr(settings, "tiktok_proxy", None):
                client_params["proxy"] = settings.tiktok_proxy
                logger.info(f"Using proxy: {settings.tiktok_proxy}")

            self.client = httpx.AsyncClient(**client_params)
            logger.info("HTTP scraper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize HTTP scraper: {e}")
            raise

    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            logger.info("HTTP scraper closed")

    # ---------------------------
    # HTML State Extraction
    # ---------------------------

    def _extract_script_json_by_id(self, html: str, script_id: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", {"id": script_id})
        if not script:
            return None
        raw = (script.string or script.get_text(strip=False) or "").strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Failed to parse {script_id} JSON: {e}")
            return None

    def extract_universal_data(self, html: str) -> Optional[Dict]:
        return self._extract_script_json_by_id(html, "__UNIVERSAL_DATA_FOR_REHYDRATION__")

    def extract_sigi_state(self, html: str) -> Optional[Dict]:
        return self._extract_script_json_by_id(html, "SIGI_STATE")

    def extract_json_data(self, html: str) -> Dict:
        """
        Backward-compatible wrapper:
        - tries UNIVERSAL_DATA first
        - then SIGI_STATE
        """
        data = self.extract_universal_data(html)
        if data:
            return data
        data = self.extract_sigi_state(html)
        if data:
            return data
        raise ValueError("Could not find embedded JSON state (UNIVERSAL_DATA or SIGI_STATE)")

    # ---------------------------
    # Profile
    # ---------------------------

    async def get_user_profile(self, username: str) -> UserProfile:
        """Get user profile information."""
        if not self.client:
            raise RuntimeError("HTTP client is not initialized. Call initialize() first.")

        try:
            url = f"https://www.tiktok.com/@{username}"
            logger.info(f"[HTTP Scraper] Fetching profile: {url}")

            response = await self.client.get(url)
            response.raise_for_status()
            logger.info(f"[HTTP Scraper] Got response: {response.status_code}, Content-Length: {len(response.text)}")

            # Prefer UNIVERSAL_DATA for profile, fallback to SIGI
            universal = self.extract_universal_data(response.text)
            if universal:
                default_scope = universal.get("__DEFAULT_SCOPE__", {})
                user_detail = default_scope.get("webapp.user-detail", {})
                user_info_container = (user_detail or {}).get("userInfo") or {}
                user_info = user_info_container.get("user", {}) or {}
                stats = user_info_container.get("stats", {}) or {}

                profile = UserProfile(
                    username=username,
                    user_id=user_info.get("id", "") or "",
                    nickname=user_info.get("nickname", username) or username,
                    avatar_url=user_info.get("avatarLarger", "") or "",
                    bio=user_info.get("signature", "") or "",
                    follower_count=stats.get("followerCount", 0) or 0,
                    following_count=stats.get("followingCount", 0) or 0,
                    video_count=stats.get("videoCount", 0) or 0,
                )

                logger.info(
                    f"[HTTP Scraper] ✓ Retrieved profile: @{username} ({profile.nickname}) - "
                    f"{profile.follower_count:,} followers, {profile.video_count} videos"
                )
                return profile

            # If UNIVERSAL_DATA missing, try SIGI_STATE for profile
            sigi = self.extract_sigi_state(response.text) or {}
            user_module = sigi.get("UserModule", {}) or {}
            users = (user_module.get("users") or {}) if isinstance(user_module, dict) else {}
            stats_map = (user_module.get("stats") or {}) if isinstance(user_module, dict) else {}

            # Try to find the user entry by username
            user_entry = None
            for _uid, u in (users or {}).items():
                if (u.get("uniqueId") or "").lower() == username.lower():
                    user_entry = u
                    break

            # Stats often keyed by internal userId (not username)
            stat_entry = None
            if user_entry:
                uid = user_entry.get("id")
                if uid and isinstance(stats_map, dict):
                    stat_entry = stats_map.get(uid)

            profile = UserProfile(
                username=username,
                user_id=(user_entry or {}).get("id", "") or "",
                nickname=(user_entry or {}).get("nickname", username) or username,
                avatar_url=(user_entry or {}).get("avatarLarger", "") or (user_entry or {}).get("avatarThumb", "") or "",
                bio=(user_entry or {}).get("signature", "") or "",
                follower_count=(stat_entry or {}).get("followerCount", 0) or 0,
                following_count=(stat_entry or {}).get("followingCount", 0) or 0,
                video_count=(stat_entry or {}).get("videoCount", 0) or 0,
            )

            logger.info(
                f"[HTTP Scraper] ✓ Retrieved profile (SIGI): @{username} ({profile.nickname}) - "
                f"{profile.follower_count:,} followers, {profile.video_count} videos"
            )
            return profile

        except Exception as e:
            logger.error(f"Failed to get user profile for {username}: {e}")
            raise

    # ---------------------------
    # Videos: helpers
    # ---------------------------

    def _normalize_video_item(self, item: Dict) -> Dict:
        """
        Some sources wrap actual item under itemStruct / itemInfo.itemStruct.
        Return the likely "itemStruct" dict.
        """
        if not isinstance(item, dict):
            return {}
        if "itemStruct" in item and isinstance(item["itemStruct"], dict):
            return item["itemStruct"]
        if "itemInfo" in item and isinstance(item["itemInfo"], dict):
            ii = item["itemInfo"]
            if "itemStruct" in ii and isinstance(ii["itemStruct"], dict):
                return ii["itemStruct"]
        return item

    def _extract_sec_uid_from_universal(self, universal: Dict) -> Optional[str]:
        try:
            default_scope = universal.get("__DEFAULT_SCOPE__", {})
            user_detail = default_scope.get("webapp.user-detail", {})
            user_info_container = user_detail.get("userInfo", {})
            user = (user_info_container.get("user") or {})
            return user.get("secUid")
        except Exception:
            return None

    def _extract_videos_from_universal(self, universal: Dict) -> List[Dict]:
        """
        Try to find video list in UNIVERSAL_DATA. TikTok often does not include it anymore,
        but we try common paths.
        """
        try:
            default_scope = universal.get("__DEFAULT_SCOPE__", {})
            user_detail = default_scope.get("webapp.user-detail", {}) or {}

            # Sometimes itemList/items are present at top-level, sometimes nested / dict.
            video_list = user_detail.get("itemList") or user_detail.get("items") or []
            if isinstance(video_list, dict):
                video_list = video_list.get("itemList") or video_list.get("items") or []

            if isinstance(video_list, list) and video_list:
                return video_list
        except Exception:
            pass
        return []

    def _extract_videos_from_sigi(self, sigi: Dict, username: str, max_videos: Optional[int]) -> List[Dict]:
        """
        SIGI_STATE often has ItemModule containing many items.
        We'll filter by author.uniqueId if available.
        """
        item_module = sigi.get("ItemModule") or {}
        if not isinstance(item_module, dict) or not item_module:
            return []

        items = list(item_module.values())
        uname = (username or "").lower()

        filtered: List[Dict] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            author = it.get("author") or {}
            if isinstance(author, dict) and (author.get("uniqueId") or "").lower() == uname:
                filtered.append(it)

        if filtered:
            items = filtered

        def _ct(x: Dict) -> int:
            try:
                return int(x.get("createTime", 0) or 0)
            except Exception:
                return 0

        items.sort(key=_ct, reverse=True)
        if max_videos:
            items = items[:max_videos]
        return items

    def _extract_video_ids_from_html_links(self, html: str) -> List[str]:
        """
        Very simple fallback: extract /@user/video/<id> links from HTML.
        """
        ids = list(set(re.findall(r"/@[^/]+/video/(\d+)", html)))
        # no ordering guaranteed
        return ids

    # ---------------------------
    # Videos: optional API (best-effort)
    # ---------------------------

    async def _fetch_videos_via_api(
        self,
        username: str,
        sec_uid: str,
        cursor: int = 0,
        count: int = 30,
    ) -> Tuple[List[Dict], int, bool]:
        """
        Best-effort call to TikTok internal API. This may return 200 with empty list.
        Returns: (videos, next_cursor, has_more)
        
        NOTE: TikTok's API requires many parameters including X-Bogus signature
        which is dynamically generated by their JavaScript. Without proper
        signatures, API will return empty results even with valid cookies.
        """
        if not self.client:
            return [], 0, False

        # Try the newer endpoint with extended parameters
        api_url = "https://www.tiktok.com/api/post/item_list/"
        
        # Build comprehensive parameter list
        # Many of these are required for TikTok's anti-bot checks
        params = {
            "secUid": sec_uid,
            "count": str(count),
            "cursor": str(cursor),
            # Basic app info
            "aid": "1988",
            "app_language": "en",
            "app_name": "tiktok_web",
            "device_platform": "web_mobile",
            "region": "US",
            "priority_region": "US",
            # Browser fingerprinting
            "browser_language": "en-US",
            "browser_name": "Mozilla",
            "browser_online": "true",
            "browser_platform": "Win32",
            "browser_version": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            # Screen info
            "screen_height": "1080",
            "screen_width": "1920",
            # Request metadata
            "from_page": "user",
            "language": "en",
            "coverFormat": "2",
            "post_item_list_request_type": "0",
            "cookie_enabled": "true",
            "focus_state": "true",
            "is_page_visible": "true",
            "is_fullscreen": "false",
            "history_len": "3",
            "tz_name": "America/New_York",
            "webcast_language": "en",
        }
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"https://www.tiktok.com/@{username}",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        try:
            logger.info(f"[HTTP Scraper] Calling TikTok API: {api_url} (cursor={cursor}, count={count})")
            logger.info(f"[HTTP Scraper] API params count: {len(params)}")
            response = await self.client.get(api_url, params=params, headers=headers)
            logger.info(f"[HTTP Scraper] API response status: {response.status_code}")

            # 429: rate limited
            if response.status_code == 429:
                logger.warning("[HTTP Scraper] API rate limited (429). Backing off and retry later.")
                await asyncio.sleep(2.0)
                return [], cursor, True

            if response.status_code == 400:
                logger.warning("[HTTP Scraper] API returned 400 Bad Request")
                logger.warning("[HTTP Scraper] This likely means missing X-Bogus signature or other required parameters")
                logger.warning(f"[HTTP Scraper] Response text: {response.text[:500]}")
                return [], 0, False

            response.raise_for_status()
            
            # Check content type first
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                logger.warning("[HTTP Scraper] API returned HTML instead of JSON - likely CAPTCHA/verification page")
                logger.warning(f"[HTTP Scraper] Response preview: {response.text[:200]}")
                return [], 0, False
            
            # Try to parse JSON
            try:
                data = response.json()
            except Exception as e:
                logger.error(f"[HTTP Scraper] Failed to parse API response as JSON: {e}")
                logger.error(f"[HTTP Scraper] Content-Type: {content_type}")
                logger.error(f"[HTTP Scraper] Response length: {len(response.text)} bytes")
                logger.error(f"[HTTP Scraper] Response preview: {response.text[:500]}")
                return [], 0, False

            videos: List[Dict] = []
            has_more = False
            next_cursor = 0

            if isinstance(data, dict):
                # Check for error status in response
                status_code = data.get("statusCode") or data.get("status_code")
                if status_code and status_code != 0:
                    status_msg = data.get("statusMsg") or data.get("status_msg") or "Unknown error"
                    logger.warning(f"[HTTP Scraper] API returned error status {status_code}: {status_msg}")
                    # If it's an auth/signature error, don't retry
                    return [], 0, False
                
                if "itemList" in data:
                    videos = data.get("itemList") or []
                    has_more = bool(data.get("hasMore", False))
                    next_cursor = int(data.get("cursor", 0) or 0)
                elif "data" in data and isinstance(data["data"], dict):
                    d = data["data"]
                    videos = d.get("itemList") or d.get("items") or []
                    has_more = bool(d.get("hasMore", False))
                    next_cursor = int(d.get("cursor", 0) or 0)

            if len(videos) == 0:
                logger.warning("[HTTP Scraper] API returned 0 videos")
                logger.warning("[HTTP Scraper] ⚠️  TikTok's API requires X-Bogus signature (generated by JavaScript)")
                logger.warning("[HTTP Scraper] Without proper signatures, API returns empty even with valid cookies")
                logger.warning("[HTTP Scraper] 💡 Recommendation: Use Playwright scraper with valid cookie for best results")
            else:
                logger.info(f"[HTTP Scraper] API returned {len(videos)} videos, hasMore={has_more}, nextCursor={next_cursor}")
            
            return videos, next_cursor, has_more

        except httpx.HTTPStatusError as e:
            logger.error(f"[HTTP Scraper] API HTTP error {e.response.status_code}: {e}")
            return [], 0, False
        except Exception as e:
            logger.error(f"[HTTP Scraper] Failed to fetch videos via API: {e}")
            return [], 0, False

    # ---------------------------
    # Videos: main
    # ---------------------------

    async def scrape_user_videos(self, username: str, max_videos: Optional[int] = None) -> List[VideoInfo]:
        """Scrape videos from a user's profile."""
        if not self.client:
            raise RuntimeError("HTTP client is not initialized. Call initialize() first.")

        try:
            url = f"https://www.tiktok.com/@{username}"
            logger.info(f"[HTTP Scraper] Scraping videos from: {url}")
            if max_videos:
                logger.info(f"[HTTP Scraper] Max videos to scrape: {max_videos}")

            response = await self.client.get(url)
            response.raise_for_status()
            logger.info(f"[HTTP Scraper] Got response: {response.status_code}")

            html = response.text

            # 1) UNIVERSAL_DATA: may have secUid + sometimes itemList
            universal = self.extract_universal_data(html)
            sigi = self.extract_sigi_state(html)

            video_list: List[Dict] = []
            sec_uid: Optional[str] = None

            if universal:
                try:
                    default_scope = universal.get("__DEFAULT_SCOPE__", {})
                    user_detail = default_scope.get("webapp.user-detail", {}) or {}
                    logger.info(f"[HTTP Scraper] webapp.user-detail keys: {list(user_detail.keys())}")

                    # If "needFix" present/true, the response might be a challenge/verification state
                    if user_detail.get("needFix"):
                        logger.warning("[HTTP Scraper] needFix=true — TikTok may be requiring verification; video list may be withheld.")

                    sec_uid = self._extract_sec_uid_from_universal(universal)
                    if sec_uid:
                        logger.info(f"[HTTP Scraper] Found secUid: {sec_uid}")

                    video_list = self._extract_videos_from_universal(universal)
                    if video_list:
                        logger.info(f"[HTTP Scraper] Found {len(video_list)} videos in UNIVERSAL_DATA (user-detail itemList/items)")
                    else:
                        logger.warning("[HTTP Scraper] UNIVERSAL_DATA has no itemList/items for videos")

                except Exception as e:
                    logger.warning(f"[HTTP Scraper] Error reading UNIVERSAL_DATA: {e}")

            # 2) SIGI_STATE ItemModule (often works when UNIVERSAL does not have videos)
            if not video_list and sigi:
                sigi_items = self._extract_videos_from_sigi(sigi, username, max_videos)
                if sigi_items:
                    video_list = sigi_items
                    logger.info(f"[HTTP Scraper] Found {len(video_list)} videos in SIGI_STATE ItemModule")
                else:
                    logger.warning("[HTTP Scraper] SIGI_STATE present but ItemModule had no usable items")

            # 3) HTML link fallback: extract video ids from links
            if not video_list:
                ids = self._extract_video_ids_from_html_links(html)
                if ids:
                    logger.info(f"[HTTP Scraper] Extracted {len(ids)} video ids from HTML links (fallback)")
                    if max_videos:
                        ids = ids[:max_videos]
                    video_list = [{"id": vid} for vid in ids]

            # 4) Last resort: internal API user/posts (best-effort)
            if not video_list and sec_uid:
                logger.info("[HTTP Scraper] No videos found in HTML states; attempting to fetch via API (best-effort)...")
                cursor = 0
                has_more = True
                target = max_videos if max_videos else 100  # keep bounded

                while has_more and len(video_list) < target:
                    api_videos, cursor, has_more = await self._fetch_videos_via_api(
                        username=username,
                        sec_uid=sec_uid,
                        cursor=cursor,
                        count=min(30, target - len(video_list)),
                    )

                    if not api_videos:
                        break

                    video_list.extend(api_videos)

                    if max_videos and len(video_list) >= max_videos:
                        video_list = video_list[:max_videos]
                        break

                    await asyncio.sleep(0.5)

            # If still empty, dump minimal debug
            if not video_list:
                try:
                    debug_dir = "downloads/.debug"
                    os.makedirs(debug_dir, exist_ok=True)

                    if universal:
                        debug_file = os.path.join(debug_dir, f"{username}_universal.json")
                        with open(debug_file, "w", encoding="utf-8") as f:
                            json.dump(universal, f, indent=2, ensure_ascii=False)
                        logger.info(f"[HTTP Scraper] 📁 Saved UNIVERSAL_DATA to: {debug_file}")

                    if sigi:
                        debug_file2 = os.path.join(debug_dir, f"{username}_sigi.json")
                        with open(debug_file2, "w", encoding="utf-8") as f:
                            json.dump(sigi, f, indent=2, ensure_ascii=False)
                        logger.info(f"[HTTP Scraper] 📁 Saved SIGI_STATE to: {debug_file2}")

                except Exception as e:
                    logger.error(f"[HTTP Scraper] Error saving debug files: {e}")

                logger.warning(f"[HTTP Scraper] ⚠️ No videos scraped for @{username}")
                return []

            # Parse into VideoInfo
            videos: List[VideoInfo] = []
            total_to_parse = len(video_list)

            logger.info(f"[HTTP Scraper] Starting to parse {total_to_parse} videos...")

            for idx, raw_item in enumerate(video_list, start=1):
                try:
                    item = self._normalize_video_item(raw_item)

                    video_obj = item.get("video", {}) or {}
                    stats_obj = item.get("stats", {}) or {}
                    vid = item.get("id", "") or ""

                    # Prefer direct video URLs if present; fallback to page URL
                    video_url = video_obj.get("downloadAddr") or video_obj.get("playAddr") or ""
                    if not video_url and vid:
                        video_url = f"https://www.tiktok.com/@{username}/video/{vid}"

                    video_info = VideoInfo(
                        video_id=vid,
                        description=item.get("desc", "") or "",
                        create_time=item.get("createTime", 0) or 0,
                        video_url=video_url,
                        thumbnail_url=video_obj.get("cover", "") or video_obj.get("dynamicCover", "") or "",
                        duration=video_obj.get("duration", 0) or 0,
                        view_count=stats_obj.get("playCount", 0) or 0,
                        like_count=stats_obj.get("diggCount", 0) or 0,
                        comment_count=stats_obj.get("commentCount", 0) or 0,
                        share_count=stats_obj.get("shareCount", 0) or 0,
                    )

                    # If max_videos enforced here too
                    videos.append(video_info)
                    if max_videos and len(videos) >= max_videos:
                        logger.info(f"[HTTP Scraper] Reached max videos limit ({max_videos})")
                        break

                    desc_preview = (video_info.description[:50] if video_info.description else "No description")
                    logger.info(
                        f"[HTTP Scraper] ✓ Video {idx}/{total_to_parse}: {video_info.video_id} - "
                        f"{desc_preview}... ({video_info.view_count:,} views)"
                    )

                except Exception as e:
                    logger.error(f"[HTTP Scraper] Failed to parse video item: {e}")
                    continue

            if not videos:
                logger.warning(f"[HTTP Scraper] ⚠️ Parsed 0 videos for @{username} (items existed but parsing failed)")
                return []

            logger.info(f"[HTTP Scraper] ✓ Successfully scraped {len(videos)} videos for user: @{username}")
            return videos

        except Exception as e:
            logger.error(f"Failed to scrape videos for {username}: {e}")
            raise


async def main():
    """Test HTTP scraper."""
    scraper = TikTokHTTPScraper()
    try:
        await scraper.initialize()

        username = "tiktok"
        profile = await scraper.get_user_profile(username)
        print(f"Profile: {profile}")

        videos = await scraper.scrape_user_videos(username, max_videos=5)
        print(f"Found {len(videos)} videos")
        for v in videos[:3]:
            print(v.video_id, v.video_url)

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
