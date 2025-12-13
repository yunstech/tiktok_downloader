# Quick Setup Guide - TikTok Cookie

## 🚨 Current Issue
You're seeing this error:
```
TikTok returned an empty response. They are detecting you're a bot
```

## ✅ Quick Fix (5 minutes)

### Step 1: Get TikTok Cookie

**Chrome/Edge:**
1. Open https://www.tiktok.com in your browser
2. Login to TikTok
3. Press **F12** (Developer Tools)
4. Click **Application** tab
5. Left sidebar: **Cookies** → `https://www.tiktok.com`
6. Find `sessionid` and copy the **Value**

**Firefox:**
1. Open https://www.tiktok.com
2. Login to TikTok
3. Press **F12**
4. Click **Storage** tab
5. **Cookies** → `https://www.tiktok.com`
6. Find `sessionid` and copy the **Value**

### Step 2: Add to .env File

On your server:
```bash
cd ~/personal/tiktok_downloader
nano .env
```

Add this line (replace with your actual cookie):
```bash
TIKTOK_COOKIE=your_sessionid_value_here
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Restart Services

```bash
sudo docker compose down
sudo docker compose up -d
```

### Step 4: Test

```bash
# Watch logs
sudo docker compose logs -f worker

# Should see:
# "TikTok API initialized successfully"
# "Retrieved profile for user: username"
```

## 🧪 Test Your Cookie

You can test if your cookie works before deploying:

```bash
# Run test script
sudo docker compose run --rm worker python test_cookie.py
```

This will:
- ✅ Check if cookie is set
- ✅ Test TikTok API connection
- ✅ Try to fetch a profile
- ✅ Verify scraping works

## 📊 Expected Results

**Before (with error):**
```
❌ TikTok returned an empty response
```

**After (working):**
```
✅ TikTok API initialized successfully
✅ Retrieved profile for user: username
✅ Scraped X videos for user: username
```

## 🔄 Cookie Expires?

If it stops working after a while:
1. Get a fresh cookie (repeat Step 1)
2. Update .env (repeat Step 2)
3. Restart services (repeat Step 3)

## 🆘 Still Not Working?

Try additional options in .env:

```bash
TIKTOK_COOKIE=your_sessionid_here
TIKTOK_HEADLESS=false
TIKTOK_PROXY=http://your-proxy:port
```

See **TIKTOK_DETECTION.md** for detailed troubleshooting.

## ⚡ Quick Commands

```bash
# Edit .env
nano .env

# Restart
sudo docker compose restart worker

# View logs
sudo docker compose logs -f worker

# Test cookie
sudo docker compose run --rm worker python test_cookie.py
```

---

**Need help?** Check GET_COOKIE.md for detailed instructions with screenshots.
