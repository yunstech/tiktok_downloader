# Quick Reference - Scraper Fallback System

## 🚀 Quick Commands

```bash
# Deploy/Update
git pull && sudo docker compose down && sudo docker compose up -d --build

# Check Status
sudo docker compose ps

# View Logs
sudo docker compose logs -f worker

# Test Scraper
sudo docker compose run --rm worker python app/scraper_unified.py

# Check Which Method
sudo docker compose logs worker | grep -i "method\|initialized"

# Restart Services
sudo docker compose restart
```

## 📊 System Status

### ✅ Good Status
```
[INFO] ✓ Playwright scraper initialized successfully
Using method: playwright
```

### ⚠️ Fallback Status (Still Working!)
```
[INFO] ✓ HTTP scraper initialized successfully (fallback mode)
Using method: http
```

### ❌ Error Status
```
[ERROR] Failed to initialize any scraper method
```
**Fix:** Add TIKTOK_COOKIE and/or TIKTOK_PROXY

## 🔧 Configuration Presets

### Minimal (Will Use Fallback)
```env
TELEGRAM_BOT_TOKEN=your_token
```

### Recommended
```env
TELEGRAM_BOT_TOKEN=your_token
TIKTOK_COOKIE=sessionid=xxx; msToken=yyy
```

### Maximum Reliability
```env
TELEGRAM_BOT_TOKEN=your_token
TIKTOK_COOKIE=sessionid=xxx; msToken=yyy
TIKTOK_PROXY=http://user:pass@proxy:port
TIKTOK_LOCALE=en-US
TIKTOK_TIMEZONE_ID=America/New_York
```

## 🔍 Troubleshooting Matrix

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| "Playwright failed" | Expected | System auto-uses HTTP |
| "HTTP scraper fallback" | Normal | No action needed |
| "empty response" | Bot detected | Add cookie or proxy |
| "Both methods failed" | No auth | Add TIKTOK_COOKIE |
| Videos not downloading | Network/disk | Check logs, disk space |
| Bot not responding | Token/service | Check bot logs, restart |

## 📂 File Structure

```
app/
├── scraper.py          → Playwright (primary)
├── scraper_http.py     → HTTP (fallback)
├── scraper_unified.py  → Combines both ⭐
└── worker.py           → Uses unified scraper
```

## 🧪 Testing Commands

```bash
# Test unified (auto fallback)
python app/scraper_unified.py

# Test Playwright only
python app/scraper.py

# Test HTTP only
python app/scraper_http.py

# Test in Docker
sudo docker compose run --rm worker python app/scraper_unified.py
```

## 📈 Method Comparison

| Feature | Playwright | HTTP |
|---------|-----------|------|
| Speed | Slower | Faster |
| Resource | Heavy | Light |
| Detection | Higher | Lower |
| Data Quality | Best | Good |
| Dependencies | Many | Few |
| Video URLs | Yes | Limited |

## 🎯 When Each Method is Used

### Playwright Used When:
- ✅ Clean initialization
- ✅ No blocking errors
- ✅ System has dependencies

### HTTP Used When:
- ⚠️ Playwright init fails
- ⚠️ Bot detection occurs
- ⚠️ Timeout/connection errors

## 🔄 Fallback Flow

```
Start → Try Playwright → Success? ─Yes→ Use Playwright
                  │
                  No
                  ↓
              Try HTTP → Success? ─Yes→ Use HTTP
                  │
                  No
                  ↓
                Error
```

## 📝 Log Patterns

### Successful Operation
```
[INFO] Attempting to initialize Playwright scraper...
[INFO] ✓ Playwright scraper initialized successfully
[INFO] get_user_profile(tiktok): Trying Playwright scraper
[INFO] Retrieved profile for user: tiktok
```

### Fallback During Init
```
[WARNING] Playwright scraper failed to initialize
[INFO] Falling back to HTTP scraper...
[INFO] ✓ HTTP scraper initialized successfully
```

### Fallback During Operation
```
[INFO] ✓ Playwright scraper initialized successfully
[WARNING] scrape_user_videos: Playwright blocked, switching to HTTP
[INFO] Switched to HTTP scraper
```

## 🛡️ Anti-Detection Tips

1. **Add Cookie** (Most Important)
   ```env
   TIKTOK_COOKIE=sessionid=...; msToken=...
   ```

2. **Use Proxy** (Recommended)
   ```env
   TIKTOK_PROXY=http://proxy:port
   ```

3. **Match Region** (If Using Proxy)
   ```env
   TIKTOK_LOCALE=en-US
   TIKTOK_TIMEZONE_ID=America/New_York
   ```

4. **Rate Limiting** (Built-in)
   - Automatic delays between requests
   - Batch processing

## 📚 Documentation Files

| File | What It Explains |
|------|------------------|
| `SCRAPER_FALLBACK.md` | How fallback works |
| `ARCHITECTURE.md` | System design |
| `DEPLOYMENT.md` | How to deploy |
| `CHANGES_SUMMARY.md` | What changed |
| `GET_COOKIE.md` | How to get cookie |
| `TIKTOK_DETECTION.md` | Bot detection fixes |

## 💡 Pro Tips

1. **Let Fallback Work**
   - Don't disable it
   - System knows when to switch

2. **Monitor Logs**
   - Check which method is used
   - Watch for patterns

3. **Add Cookie**
   - Works with both methods
   - Significantly improves success

4. **Use Residential Proxy**
   - Best for high volume
   - Reduces detection

5. **Check Method**
   ```bash
   sudo docker compose logs worker | grep "method"
   ```

## ⚡ Emergency Commands

```bash
# Service not responding
sudo docker compose restart

# Need clean start
sudo docker compose down && sudo docker compose up -d

# Check if running
sudo docker compose ps

# See errors only
sudo docker compose logs | grep -i error

# Full logs last 100 lines
sudo docker compose logs --tail=100

# Stop everything
sudo docker compose down
```

## 🎯 Success Checklist

- [ ] Services running (docker compose ps)
- [ ] Scraper initialized (check logs)
- [ ] Bot responds to /start
- [ ] Can create test job
- [ ] Videos download
- [ ] Bot sends videos
- [ ] Know which method is active

## 📞 Quick Health Check

```bash
# 1. Services up?
sudo docker compose ps

# 2. Which scraper method?
sudo docker compose logs worker | grep "initialized successfully"

# 3. API working?
curl http://localhost:8000/health

# 4. Redis working?
sudo docker compose exec redis redis-cli ping

# 5. Bot token correct?
sudo docker compose exec bot env | grep TELEGRAM_BOT_TOKEN
```

## 🔗 Quick Links

- Main Docs: `README.md`
- Fallback Guide: `SCRAPER_FALLBACK.md`
- Deployment: `DEPLOYMENT.md`
- Get Cookie: `GET_COOKIE.md`
- Architecture: `ARCHITECTURE.md`

---

**Remember:** The fallback is automatic - just deploy and it works! 🚀
