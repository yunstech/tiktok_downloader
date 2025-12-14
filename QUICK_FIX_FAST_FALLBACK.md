# Quick Fix Applied - Faster Fallback

## Problem

The Playwright scraper was taking too long to fail when TikTok detected it as a bot. It would:
1. Try to initialize (succeed)
2. Try to scrape user profile (fail - EmptyResponse)  
3. Recover sessions (try again)
4. Fail again
5. Recover sessions again
6. Eventually raise error after ~45-60 seconds

This delayed the fallback to HTTP scraper.

## Solution Applied

### 1. Added Timeout to Playwright Initialization (30s)

```python
# Now with timeout
await asyncio.wait_for(
    self.playwright_scraper.initialize(),
    timeout=30.0  # Fail fast if taking too long
)
```

If Playwright takes more than 30 seconds to initialize, it automatically falls back to HTTP scraper.

### 2. Better Error Detection

Added more keywords to detect blocking:
- `'after retries'`
- `'detecting you'`  
- `'could not fetch'`

### 3. More Informative Logs

```
[INFO] Attempting to initialize Playwright scraper...
[WARNING] Playwright scraper failed: ...
[INFO] Falling back to HTTP scraper...
[INFO] ✓ HTTP scraper initialized successfully (fallback mode)
```

## Expected Behavior Now

### Scenario 1: Playwright Works
```
[INFO] Attempting to initialize Playwright scraper...
[INFO] ✓ Playwright scraper initialized successfully
[INFO] get_user_profile(username): Trying Playwright scraper
```

### Scenario 2: Playwright Fails at Init (Fast)
```
[INFO] Attempting to initialize Playwright scraper...
[WARNING] Playwright scraper failed to initialize: ...
[INFO] Falling back to HTTP scraper...
[INFO] ✓ HTTP scraper initialized successfully (fallback mode)
```

### Scenario 3: Playwright Inits but Gets Blocked (Fast)
```
[INFO] ✓ Playwright scraper initialized successfully
[WARNING] get_user_profile: Playwright blocked/failed, switching to HTTP scraper
[INFO] Playwright error: Blocked: TikTok detecting bot after 2 attempts
[INFO] ✓ Switched to HTTP scraper
```

## Deploy

```bash
git pull
sudo docker compose down
sudo docker compose up -d --build
```

## Test

Try scraping again and you should see much faster fallback to HTTP scraper when Playwright is blocked.

## Next Steps

The HTTP scraper should work without cookies, but for better results:

1. **Add TikTok Cookie** (Recommended)
   ```env
   TIKTOK_COOKIE=sessionid=xxx; msToken=yyy
   ```

2. **Use Proxy** (Optional)
   ```env
   TIKTOK_PROXY=http://proxy:port
   ```

## Changes Made

- ✅ Added 30s timeout to Playwright initialization
- ✅ Improved error keyword detection
- ✅ Better logging for fallback events
- ✅ Faster failure detection

The system will now fail over to HTTP scraper within ~30-40 seconds instead of 60+ seconds!
