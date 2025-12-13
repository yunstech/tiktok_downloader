# Visual Cookie Guide

## Chrome/Edge - Step by Step

```
1. Open TikTok and Login
   ┌─────────────────────────────────────┐
   │  https://www.tiktok.com            │
   │  [Login with your account]          │
   └─────────────────────────────────────┘

2. Press F12 (or Right-click → Inspect)
   ┌─────────────────────────────────────┐
   │  Browser opens Developer Tools     ││
   └─────────────────────────────────────┘

3. Click "Application" Tab
   ┌─────────────────────────────────────┐
   │ Elements Console Sources  >>>      ││
   │ [Application] ← Click this         ││
   └─────────────────────────────────────┘

4. Navigate to Cookies
   ┌──────────────┬──────────────────────┐
   │ Application  │                      │
   │ ├─ Storage   │                      │
   │ │  ├─ Cookies│                      │
   │ │  │  └─ https://www.tiktok.com ←  │
   └──────────────┴──────────────────────┘

5. Find "sessionid" Cookie
   ┌────────────────────────────────────────────┐
   │ Name          │ Value                      │
   ├───────────────┼────────────────────────────┤
   │ sessionid     │ 1a2b3c4d5e6f7g8h9i... ← Copy this! │
   │ tt_webid      │ ...                        │
   │ msToken       │ ...                        │
   └────────────────────────────────────────────┘

6. Copy the entire Value
   - Click on the Value cell
   - It will highlight
   - Ctrl+C to copy
   - Should be a long string like:
     1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7...
```

## Firefox - Step by Step

```
1. Open TikTok and Login
   Same as Chrome

2. Press F12
   Developer Tools open

3. Click "Storage" Tab
   ┌─────────────────────────────────────┐
   │ Inspector Console Debugger  >>>    ││
   │ [Storage] ← Click this             ││
   └─────────────────────────────────────┘

4. Navigate to Cookies
   ┌──────────────┬──────────────────────┐
   │ Storage      │                      │
   │ ├─ Cookies   │                      │
   │ │  └─ https://www.tiktok.com ←     │
   └──────────────┴──────────────────────┘

5. Find "sessionid"
   Same table view as Chrome

6. Double-click Value to select all, then Ctrl+C
```

## What Does It Look Like?

### ✅ Correct Cookie Format:
```
TIKTOK_COOKIE=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7
```

### ❌ Wrong Formats:
```
# Don't include the name
❌ TIKTOK_COOKIE=sessionid=1a2b3c4d5e...

# Don't add quotes
❌ TIKTOK_COOKIE="1a2b3c4d5e..."

# Don't add spaces
❌ TIKTOK_COOKIE= 1a2b3c4d5e...

# Don't use the cookie name
❌ TIKTOK_COOKIE=sessionid
```

## Add to .env File

```bash
# On your server
cd ~/personal/tiktok_downloader
nano .env

# Add this line at the end:
TIKTOK_COOKIE=paste_your_cookie_value_here

# Save: Ctrl+X, then Y, then Enter
```

## Full .env Example

```bash
# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True
API_BASE_URL=http://localhost:8000

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_IDS=123456789

# TikTok Configuration - ADD YOUR COOKIE HERE
TIKTOK_COOKIE=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7
TIKTOK_PROXY=
TIKTOK_HEADLESS=true

# Download Configuration
DOWNLOAD_PATH=./downloads
MAX_CONCURRENT_DOWNLOADS=3
VIDEO_QUALITY=highest

# Logging
LOG_LEVEL=INFO
```

## Verify It's Working

```bash
# Restart services
sudo docker compose down
sudo docker compose up -d

# Check logs (should see "initialized successfully")
sudo docker compose logs -f worker

# Or run test
sudo docker compose run --rm worker python test_cookie.py
```

## Common Mistakes

### Cookie Too Short
If your cookie is less than 30 characters, you probably copied the wrong thing.
- Should be 50-100+ characters long
- Look for the longest value in the sessionid row

### Cookie Has Spaces
Remove any spaces:
```bash
# Wrong
TIKTOK_COOKIE=abc def ghi

# Right
TIKTOK_COOKIE=abcdefghi
```

### Copied Cookie Name Instead of Value
Make sure you copy from the "Value" column, not the "Name" column!

## Need More Help?

See these guides:
- **QUICK_FIX.md** - Fastest solution
- **GET_COOKIE.md** - Detailed instructions
- **TIKTOK_DETECTION.md** - All solutions and alternatives

Or run the test script:
```bash
sudo docker compose run --rm worker python test_cookie.py
```
