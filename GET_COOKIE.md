# How to Get TikTok Session Cookie

## Why You Need This
TikTok detects bots and blocks automated scraping. Using a valid session cookie from a logged-in account makes your scraper appear as a legitimate user.

## Step-by-Step Guide

### Method 1: Chrome/Edge

1. **Open Chrome/Edge** and go to https://www.tiktok.com

2. **Login to your TikTok account**

3. **Open Developer Tools**
   - Press `F12` or
   - Right-click → Inspect

4. **Go to Application Tab**
   - Click "Application" at the top
   - In left sidebar: Storage → Cookies → https://www.tiktok.com

5. **Find the Cookie**
   - Look for `sessionid` or `ms_token`
   - Click on it to see the value

6. **Copy the Value**
   - Copy the entire value (it's a long string)

7. **Add to .env**
   ```bash
   TIKTOK_COOKIE=your_copied_value_here
   ```

### Method 2: Firefox

1. **Open Firefox** and go to https://www.tiktok.com

2. **Login to your TikTok account**

3. **Open Developer Tools**
   - Press `F12` or
   - Right-click → Inspect Element

4. **Go to Storage Tab**
   - Click "Storage" at the top
   - In left sidebar: Cookies → https://www.tiktok.com

5. **Find the Cookie**
   - Look for `sessionid` or `ms_token`
   - Double-click the Value column to select

6. **Copy and Add to .env**
   ```bash
   TIKTOK_COOKIE=your_copied_value_here
   ```

### Method 3: Using Browser Extension (Easy)

1. **Install Cookie Editor Extension**
   - Chrome: [Cookie Editor](https://chrome.google.com/webstore/detail/cookie-editor)
   - Firefox: [Cookie Editor](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/)

2. **Go to TikTok and Login**

3. **Click Extension Icon**

4. **Find and Copy Cookie**
   - Search for `sessionid` or `ms_token`
   - Copy the value

5. **Add to .env**

## Example

Your cookie should look something like this:
```bash
TIKTOK_COOKIE=sessionid%3D1234567890abcdef1234567890abcdef%3B
```

## Important Notes

⚠️ **Security:**
- Don't share your cookie with anyone
- Don't commit .env file to git
- Cookies can access your account

⏰ **Expiration:**
- Cookies expire after some time (usually 30-90 days)
- If scraper stops working, get a new cookie
- You'll know it expired if you see bot detection errors again

🔄 **Refresh:**
- If cookie expires: clear browser cookies, login again, get new cookie
- Update .env with new value
- Restart docker containers

## Testing

After adding cookie:

```bash
# Restart services
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs -f worker

# Should see: "TikTok API initialized successfully"
```

## Troubleshooting

### Still Getting Bot Detection
- Make sure you copied the ENTIRE cookie value
- Try using `ms_token` instead of `sessionid`
- Combine with proxy: `TIKTOK_PROXY=http://proxy:port`
- Try headless=false: `TIKTOK_HEADLESS=false`

### Cookie Format Errors
- Remove any spaces
- Make sure no line breaks
- Should be one continuous string

### Multiple Cookies
You can try multiple session tokens:
```bash
TIKTOK_COOKIE=token1,token2,token3
```

## Alternative: Create New Account

If you don't want to use your main account:
1. Create a new TikTok account
2. Add some activity (watch videos, like, follow)
3. Wait a day or two
4. Then get the cookie from this account

This keeps your main account safe while still avoiding bot detection.
