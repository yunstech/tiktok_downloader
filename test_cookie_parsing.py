#!/usr/bin/env python3
"""
Quick test to verify cookie parsing from .env file
"""

import sys
sys.path.insert(0, '/app')

from app.config import get_settings
from app.scraper_http import TikTokHTTPScraper

settings = get_settings()

print("="*70)
print("🍪 Cookie Configuration Test")
print("="*70)

print(f"\n📝 Raw cookie from .env:")
if settings.tiktok_cookie:
    raw = settings.tiktok_cookie
    print(f"   Length: {len(raw)} characters")
    print(f"   First 50 chars: {raw[:50]}")
    print(f"   Last 50 chars: ...{raw[-50:]}")
    has_quotes = raw.startswith('"') or raw.startswith("'")
    print(f"   Has quotes: {has_quotes}")
    print(f"   Has semicolons: {';' in raw}")
    print(f"   Has equals: {'=' in raw}")
else:
    print("   ❌ NOT SET!")
    sys.exit(1)

print(f"\n🔧 Parsed cookies:")
scraper = TikTokHTTPScraper()
parsed = scraper._parse_cookie(settings.tiktok_cookie)

if parsed:
    print(f"   Total cookies: {len(parsed)}")
    print(f"\n   Cookie names:")
    for i, name in enumerate(parsed.keys(), 1):
        value_preview = parsed[name][:20] + "..." if len(parsed[name]) > 20 else parsed[name]
        print(f"      {i}. {name} = {value_preview}")
    
    print(f"\n✅ Important cookies:")
    important = {
        "sessionid": "Session ID (main auth)",
        "sessionid_ss": "Session ID (secure)",
        "msToken": "Microsoft Token",
        "tt_chain_token": "TikTok Chain Token",
        "sid_tt": "Session ID TikTok",
        "ttwid": "TikTok Web ID",
        "odin_tt": "Odin Token"
    }
    
    found_important = []
    for key, desc in important.items():
        if key in parsed:
            found_important.append(key)
            print(f"   ✅ {key}: {desc}")
        else:
            print(f"   ❌ {key}: {desc} - MISSING")
    
    if len(found_important) >= 3:
        print(f"\n✅ Good! Found {len(found_important)}/7 important cookies")
    else:
        print(f"\n⚠️  Warning: Only {len(found_important)}/7 important cookies found")
else:
    print("   ❌ Parsing failed - no cookies extracted!")

print("\n" + "="*70)
