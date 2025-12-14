# TikTok Scraper Setup Guide

## 🚀 Quick Start

This guide will help you configure the TikTok scraper to avoid bot detection and maximize success rates.

## 🍪 Getting TikTok Cookies (REQUIRED for best results)

TikTok uses aggressive bot detection. Using a valid session cookie is **highly recommended** to avoid getting blocked.

### Method 1: Using Chrome DevTools (Recommended)

1. **Open TikTok in your browser**
   - Go to https://www.tiktok.com
   - Log in to your TikTok account (optional but helps)

2. **Open Developer Tools**
   - Press `F12` or `Ctrl+Shift+I` (Windows/Linux)
   - Press `Cmd+Option+I` (Mac)

3. **Navigate to Cookies**
   - Click on the **Application** tab (Chrome) or **Storage** tab (Firefox)
   - In the left sidebar, expand **Cookies**
   - Click on `https://www.tiktok.com`

4. **Copy the session cookie**
   - Look for one of these cookies (in order of preference):
     * `sessionid` (best option)
     * `msToken` or `ms_token`
     * `tt_chain_token`
   - Double-click on the **Value** column and copy the entire value
   - It should be a long string like: `7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3`

5. **Add to your `.env` file**
   ```bash
   TIKTOK_COOKIE=your_cookie_value_here
   ```

### Method 2: Using Browser Extension (Easy)

1. Install **Cookie Editor** extension:
   - Chrome: https://chrome.google.com/webstore
   - Firefox: https://addons.mozilla.org/firefox

2. Go to https://www.tiktok.com

3. Click the Cookie Editor extension icon

4. Find `sessionid` and copy its value

5. Paste into `.env` file

## ⚙️ Configuration Options

### Basic Configuration (.env file)

```bash
# TikTok Configuration
TIKTOK_COOKIE=your_sessionid_here          # Session cookie (HIGHLY RECOMMENDED)
TIKTOK_PROXY=http://proxy:port             # Optional proxy (residential recommended)
TIKTOK_HEADLESS=false                      # Set to false to see browser (helps with debugging)
```

### Headless vs Headed Mode

**Headless Mode (default: `true`)**
- Browser runs in background (no window visible)
- Faster and uses less resources
- ⚠️ More likely to be detected as bot

**Headed Mode (`false`)**
- Browser window is visible
- Slower but more human-like
- ✅ Better for avoiding bot detection
- Recommended when testing or if getting blocked

To use headed mode:
```bash
TIKTOK_HEADLESS=false
```

## 🌐 Using Proxies

TikTok may block datacenter IPs. Consider using residential proxies for better success.

### Proxy Format

```bash
# HTTP Proxy
TIKTOK_PROXY=http://username:password@proxy.example.com:8080

# SOCKS5 Proxy
TIKTOK_PROXY=socks5://username:password@proxy.example.com:1080

# No authentication
TIKTOK_PROXY=http://proxy.example.com:8080
```

### Recommended Proxy Providers

- **Residential Proxies** (best for TikTok):
  - Bright Data
  - Smartproxy
  - Oxylabs
  - IPRoyal

- Avoid datacenter proxies - TikTok blocks them aggressively

## 🔧 Testing Your Setup

Use the built-in test script to verify your configuration:

```bash
# Test with a specific username
docker compose exec worker python test_scraper.py --username tiktok

# Test with different settings
docker compose exec worker python test_scraper.py --username tiktok --max-videos 5
```

## 🐛 Troubleshooting

### Problem: "Bot detection error" / "Empty response"

**Solutions:**
1. ✅ Add a valid `TIKTOK_COOKIE` to `.env`
2. ✅ Set `TIKTOK_HEADLESS=false` to use headed mode
3. ✅ Use a residential proxy
4. ✅ Reduce scraping speed (already implemented with delays)
5. ✅ Try a different browser: change `browser="chromium"` to `browser="webkit"` in `app/scraper.py`

### Problem: "No videos found" but profile shows video count > 0

**Causes:**
- Account may be private
- Geographic restrictions
- Bot detection blocking video list (but not profile)

**Solutions:**
1. Use a valid session cookie from a logged-in account
2. Add a proxy from the same region as the target user
3. Switch to HTTP fallback scraper (automatic)

### Problem: Scraper is too slow

**Solutions:**
1. Set `TIKTOK_HEADLESS=true` (faster)
2. Reduce `max_videos` parameter
3. Use multiple worker instances (advanced)

### Problem: Getting rate limited

**Solutions:**
1. Increase delays between requests (edit `app/scraper.py`)
2. Use rotating proxies
3. Reduce concurrent scraping jobs

## 📊 Success Rate Optimization

### Best Configuration (High Success Rate)

```bash
# .env
TIKTOK_COOKIE=your_valid_sessionid       # ⭐ MOST IMPORTANT
TIKTOK_PROXY=http://residential-proxy    # ⭐ Use residential IP
TIKTOK_HEADLESS=false                    # More human-like
```

### Fallback Configuration (Medium Success Rate)

```bash
# .env
TIKTOK_COOKIE=your_valid_sessionid       # ⭐ CRITICAL
TIKTOK_PROXY=                            # No proxy
TIKTOK_HEADLESS=true                     # Headless mode
```

The scraper will automatically fall back to HTTP scraper if Playwright fails.

## 🔒 Cookie Expiry

Session cookies typically expire after:
- **30 days** of inactivity
- When you log out from TikTok
- When TikTok detects suspicious activity

**Recommendation:** Update your cookie monthly or when you see authentication errors.

## 📝 Advanced Tips

### Multiple Accounts
You can use different cookies for different scraping jobs by storing them in Redis and passing them per-request (requires code modification).

### Cookie Rotation
For high-volume scraping, rotate between multiple valid session cookies to distribute requests.

### Browser Fingerprinting
The scraper already includes:
- ✅ Realistic User-Agent
- ✅ Browser headers (sec-ch-ua, etc.)
- ✅ Viewport and timezone
- ✅ Human-like delays

## 🆘 Still Having Issues?

1. Check logs: `docker compose logs -f worker`
2. Enable debug mode: Set `LOG_LEVEL=DEBUG` in `.env`
3. Test with a known-working username (e.g., `@tiktok`, `@charlidamelio`)
4. Verify your cookie is still valid by logging into TikTok in your browser

## 📚 Related Files

- `app/scraper.py` - Playwright scraper implementation
- `app/scraper_http.py` - HTTP fallback scraper
- `app/scraper_unified.py` - Automatic fallback orchestrator
- `.env.example` - Configuration template
