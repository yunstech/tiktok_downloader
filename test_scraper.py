#!/usr/bin/env python3
"""
Test script to verify TikTok scraper configuration and connectivity.
Run this to test if your cookies, proxies, and settings work correctly.
"""

import asyncio
import argparse
import sys
from app.scraper import TikTokScraper
from app.scraper_unified import UnifiedTikTokScraper
from app.config import get_settings
from app.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


async def test_playwright_scraper(username: str, max_videos: int = 5):
    """Test the Playwright scraper directly"""
    print("\n" + "="*60)
    print("🎭 Testing Playwright Scraper")
    print("="*60)
    
    scraper = TikTokScraper()
    
    try:
        # Initialize
        print("\n⏳ Initializing Playwright...")
        await scraper.initialize()
        print("✅ Playwright initialized successfully!")
        
        # Test profile fetching
        print(f"\n⏳ Fetching profile for @{username}...")
        profile = await scraper.get_user_profile(username)
        print(f"✅ Profile retrieved!")
        print(f"   - Name: {profile.nickname}")
        print(f"   - Username: @{profile.username}")
        print(f"   - Followers: {profile.follower_count:,}")
        print(f"   - Total Videos: {profile.video_count}")
        
        # Test video scraping
        print(f"\n⏳ Scraping first {max_videos} videos...")
        videos = await scraper.scrape_user_videos(username, max_videos=max_videos)
        print(f"✅ Scraped {len(videos)} videos!")
        
        if videos:
            print("\n📹 Sample video:")
            video = videos[0]
            desc = video.description[:50] + "..." if len(video.description) > 50 else video.description
            print(f"   - ID: {video.video_id}")
            print(f"   - Description: {desc}")
            print(f"   - Views: {video.view_count:,}")
            print(f"   - Likes: {video.like_count:,}")
        
        print("\n✅ Playwright scraper is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Playwright scraper failed: {e}")
        return False
    
    finally:
        await scraper.close()


async def test_unified_scraper(username: str, max_videos: int = 5):
    """Test the unified scraper (with automatic fallback)"""
    print("\n" + "="*60)
    print("🔀 Testing Unified Scraper (with automatic fallback)")
    print("="*60)
    
    scraper = UnifiedTikTokScraper()
    
    try:
        # Initialize
        print("\n⏳ Initializing scrapers...")
        await scraper.initialize()
        print("✅ Scrapers initialized!")
        
        # Test profile fetching
        print(f"\n⏳ Fetching profile for @{username}...")
        profile = await scraper.get_user_profile(username)
        print(f"✅ Profile retrieved using: {scraper.current_method.upper()} scraper")
        print(f"   - Name: {profile.nickname}")
        print(f"   - Username: @{profile.username}")
        print(f"   - Followers: {profile.follower_count:,}")
        print(f"   - Total Videos: {profile.video_count}")
        
        # Test video scraping
        print(f"\n⏳ Scraping first {max_videos} videos...")
        videos = await scraper.scrape_user_videos(username, max_videos=max_videos)
        print(f"✅ Scraped {len(videos)} videos using: {scraper.current_method.upper()} scraper")
        
        if videos:
            print("\n📹 Sample video:")
            video = videos[0]
            desc = video.description[:50] + "..." if len(video.description) > 50 else video.description
            print(f"   - ID: {video.video_id}")
            print(f"   - Description: {desc}")
            print(f"   - Views: {video.view_count:,}")
            print(f"   - Likes: {video.like_count:,}")
        
        print("\n✅ Unified scraper is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Unified scraper failed: {e}")
        return False
    
    finally:
        await scraper.close()


def print_configuration():
    """Print current configuration"""
    print("\n" + "="*60)
    print("⚙️  Current Configuration")
    print("="*60)
    
    print(f"\n🍪 Cookie: {'✅ SET' if settings.tiktok_cookie else '❌ NOT SET (HIGHLY RECOMMENDED!)'}")
    if not settings.tiktok_cookie:
        print("   💡 Get cookie: See TIKTOK_SETUP.md for instructions")
    
    print(f"\n🌐 Proxy: {'✅ SET - ' + settings.tiktok_proxy if settings.tiktok_proxy else '❌ NOT SET (optional)'}")
    
    print(f"\n👻 Headless: {'✅ YES (faster, more detectable)' if settings.tiktok_headless else '🖥️  NO (slower, less detectable)'}")
    if settings.tiktok_headless:
        print("   💡 Set TIKTOK_HEADLESS=false if getting bot detection errors")
    
    print("\n" + "-"*60)


async def main():
    parser = argparse.ArgumentParser(
        description="Test TikTok scraper configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default username
  python test_scraper.py
  
  # Test with specific username
  python test_scraper.py --username charlidamelio
  
  # Test with more videos
  python test_scraper.py --username tiktok --max-videos 10
  
  # Test only Playwright (no fallback)
  python test_scraper.py --playwright-only
        """
    )
    
    parser.add_argument(
        "--username",
        default="tiktok",
        help="TikTok username to test with (default: tiktok)"
    )
    
    parser.add_argument(
        "--max-videos",
        type=int,
        default=5,
        help="Maximum number of videos to scrape (default: 5)"
    )
    
    parser.add_argument(
        "--playwright-only",
        action="store_true",
        help="Test only Playwright scraper (no unified/fallback)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🧪 TikTok Scraper Configuration Test")
    print("="*60)
    
    # Print configuration
    print_configuration()
    
    # Run tests
    if args.playwright_only:
        success = await test_playwright_scraper(args.username, args.max_videos)
    else:
        success = await test_unified_scraper(args.username, args.max_videos)
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ All tests passed! Your scraper is configured correctly.")
        print("\n💡 Next steps:")
        print("   1. Start the full application: docker compose up")
        print("   2. Use the Telegram bot or API to scrape videos")
    else:
        print("❌ Tests failed! Please check your configuration.")
        print("\n💡 Troubleshooting:")
        print("   1. Add a valid TIKTOK_COOKIE to .env (MOST IMPORTANT)")
        print("   2. Set TIKTOK_HEADLESS=false to see the browser")
        print("   3. Try using a residential proxy")
        print("   4. See TIKTOK_SETUP.md for detailed instructions")
    print("="*60 + "\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
