#!/usr/bin/env python3
"""
Test TikTok Cookie Configuration
This script helps you test if your TikTok cookie is working correctly.
"""

import asyncio
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.scraper import TikTokScraper
from app.config import get_settings
from app.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


async def test_cookie():
    """Test if TikTok cookie is working"""
    
    print("=" * 60)
    print("TikTok Cookie Configuration Test")
    print("=" * 60)
    print()
    
    # Check if cookie is set
    if not settings.tiktok_cookie:
        print("❌ TIKTOK_COOKIE is not set in .env file")
        print()
        print("📋 To fix this:")
        print("1. Open .env file")
        print("2. Add: TIKTOK_COOKIE=your_session_cookie_here")
        print("3. See GET_COOKIE.md for detailed instructions")
        print()
        return False
    
    print(f"✅ TIKTOK_COOKIE is set (length: {len(settings.tiktok_cookie)})")
    print(f"📊 TIKTOK_HEADLESS: {settings.tiktok_headless}")
    if settings.tiktok_proxy:
        print(f"🌐 TIKTOK_PROXY: {settings.tiktok_proxy}")
    print()
    
    # Test scraper
    print("🔍 Testing TikTok API connection...")
    scraper = TikTokScraper()
    
    try:
        # Initialize
        await scraper.initialize()
        print("✅ TikTok API initialized successfully")
        print()
        
        # Test with a known user
        test_username = "tiktok"  # Official TikTok account
        print(f"🎯 Testing with user: @{test_username}")
        
        try:
            profile = await scraper.get_user_profile(test_username)
            print(f"✅ Profile retrieved successfully!")
            print(f"   - Nickname: {profile.nickname}")
            print(f"   - Followers: {profile.follower_count:,}")
            print(f"   - Videos: {profile.video_count:,}")
            print()
            
            # Test scraping videos
            print("📹 Testing video scraping (max 3 videos)...")
            videos = await scraper.scrape_user_videos(test_username, max_videos=3)
            print(f"✅ Scraped {len(videos)} videos successfully!")
            print()
            
            print("=" * 60)
            print("🎉 SUCCESS! Your TikTok configuration is working!")
            print("=" * 60)
            print()
            print("You can now use the bot to scrape TikTok videos.")
            return True
            
        except Exception as e:
            print(f"❌ Failed to scrape user: {e}")
            print()
            
            if "bot" in str(e).lower() or "empty response" in str(e).lower():
                print("⚠️  TikTok is still detecting bot activity")
                print()
                print("💡 Try these solutions:")
                print("1. Get a fresh session cookie (current one may be expired)")
                print("2. Set TIKTOK_HEADLESS=false in .env")
                print("3. Use a residential proxy: TIKTOK_PROXY=http://proxy:port")
                print("4. See TIKTOK_DETECTION.md for more solutions")
            else:
                print(f"⚠️  Unexpected error: {e}")
            
            return False
    
    except Exception as e:
        print(f"❌ Failed to initialize TikTok API: {e}")
        print()
        print("💡 Check your configuration and try again")
        return False
    
    finally:
        await scraper.close()


async def main():
    success = await test_cookie()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
