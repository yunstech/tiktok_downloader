"""
Video Cache System
Saves scraped video IDs to avoid re-scraping existing videos
"""
import json
import os
from pathlib import Path
from typing import List, Set, Dict, Optional
from datetime import datetime
from app.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class VideoCache:
    """Cache for storing scraped video IDs per user"""
    
    def __init__(self):
        self.cache_dir = Path(settings.download_path) / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Video cache directory: {self.cache_dir}")
    
    def _get_cache_file(self, username: str) -> Path:
        """Get cache file path for a user"""
        return self.cache_dir / f"{username}.json"
    
    def load_cached_videos(self, username: str) -> Dict:
        """Load cached video data for a user"""
        cache_file = self._get_cache_file(username)
        
        if not cache_file.exists():
            logger.info(f"[Cache] No cache found for @{username}")
            return {
                "username": username,
                "last_updated": None,
                "total_videos": 0,
                "video_ids": []
            }
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"[Cache] Loaded {len(data.get('video_ids', []))} cached videos for @{username}")
                return data
        except Exception as e:
            logger.error(f"[Cache] Failed to load cache for @{username}: {e}")
            return {
                "username": username,
                "last_updated": None,
                "total_videos": 0,
                "video_ids": []
            }
    
    def get_cached_video_ids(self, username: str) -> Set[str]:
        """Get set of cached video IDs for a user"""
        data = self.load_cached_videos(username)
        return set(data.get("video_ids", []))
    
    def save_videos(self, username: str, video_ids: List[str]) -> None:
        """Save video IDs to cache"""
        cache_file = self._get_cache_file(username)
        
        # Load existing cache
        existing_data = self.load_cached_videos(username)
        existing_ids = set(existing_data.get("video_ids", []))
        
        # Add new video IDs (prepend new ones to keep newest first)
        new_ids = [vid for vid in video_ids if vid not in existing_ids]
        updated_ids = new_ids + existing_data.get("video_ids", [])
        
        # Prepare cache data
        cache_data = {
            "username": username,
            "last_updated": datetime.utcnow().isoformat(),
            "total_videos": len(updated_ids),
            "video_ids": updated_ids
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"[Cache] Saved {len(updated_ids)} videos for @{username} ({len(new_ids)} new)")
        except Exception as e:
            logger.error(f"[Cache] Failed to save cache for @{username}: {e}")
    
    def add_videos(self, username: str, video_ids: List[str]) -> int:
        """
        Add video IDs to cache, return count of new videos
        
        Returns:
            Number of new videos added
        """
        existing_ids = self.get_cached_video_ids(username)
        new_ids = [vid for vid in video_ids if vid not in existing_ids]
        
        if new_ids:
            # Prepend new videos (newest first)
            all_ids = new_ids + list(existing_ids)
            self.save_videos(username, all_ids)
            logger.info(f"[Cache] Added {len(new_ids)} new videos for @{username}")
        else:
            logger.info(f"[Cache] No new videos for @{username}, all {len(video_ids)} already cached")
        
        return len(new_ids)
    
    def filter_new_videos(self, username: str, video_ids: List[str]) -> List[str]:
        """
        Filter list to only new videos not in cache
        
        Args:
            username: TikTok username
            video_ids: List of video IDs to check
            
        Returns:
            List of video IDs that are not in cache (new videos)
        """
        cached_ids = self.get_cached_video_ids(username)
        new_videos = [vid for vid in video_ids if vid not in cached_ids]
        
        logger.info(f"[Cache] Filtered videos for @{username}: {len(video_ids)} total, {len(new_videos)} new, {len(video_ids) - len(new_videos)} already cached")
        
        return new_videos
    
    def get_cache_stats(self, username: str) -> Dict:
        """Get cache statistics for a user"""
        data = self.load_cached_videos(username)
        return {
            "username": username,
            "total_cached": len(data.get("video_ids", [])),
            "last_updated": data.get("last_updated"),
            "has_cache": len(data.get("video_ids", [])) > 0
        }
    
    def clear_cache(self, username: str) -> bool:
        """Clear cache for a user"""
        cache_file = self._get_cache_file(username)
        
        if cache_file.exists():
            try:
                cache_file.unlink()
                logger.info(f"[Cache] Cleared cache for @{username}")
                return True
            except Exception as e:
                logger.error(f"[Cache] Failed to clear cache for @{username}: {e}")
                return False
        else:
            logger.info(f"[Cache] No cache to clear for @{username}")
            return False
    
    def list_cached_users(self) -> List[str]:
        """List all users with cached data"""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            usernames = [f.stem for f in cache_files]
            logger.info(f"[Cache] Found {len(usernames)} cached users")
            return usernames
        except Exception as e:
            logger.error(f"[Cache] Failed to list cached users: {e}")
            return []


# Global cache instance
_video_cache = None

def get_video_cache() -> VideoCache:
    """Get global video cache instance"""
    global _video_cache
    if _video_cache is None:
        _video_cache = VideoCache()
    return _video_cache
