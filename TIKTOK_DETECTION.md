# TikTok Bot Detection - Solutions

## Problem
TikTok detects automated scraping and returns empty responses with the message:
```
TikTok returned an empty response. They are detecting you're a bot
```

## Solutions Implemented

### 1. Configurable Headless Mode
Set `TIKTOK_HEADLESS=false` in your `.env` file to run browser in non-headless mode with virtual display.

```bash
TIKTOK_HEADLESS=false
```

### 2. Proxy Support
Use a proxy to avoid IP-based detection:

```bash
TIKTOK_PROXY=http://proxy.example.com:8080
# or with authentication
TIKTOK_PROXY=http://username:password@proxy.example.com:8080
```

### 3. Browser Context Options
The scraper now uses realistic browser settings:
- Real viewport size (1920x1080)
- Genuine User-Agent string
- US locale and timezone
- Better browser fingerprinting

## Recommended Solutions (in order)

### Option 1: Get TikTok Session Cookie (Best)
This is the most reliable method:

1. **Open TikTok in your browser** (Chrome/Firefox)
2. **Login to your account**
3. **Open Developer Tools** (F12)
4. **Go to Application/Storage tab**
5. **Find Cookies** → `www.tiktok.com`
6. **Copy the `sessionid` or `ms_token` cookie value**
7. **Add to .env:**
   ```bash
   TIKTOK_COOKIE=your_cookie_value_here
   ```

### Option 2: Use Residential Proxy
Use a residential proxy service (not datacenter):

```bash
# Popular proxy services:
# - BrightData (formerly Luminati)
# - Smartproxy
# - Oxylabs
# - IPRoyal

TIKTOK_PROXY=http://user:pass@proxy.provider.com:port
```

### Option 3: Disable Headless Mode
Run browser with visible display (slower but more reliable):

```bash
TIKTOK_HEADLESS=false
```

### Option 4: Reduce Request Rate
Add delays between requests (implemented with `sleep_after=3`).

## Testing Your Configuration

1. **Update your `.env` file:**
   ```bash
   TIKTOK_HEADLESS=false
   TIKTOK_COOKIE=your_session_cookie
   # or
   TIKTOK_PROXY=http://proxy:port
   ```

2. **Rebuild and restart:**
   ```bash
   sudo docker compose down
   sudo docker compose up -d --build
   ```

3. **Test with bot:**
   - Send a username to your Telegram bot
   - Check logs: `sudo docker compose logs -f worker`

4. **Monitor for success:**
   ```bash
   # Should see:
   # "TikTok API initialized successfully"
   # "Retrieved profile for user: username"
   # "Scraped X videos for user: username"
   ```

## Common Issues & Fixes

### Issue: Still getting detected
**Solution:** Combine multiple methods:
```bash
TIKTOK_COOKIE=your_cookie
TIKTOK_PROXY=http://proxy:port
TIKTOK_HEADLESS=false
```

### Issue: Xvfb display errors
**Solution:** Ensure Docker has enough resources:
```bash
# Add to docker-compose.yml worker service:
deploy:
  resources:
    limits:
      memory: 2G
```

### Issue: Proxy connection errors
**Solution:** Test proxy separately:
```bash
curl -x http://proxy:port https://www.tiktok.com
```

### Issue: Cookie expired
**Solution:** Cookies expire. Get a fresh one:
- Clear browser cookies
- Login to TikTok again
- Get new session cookie
- Update .env

## Alternative: Use TikTok API (Official)
If scraping becomes too difficult, consider:
- TikTok Official API (limited features)
- TikTok for Developers program
- Paid scraping services

## Rate Limiting
To avoid detection:
- Don't scrape more than 50-100 videos per hour
- Add random delays between requests
- Use multiple proxies/sessions
- Rotate user agents

## Legal Notice
⚠️ **Important:** Web scraping may violate TikTok's Terms of Service. Use responsibly and consider:
- Only scraping public content
- Respecting robots.txt
- Not overloading servers
- Using official APIs when available

## Best Practices
1. ✅ Use authenticated session (cookie)
2. ✅ Use residential proxy
3. ✅ Add random delays
4. ✅ Limit request rate
5. ✅ Monitor for errors
6. ✅ Have fallback strategies
7. ❌ Don't scrape excessively
8. ❌ Don't bypass rate limits aggressively
