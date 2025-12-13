# TikTok Scraper & Downloader Bot

A powerful TikTok scraper and downloader built with Python FastAPI, Redis, and Telegram Bot integration. This application allows users to scrape all videos from a TikTok profile and automatically download them.

## 🌟 Features

- 🔍 **Profile Scraping**: Search and scrape all videos from any TikTok user profile
- ⬇️ **Automatic Downloads**: Videos are automatically downloaded using Redis queue system
- 📦 **Batch Video Delivery**: Bot automatically sends videos to users in batches of 5
- 🤖 **Telegram Bot**: Easy-to-use Telegram bot interface
- 🚀 **FastAPI Backend**: High-performance REST API
- 📊 **Job Tracking**: Monitor scraping and download progress in real-time
- 🔄 **Async Processing**: Concurrent downloads with configurable limits
- 🐳 **Docker Support**: Easy deployment with Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Redis 7+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Optional: Docker & Docker Compose

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tiktok-scrapper-download
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
copy .env.example .env
```

Edit `.env` and set your values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_IDS=your_telegram_user_id
```

### 3. Option A: Run with Docker (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Option B: Run Locally

#### Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

#### Start Redis

```bash
# Windows (using WSL or Redis for Windows)
redis-server

# Linux/Mac
redis-server
```

#### Start Services

You'll need to run these in separate terminal windows:

```bash
# Terminal 1: Start FastAPI
python -m app.main

# Terminal 2: Start Worker
python -m app.worker

# Terminal 3: Start Telegram Bot
python -m app.bot
```

## 📖 Usage

### Using the Telegram Bot

1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Send a TikTok username (without @) to start scraping
4. **Videos will be automatically sent to you in batches of 5!** 📦
5. Use `/status <job_id>` to check progress
6. Use `/jobs` to see all your jobs

**Note**: After every 5 videos are downloaded, the bot will automatically send them to you. When all downloads are complete, any remaining videos (less than 5) will also be sent.

### Using the API

#### Start Scraping

```bash
POST http://localhost:8000/scrape
Content-Type: application/json

{
  "username": "tiktok",
  "max_videos": 50
}
```

#### Check Job Status

```bash
GET http://localhost:8000/job/{job_id}
```

#### List All Jobs

```bash
GET http://localhost:8000/jobs
```

## 🏗️ Architecture

```
┌─────────────────┐
│  Telegram Bot   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│      Redis      │◄────┤     Worker      │
│   Job Queue     │     │  (Scraper +     │
└─────────────────┘     │   Downloader)   │
                        └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │   Downloads/    │
                        │   {username}/   │
                        └─────────────────┘
```

## 📁 Project Structure

```
tiktok-scrapper-download/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── bot.py           # Telegram bot
│   ├── worker.py        # Background worker
│   ├── scraper.py       # TikTok scraper
│   ├── downloader.py    # Video downloader
│   ├── redis_client.py  # Redis client
│   ├── config.py        # Configuration
│   ├── models.py        # Data models
│   └── logger.py        # Logging setup
├── downloads/           # Downloaded videos
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker Compose config
├── Dockerfile          # Docker image
├── .env.example        # Example environment variables
└── README.md           # This file
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | FastAPI host | `0.0.0.0` |
| `API_PORT` | FastAPI port | `8000` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required |
| `TELEGRAM_ADMIN_IDS` | Comma-separated admin IDs | Optional |
| `DOWNLOAD_PATH` | Path for downloads | `./downloads` |
| `MAX_CONCURRENT_DOWNLOADS` | Max parallel downloads | `3` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🔧 API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /scrape` - Start scraping job
- `GET /job/{job_id}` - Get job status
- `GET /jobs` - List all jobs
- `DELETE /job/{job_id}` - Delete a job

## 🐛 Troubleshooting

### Bot Not Responding

1. Check if bot token is correct in `.env`
2. Verify bot is running: `docker-compose ps` or check terminal
3. Check logs: `docker-compose logs bot`

### Videos Not Downloading

1. Check worker status: `docker-compose logs worker`
2. Verify Redis is running: `redis-cli ping`
3. Check download path permissions

### Scraper Errors

1. TikTok may block excessive requests - add delays
2. Install Playwright browsers: `playwright install chromium`
3. Check TikTok username is valid

## 📝 Notes

- Downloads are organized by username in the `downloads/` folder
- Large profiles may take significant time to scrape
- Rate limiting is important to avoid being blocked by TikTok
- Videos are stored as MP4 files

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is for educational purposes only. Please respect TikTok's Terms of Service and content creators' rights.

## ⚠️ Disclaimer

This tool is for educational purposes only. Users are responsible for complying with TikTok's Terms of Service and applicable laws. The developers are not responsible for any misuse of this software.

## 🔗 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Redis Documentation](https://redis.io/docs/)
- [TikTokApi Documentation](https://github.com/davidteather/TikTok-Api)

---

Made with ❤️ by [Your Name]
