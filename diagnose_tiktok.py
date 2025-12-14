#!/usr/bin/env python3
"""
TikTok Cookie & Connection Diagnostic Tool

This script helps diagnose why TikTok scraping is failing by:
1. Testing your cookie validity
2. Checking what data TikTok returns
3. Analyzing the JSON structure
4. Suggesting fixes
"""

import asyncio
import json
import httpx
from bs4 import BeautifulSoup
import sys


async def test_tiktok_connection(username: str, cookie: str = None):
    """Test connection to TikTok and analyze response"""
    
    print("\n" + "="*70)
    print("🔍 TikTok Connection Diagnostic Tool")
    print("="*70)
    
    # Setup
    url = f"https://www.tiktok.com/@{username}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    cookies = {}
    if cookie:
        print(f"\n🍪 Testing with cookie (length: {len(cookie)} chars)")
        print(f"   First 20 chars: {cookie[:20]}...")
        print(f"   Last 20 chars: ...{cookie[-20:]}")
        
        # Try different cookie names TikTok might use
        cookies = {
            "sessionid": cookie,
            "sessionid_ss": cookie,
            "sid_tt": cookie,
            "msToken": cookie,
            "tt_chain_token": cookie,
        }
    else:
        print("\n⚠️  No cookie provided - testing without authentication")
    
    # Test 1: Fetch profile page
    print(f"\n📥 Test 1: Fetching profile page...")
    print(f"   URL: {url}")
    
    async with httpx.AsyncClient(headers=headers, cookies=cookies, follow_redirects=True, timeout=30.0) as client:
        try:
            response = await client.get(url)
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📦 Content-Length: {len(response.text):,} bytes")
            print(f"   🔗 Final URL: {response.url}")
            
            if response.status_code != 200:
                print(f"   ❌ ERROR: Expected 200, got {response.status_code}")
                return False
            
            # Test 2: Extract JSON data
            print(f"\n📥 Test 2: Extracting JSON data...")
            soup = BeautifulSoup(response.text, 'html.parser')
            script = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
            
            if not script:
                print("   ❌ ERROR: Could not find __UNIVERSAL_DATA_FOR_REHYDRATION__ script tag")
                print("   This means TikTok might be blocking or showing a different page")
                return False
            
            print("   ✅ Found JSON data script")
            
            data = json.loads(script.string)
            print(f"   📊 JSON size: {len(json.dumps(data)):,} bytes")
            
            # Test 3: Check profile data
            print(f"\n📥 Test 3: Checking profile data...")
            try:
                default_scope = data.get("__DEFAULT_SCOPE__", {})
                user_detail = default_scope.get("webapp.user-detail", {})
                
                if not user_detail:
                    print("   ❌ ERROR: No user detail data found")
                    print(f"   Available keys: {list(default_scope.keys())}")
                    return False
                
                print(f"   ✅ Found user detail data")
                print(f"   📋 Keys: {list(user_detail.keys())}")
                
                # Extract profile info
                user_info = user_detail.get("userInfo", {})
                if user_info:
                    user = user_info.get("user", {})
                    stats = user_info.get("stats", {})
                    
                    print(f"\n   👤 Profile:")
                    print(f"      Username: @{user.get('uniqueId', 'N/A')}")
                    print(f"      Nickname: {user.get('nickname', 'N/A')}")
                    print(f"      Followers: {stats.get('followerCount', 0):,}")
                    print(f"      Videos: {stats.get('videoCount', 0):,}")
                    print(f"      Verified: {user.get('verified', False)}")
                    print(f"      Private: {user.get('privateAccount', False)}")
                    
                    sec_uid = user.get('secUid', '')
                    if sec_uid:
                        print(f"      SecUid: {sec_uid[:30]}...")
            except Exception as e:
                print(f"   ⚠️  Error parsing profile: {e}")
            
            # Test 4: Check for video data
            print(f"\n📥 Test 4: Checking for video data in HTML...")
            
            # Check all possible paths
            video_paths = [
                ("webapp.user-detail.itemList", lambda: user_detail.get("itemList", [])),
                ("webapp.user-detail.items", lambda: user_detail.get("items", [])),
                ("webapp.video-detail", lambda: default_scope.get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct")),
            ]
            
            videos_found = False
            for path_name, path_func in video_paths:
                try:
                    result = path_func()
                    if result:
                        if isinstance(result, list):
                            print(f"   ✅ Found {len(result)} videos at: {path_name}")
                            videos_found = True
                            # Show sample video
                            if result:
                                sample = result[0]
                                print(f"      Sample video ID: {sample.get('id', 'N/A')}")
                                print(f"      Description: {sample.get('desc', 'N/A')[:50]}...")
                        else:
                            print(f"   ✅ Found video at: {path_name}")
                            videos_found = True
                    else:
                        print(f"   ⚠️  Empty: {path_name}")
                except Exception as e:
                    print(f"   ❌ Error checking {path_name}: {e}")
            
            if not videos_found:
                print(f"\n   ❌ NO VIDEOS FOUND IN HTML")
                print(f"   This is the main problem! TikTok is not including videos in the page.")
            
            # Test 5: Try API endpoint
            print(f"\n📥 Test 5: Testing TikTok API endpoint...")
            
            if sec_uid:
                api_url = "https://www.tiktok.com/api/user/posts"
                params = {
                    "secUid": sec_uid,
                    "count": 10,
                    "cursor": 0,
                }
                
                print(f"   URL: {api_url}")
                print(f"   Params: {params}")
                
                try:
                    api_response = await client.get(api_url, params=params)
                    print(f"   Status: {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        api_data = api_response.json()
                        print(f"   ✅ API responded")
                        print(f"   📋 Keys: {list(api_data.keys())}")
                        
                        item_list = api_data.get("itemList", [])
                        has_more = api_data.get("hasMore", False)
                        status_code = api_data.get("statusCode", -1)
                        
                        print(f"   Status Code: {status_code}")
                        print(f"   Videos: {len(item_list)}")
                        print(f"   Has More: {has_more}")
                        
                        if len(item_list) == 0:
                            print(f"\n   ❌ API RETURNED 0 VIDEOS")
                            print(f"   This means:")
                            print(f"      1. Cookie is invalid/expired")
                            print(f"      2. Account might be private")
                            print(f"      3. TikTok is blocking the request")
                            print(f"      4. API endpoint has changed")
                            
                            # Check for error message
                            if "statusMsg" in api_data:
                                print(f"   Error message: {api_data['statusMsg']}")
                        else:
                            print(f"   ✅ API RETURNED VIDEOS!")
                            sample = item_list[0]
                            print(f"      Sample video ID: {sample.get('id', 'N/A')}")
                    else:
                        print(f"   ❌ API error: {api_response.status_code}")
                        print(f"   Response: {api_response.text[:200]}")
                        
                except Exception as e:
                    print(f"   ❌ API request failed: {e}")
            else:
                print("   ⚠️  Cannot test API - no secUid found")
            
            # Summary
            print(f"\n" + "="*70)
            print("📊 DIAGNOSTIC SUMMARY")
            print("="*70)
            
            print(f"\n✅ Working:")
            print(f"   - HTTP connection to TikTok")
            print(f"   - JSON data extraction")
            print(f"   - Profile information retrieval")
            
            print(f"\n❌ Not Working:")
            if not videos_found:
                print(f"   - Videos are NOT in the HTML response")
            print(f"   - API returns 0 videos")
            
            print(f"\n💡 RECOMMENDATIONS:")
            print(f"\n1. **Cookie Issue** (Most Likely)")
            print(f"   Your cookie is either:")
            print(f"   - Not set")
            print(f"   - Expired (TikTok cookies expire after ~30 days)")
            print(f"   - Wrong format")
            print(f"   - From a logged-out session")
            
            print(f"\n   📝 How to get a VALID cookie:")
            print(f"   a) Open https://www.tiktok.com in Chrome")
            print(f"   b) LOG IN to your TikTok account (important!)")
            print(f"   c) Press F12 > Application > Cookies > tiktok.com")
            print(f"   d) Find 'sessionid' (or 'sessionid_ss')")
            print(f"   e) Copy the ENTIRE value")
            print(f"   f) Add to .env: TIKTOK_COOKIE=<value>")
            
            print(f"\n2. **Account Privacy**")
            print(f"   - If testing with a private account, videos won't be accessible")
            print(f"   - Try with a public account like: tiktok, charlidamelio")
            
            print(f"\n3. **Use Playwright Instead**")
            print(f"   - HTTP scraper has limitations")
            print(f"   - Playwright runs a real browser (harder to detect)")
            print(f"   - Set TIKTOK_HEADLESS=false")
            print(f"   - Add a valid cookie")
            print(f"   - Consider using a residential proxy")
            
            print("="*70 + "\n")
            
            return videos_found
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python diagnose_tiktok.py <username> [cookie]")
        print("Example: python diagnose_tiktok.py tiktok")
        print("Example: python diagnose_tiktok.py itsceceh your_sessionid_cookie_here")
        sys.exit(1)
    
    username = sys.argv[1]
    cookie = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = await test_tiktok_connection(username, cookie)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
