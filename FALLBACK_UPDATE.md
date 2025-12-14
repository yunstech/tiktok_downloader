# Latest Updates - Scraper Fallback System

## 📅 Update Summary

**Date:** Latest Update  
**Feature:** Dual-Method Scraper with Automatic Fallback

## 🎯 What's New

### 1. Dual Scraping Methods

The scraper now supports **two methods** of scraping TikTok:

1. **Playwright Method** (`app/scraper.py`)
   - Browser automation via TikTokApi
   - Best for getting complete data and video URLs
   - Primary method, tried first

2. **HTTP Method** (`app/scraper_http.py`)
   - Direct HTTP requests + HTML parsing
   - Lightweight, no browser needed
   - Fallback method when Playwright fails

### 2. Unified Scraper (`app/scraper_unified.py`)

New unified scraper that combines both methods:
- ✅ Tries Playwright first
- ✅ Automatically falls back to HTTP if blocked
- ✅ Detects bot detection errors and switches methods
- ✅ Seamless switching during operation
- ✅ Well-logged for debugging

### 3. Updated Worker

`app/worker.py` now uses `UnifiedTikTokScraper`:
```python
from app.scraper_unified import UnifiedTikTokScraper

class Worker:
    def __init__(self):
        self.scraper = UnifiedTikTokScraper()  # Auto fallback!
```

### 4. New Dependencies

Added to `requirements.txt`:
```
beautifulsoup4==4.12.2
jmespath==1.0.1
lxml==4.9.3
```

These are needed for the HTTP scraper's HTML parsing.

## 📖 New Documentation

### 1. `SCRAPER_FALLBACK.md`
Complete guide to the fallback system:
- How it works
- Configuration
- When each method is used
- Testing instructions
- Troubleshooting

### 2. Updated `README.md`
- Added fallback system to features
- Updated project structure
- Enhanced TikTok detection troubleshooting
- Links to new documentation

## 🔧 How It Works

### Initialization Flow

```
┌─────────────────────────────┐
│ UnifiedTikTokScraper        │
│ .initialize()               │
└──────────┬──────────────────┘
           │
           ▼
    Try Playwright
           │
    ┌──────┴──────┐
    │             │
 Success      Failed
    │             │
    │             ▼
    │      Try HTTP Scraper
    │             │
    │      ┌──────┴──────┐
    │      │             │
    │   Success      Failed
    │      │             │
    ▼      ▼             ▼
  Ready   Ready      Error
```

### Operation Flow

```
User Request
     ↓
Try Playwright
     ↓
   ┌─┴─┐
 OK?   Bot Detection?
   │         │
   │         ▼
   │    Switch to HTTP
   │         │
   ↓         ↓
  Return  Return
  Result  Result
```

## 🚀 Usage

No changes needed! The system works automatically:

```python
# This now uses unified scraper with automatic fallback
scraper = UnifiedTikTokScraper()
await scraper.initialize()

# If Playwright fails, HTTP scraper kicks in automatically
profile = await scraper.get_user_profile("username")
videos = await scraper.scrape_user_videos("username", max_videos=10)
```

## 🧪 Testing

### Test the Unified Scraper

```bash
# Test in Docker
sudo docker compose run --rm worker python app/scraper_unified.py

# Test locally
python app/scraper_unified.py
```

### Test Individual Scrapers

```bash
# Test Playwright only
python app/scraper.py

# Test HTTP only
python app/scraper_http.py
```

## 📊 What Happens in Production

### Scenario 1: Playwright Works
```
[INFO] Attempting to initialize Playwright scraper...
[INFO] ✓ Playwright scraper initialized successfully
[INFO] get_user_profile(tiktok): Trying Playwright scraper
[INFO] Retrieved profile for user: tiktok
```

### Scenario 2: Playwright Blocked
```
[WARNING] Playwright scraper failed to initialize: EmptyResponseException
[INFO] Falling back to HTTP scraper...
[INFO] ✓ HTTP scraper initialized successfully (fallback mode)
[INFO] get_user_profile(tiktok): Using HTTP scraper (already in fallback mode)
[INFO] Retrieved profile for user: tiktok
```

### Scenario 3: Playwright Works Then Gets Blocked
```
[INFO] ✓ Playwright scraper initialized successfully
[INFO] get_user_profile(user1): Trying Playwright scraper
[INFO] Retrieved profile for user: user1
[WARNING] scrape_user_videos(user2): Playwright blocked, switching to HTTP
[INFO] Switched to HTTP scraper for scrape_user_videos
[INFO] Scraped 25 videos for user: user2
```

## 🎯 Benefits

1. **Higher Reliability**
   - If one method fails, the other kicks in
   - No complete failures due to bot detection

2. **No Manual Intervention**
   - Automatic switching
   - No need to restart or reconfigure

3. **Better User Experience**
   - Jobs complete successfully even with detection
   - Users get their videos regardless of method

4. **Flexibility**
   - Can use either method
   - Easy to test both
   - Can force one method if needed

## ⚙️ Configuration

Both methods use the same configuration:

```env
# Cookie (helps both methods)
TIKTOK_COOKIE=sessionid=...; msToken=...

# Proxy (optional for both)
TIKTOK_PROXY=http://proxy:port

# Locale/timezone (Playwright mainly)
TIKTOK_LOCALE=id-ID
TIKTOK_TIMEZONE_ID=Asia/Jakarta
```

## 🐛 Troubleshooting

### Check Which Method is Active

Look at worker logs:
```bash
sudo docker compose logs -f worker
```

You'll see:
- `Using method: playwright` - Playwright is active
- `Using method: http` - HTTP scraper is active
- `Switched to HTTP scraper` - Fallback occurred

### Force Rebuild

After pulling updates:
```bash
sudo docker compose down
sudo docker compose up -d --build
```

### Test Both Methods

```bash
# This will test initialization and basic scraping
sudo docker compose run --rm worker python app/scraper_unified.py
```

## 📚 Related Documentation

- [`SCRAPER_FALLBACK.md`](SCRAPER_FALLBACK.md) - Complete fallback system guide
- [`TIKTOK_DETECTION.md`](TIKTOK_DETECTION.md) - Bot detection troubleshooting
- [`README.md`](README.md) - Main documentation

## 🎉 Summary

You now have a **resilient, self-healing scraper** that:
- ✅ Tries the best method first
- ✅ Automatically falls back if blocked
- ✅ Continues working despite detection
- ✅ Requires no manual intervention
- ✅ Is well-documented and tested

Just pull the updates, rebuild, and you're good to go! 🚀

```bash
git pull
sudo docker compose down
sudo docker compose up -d --build
```
