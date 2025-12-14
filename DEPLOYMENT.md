# Quick Deployment Guide

This guide will help you deploy the TikTok Scraper with the new fallback system.

## 🚀 Quick Start (5 Minutes)

### 1. Update Code

```bash
# Navigate to project directory
cd /path/to/tiktok-scrapper-download

# Pull latest changes
git pull origin main
```

### 2. Configure Environment

```bash
# Edit .env file
nano .env
```

**Minimum required:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**Recommended for better results:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TIKTOK_COOKIE=sessionid=xxx; msToken=yyy
TIKTOK_PROXY=http://proxy:port
```

### 3. Deploy with Docker

```bash
# Stop existing containers
sudo docker compose down

# Build and start with new changes
sudo docker compose up -d --build

# Watch logs
sudo docker compose logs -f
```

That's it! The scraper will now automatically use fallback if needed.

## 📋 Detailed Deployment Steps

### Prerequisites

- Docker & Docker Compose installed
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- (Optional) TikTok session cookie
- (Optional) Proxy service

### Step 1: Clone or Update Repository

**First time:**
```bash
git clone <repository-url>
cd tiktok-scrapper-download
```

**Updating existing:**
```bash
cd tiktok-scrapper-download
git pull origin main
```

### Step 2: Configure Environment Variables

```bash
# Copy example if first time
cp .env.example .env

# Edit configuration
nano .env
```

**Basic Configuration:**
```env
# Required
TELEGRAM_BOT_TOKEN=123456:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional but recommended
TELEGRAM_ADMIN_IDS=your_user_id
```

**Advanced Configuration (Anti-Detection):**
```env
# TikTok Cookie (helps avoid detection)
TIKTOK_COOKIE=sessionid=abc123; msToken=xyz789

# Proxy (use residential proxy for best results)
TIKTOK_PROXY=http://username:password@proxy:port

# Locale/Timezone (match your proxy region)
TIKTOK_LOCALE=en-US
TIKTOK_TIMEZONE_ID=America/New_York

# Headless mode (false may help in some cases)
TIKTOK_HEADLESS=true
```

### Step 3: Deploy Services

```bash
# Stop existing containers (if any)
sudo docker compose down

# Build images with latest changes
sudo docker compose build

# Start all services in background
sudo docker compose up -d

# Verify all services are running
sudo docker compose ps
```

Expected output:
```
NAME                   SERVICE   STATUS    PORTS
tiktok-bot             bot       running
tiktok-api             api       running   0.0.0.0:8000->8000/tcp
tiktok-worker          worker    running
tiktok-redis           redis     running   6379/tcp
```

### Step 4: Verify Deployment

**Check logs:**
```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f worker

# Last 50 lines
sudo docker compose logs --tail=50 worker
```

**Look for:**
```
[INFO] Attempting to initialize Playwright scraper...
[INFO] ✓ Playwright scraper initialized successfully
```

Or fallback mode:
```
[WARNING] Playwright scraper failed to initialize: ...
[INFO] Falling back to HTTP scraper...
[INFO] ✓ HTTP scraper initialized successfully (fallback mode)
```

**Test bot:**
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Try `/scrape username`

### Step 5: Monitor Operation

**Check worker status:**
```bash
sudo docker compose logs -f worker
```

**Check bot responses:**
```bash
sudo docker compose logs -f bot
```

**Check API health:**
```bash
curl http://localhost:8000/health
```

**Check Redis:**
```bash
sudo docker compose exec redis redis-cli ping
# Should return: PONG
```

## 🔧 Configuration Options

### Minimal Configuration
```env
TELEGRAM_BOT_TOKEN=your_token
```
- Works with automatic fallback
- May hit rate limits
- HTTP scraper will be used if Playwright fails

### Recommended Configuration
```env
TELEGRAM_BOT_TOKEN=your_token
TIKTOK_COOKIE=sessionid=xxx; msToken=yyy
```
- Better success rate
- Both methods work better with auth
- Less likely to be rate limited

### Maximum Reliability
```env
TELEGRAM_BOT_TOKEN=your_token
TIKTOK_COOKIE=sessionid=xxx; msToken=yyy
TIKTOK_PROXY=http://user:pass@proxy:port
TIKTOK_LOCALE=en-US
TIKTOK_TIMEZONE_ID=America/New_York
```
- Best for high volume scraping
- Least detection risk
- Most reliable results

## 🧪 Testing the Deployment

### Test 1: Basic Functionality

```bash
# Test the unified scraper directly
sudo docker compose run --rm worker python app/scraper_unified.py
```

Should see:
```
✓ Initialized with method: playwright
Fetching profile for @tiktok...
✓ Profile: TikTok (123M followers)
```

### Test 2: Bot Commands

In Telegram, send:
1. `/start` - Should get welcome message
2. `/help` - Should show command list
3. `/scrape tiktok` - Should start scraping job

### Test 3: API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List jobs
curl http://localhost:8000/jobs
```

### Test 4: Check Which Method is Active

```bash
# Watch worker logs
sudo docker compose logs -f worker | grep -i "method\|scraper"
```

## 🐛 Troubleshooting Deployment

### Services Won't Start

```bash
# Check for port conflicts
sudo netstat -tulpn | grep -E '6379|8000'

# Check Docker status
sudo docker ps -a

# Check service logs
sudo docker compose logs
```

### Playwright Initialization Fails

**Expected behavior:** System automatically falls back to HTTP scraper

```bash
# Verify fallback is working
sudo docker compose logs worker | grep -i "fallback\|http scraper"
```

Should see:
```
[INFO] Falling back to HTTP scraper...
[INFO] ✓ HTTP scraper initialized successfully (fallback mode)
```

### HTTP Scraper Also Fails

**Check cookie:**
```bash
# Verify cookie is set
sudo docker compose exec worker env | grep TIKTOK_COOKIE
```

**Test cookie:**
```bash
sudo docker compose run --rm worker python test_cookie.py
```

### Bot Not Responding

```bash
# Check bot logs
sudo docker compose logs bot

# Verify token
sudo docker compose exec bot env | grep TELEGRAM_BOT_TOKEN

# Restart bot
sudo docker compose restart bot
```

### Videos Not Downloading

```bash
# Check worker logs
sudo docker compose logs worker

# Check downloads directory
ls -la downloads/

# Check disk space
df -h

# Check Redis queue
sudo docker compose exec redis redis-cli
> LLEN download_queue
> LLEN scrape_queue
```

## 🔄 Updating the System

### Pull Latest Changes

```bash
cd tiktok-scrapper-download
git pull origin main
```

### Rebuild and Restart

```bash
# Stop services
sudo docker compose down

# Rebuild with changes
sudo docker compose up -d --build

# Verify
sudo docker compose ps
sudo docker compose logs -f
```

### Clean Start (If Needed)

```bash
# Stop and remove containers
sudo docker compose down

# Remove volumes (WARNING: deletes Redis data)
sudo docker compose down -v

# Remove images
sudo docker compose down --rmi all

# Rebuild everything
sudo docker compose up -d --build
```

## 📊 Monitoring

### View All Logs

```bash
sudo docker compose logs -f
```

### View Specific Service

```bash
sudo docker compose logs -f worker
sudo docker compose logs -f bot
sudo docker compose logs -f api
```

### Follow Logs with Filters

```bash
# Only errors
sudo docker compose logs -f | grep -i error

# Only scraper activity
sudo docker compose logs -f worker | grep -i "scraper\|video"

# Only bot messages
sudo docker compose logs -f bot | grep -i "message\|command"
```

### Check Resource Usage

```bash
# Container stats
sudo docker stats

# Disk usage
sudo docker compose exec worker df -h

# Redis memory usage
sudo docker compose exec redis redis-cli INFO memory
```

## 🎯 Post-Deployment Checklist

- [ ] All services running (`docker compose ps`)
- [ ] Worker logs show scraper initialized
- [ ] Bot responds to `/start`
- [ ] API health check returns OK
- [ ] Redis is connected
- [ ] Can create a test job
- [ ] Videos download successfully
- [ ] Bot sends videos to user

## 📚 Next Steps

1. **Get TikTok Cookie** - See [GET_COOKIE.md](GET_COOKIE.md)
2. **Configure Proxy** - See [TIKTOK_DETECTION.md](TIKTOK_DETECTION.md)
3. **Understand Fallback** - See [SCRAPER_FALLBACK.md](SCRAPER_FALLBACK.md)
4. **Monitor Logs** - Watch for which scraper method is used

## 🆘 Getting Help

If you encounter issues:

1. **Check logs** - Most issues are visible in logs
2. **Read error messages** - They usually indicate the problem
3. **Review documentation** - Check relevant .md files
4. **Test components** - Use test scripts to isolate issues

## 🎉 Success Indicators

Your deployment is successful when:

✅ All 4 services running (api, worker, bot, redis)  
✅ Worker shows "initialized successfully"  
✅ Bot responds to commands  
✅ Can scrape a user profile  
✅ Videos are downloaded  
✅ Bot sends videos to users  
✅ Logs show appropriate method (Playwright or HTTP)  

**Happy scraping!** 🚀
