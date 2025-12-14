# Scraper Fallback System

## Overview

The TikTok scraper now uses a **dual-method approach** with automatic fallback:

1. **Playwright Method** (Primary) - Uses browser automation via TikTokApi
2. **HTTP Method** (Fallback) - Scrapes HTML directly, no browser needed

The system automatically switches to HTTP scraping if Playwright gets blocked.

## How It Works

### Initialization

```python
from app.scraper_unified import UnifiedTikTokScraper

scraper = UnifiedTikTokScraper()
await scraper.initialize()
```

The scraper tries to initialize in this order:
1. **Try Playwright first** - Best for getting video download URLs
2. **Fallback to HTTP** - If Playwright fails (bot detection, dependencies, etc.)

### Automatic Fallback

During operation, if Playwright encounters blocking errors:
- "empty response"
- "bot detected"
- "captcha"
- "timeout"
- "connection" errors

The scraper **automatically switches** to HTTP method and retries.

### Methods

Both scraping methods support:
- ✅ `get_user_profile(username)` - Get user profile info
- ✅ `scrape_user_videos(username, max_videos)` - Get list of videos

## Configuration

### Playwright Method Settings

```env
# Cookie for authentication (recommended)
TIKTOK_COOKIE=your_mstoken_here

# Proxy (optional)
TIKTOK_PROXY=http://proxy:port

# Locale/timezone
TIKTOK_LOCALE=id-ID
TIKTOK_TIMEZONE_ID=Asia/Jakarta
```

### HTTP Method Settings

```env
# Cookie (full cookie string including sessionid)
TIKTOK_COOKIE=sessionid=xxx; msToken=yyy; ...

# Proxy (optional, uses httpx format)
TIKTOK_PROXY=http://proxy:port
```

## When Each Method is Used

### Playwright is Used When:
- ✅ Sessions initialize successfully
- ✅ No blocking/detection errors
- ✅ System has all Playwright dependencies

**Advantages:**
- Gets actual video download URLs
- More complete data
- Handles JavaScript rendering

### HTTP is Used When:
- ⚠️ Playwright initialization fails
- ⚠️ Playwright gets blocked by TikTok
- ⚠️ "Empty response" or bot detection errors

**Advantages:**
- No browser dependencies needed
- Lighter weight
- Less detectable (no automation markers)
- More resilient to TikTok updates

## Troubleshooting

### Check Which Method is Active

```python
scraper = UnifiedTikTokScraper()
await scraper.initialize()
print(f"Using method: {scraper.current_method}")
# Output: "playwright" or "http"
```

### Force HTTP Method

If you want to use HTTP method only, you can modify the code or just don't install Playwright dependencies.

### Get Better Results

1. **Add TikTok Cookie** - Both methods work better with authentication
   ```env
   TIKTOK_COOKIE=sessionid=...; msToken=...
   ```

2. **Use Residential Proxy** - Reduces detection risk
   ```env
   TIKTOK_PROXY=http://username:password@proxy:port
   ```

3. **Match Proxy Region** - Set locale/timezone to match proxy location
   ```env
   TIKTOK_LOCALE=en-US
   TIKTOK_TIMEZONE_ID=America/New_York
   ```

## Testing

### Test Unified Scraper

```bash
# In Docker
sudo docker compose run --rm worker python app/scraper_unified.py

# Locally
python app/scraper_unified.py
```

### Test Playwright Only

```bash
sudo docker compose run --rm worker python app/scraper.py
```

### Test HTTP Only

```bash
sudo docker compose run --rm worker python app/scraper_http.py
```

## Logs

The scraper logs which method it's using:

```
[INFO] Attempting to initialize Playwright scraper...
[INFO] ✓ Playwright scraper initialized successfully
```

Or if fallback occurs:

```
[WARNING] Playwright scraper failed to initialize: ...
[INFO] Falling back to HTTP scraper...
[INFO] ✓ HTTP scraper initialized successfully (fallback mode)
```

During operation:

```
[WARNING] get_user_profile(username): Playwright blocked, switching to HTTP
[INFO] Switched to HTTP scraper for get_user_profile
```

## Limitations

### HTTP Method Limitations

The HTTP scraper has some limitations:
- ❌ Cannot get direct video download URLs (no `get_video_download_url()`)
- ⚠️ May get less complete data in some cases
- ⚠️ Relies on TikTok's HTML structure (may break if TikTok changes it)

### Playwright Method Limitations

- ❌ Requires more system resources
- ❌ More detectable by TikTok
- ❌ Needs browser dependencies installed

## Best Practices

1. **Let automatic fallback work** - Don't disable it
2. **Add cookie for both methods** - Improves success rate
3. **Monitor logs** - Check which method is being used
4. **Use proxy** - Especially if scraping large volumes
5. **Respect rate limits** - Don't scrape too aggressively

## Architecture

```
┌─────────────────────────────────────┐
│   UnifiedTikTokScraper              │
│   (app/scraper_unified.py)          │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────┐
│ TikTokScraper│  │TikTokHTTP    │
│ (Playwright) │  │Scraper       │
│ scraper.py   │  │scraper_http.py│
└─────────────┘  └──────────────┘
      │                 │
      ▼                 ▼
  TikTokApi         httpx + BS4
  (Browser)         (Direct HTTP)
```

## Summary

✅ **Automatic fallback** ensures high reliability
✅ **Playwright first** for best quality data
✅ **HTTP fallback** when Playwright is blocked
✅ **Easy to use** - same interface for both methods
✅ **Well logged** - know which method is being used

The unified scraper gives you the best of both worlds!
