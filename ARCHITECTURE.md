# TikTok Scraper Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │ Telegram Bot │◄────────┤   FastAPI    │                      │
│  │  Interface   │         │     REST     │                      │
│  └──────────────┘         └──────┬───────┘                      │
└─────────────────────────────────┼─────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │       Redis Queue           │
                    │  ┌────────────────────┐     │
                    │  │ Scrape Jobs        │     │
                    │  │ Download Jobs      │     │
                    │  │ Job Status         │     │
                    │  │ Video Tracking     │     │
                    │  └────────────────────┘     │
                    └──────────────┬──────────────┘
                                   │
┌──────────────────────────────────┼──────────────────────────────┐
│                            WORKER                                │
│                                   │                              │
│  ┌────────────────────────────────▼───────────────────────────┐ │
│  │           Unified TikTok Scraper                           │ │
│  │                                                             │ │
│  │  ┌──────────────────┐         ┌──────────────────┐        │ │
│  │  │  Playwright      │         │   HTTP Scraper   │        │ │
│  │  │  Method          │◄────────┤   (Fallback)     │        │ │
│  │  │                  │         │                  │        │ │
│  │  │ • TikTokApi      │  Auto   │ • httpx + BS4    │        │ │
│  │  │ • Browser        │  Switch │ • No browser     │        │ │
│  │  │ • Primary        │ on      │ • Lighter        │        │ │
│  │  │                  │  Block  │                  │        │ │
│  │  └──────────────────┘         └──────────────────┘        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                   │                              │
│  ┌────────────────────────────────▼───────────────────────────┐ │
│  │              Video Downloader                              │ │
│  │  • Concurrent downloads (max 3)                            │ │
│  │  • Duplicate detection                                     │ │
│  │  • Progress tracking                                       │ │
│  └─────────────────────────────────┬───────────────────────────┘ │
└────────────────────────────────────┼──────────────────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │     File System                 │
                    │  downloads/                     │
                    │    └── {username}/              │
                    │         ├── video1.mp4          │
                    │         ├── video2.mp4          │
                    │         └── ...                 │
                    └─────────────────────────────────┘
```

## Scraper Fallback Flow

```
                Start Scraping Job
                        │
                        ▼
            ┌───────────────────────┐
            │ Initialize Unified    │
            │ Scraper               │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │ Try Playwright Init   │
            └───────────┬───────────┘
                        │
                ┌───────┴───────┐
                │               │
           ✓ Success      ✗ Failed
                │               │
                │               ▼
                │     ┌─────────────────┐
                │     │ Initialize HTTP │
                │     │ Scraper         │
                │     └────────┬────────┘
                │              │
                ▼              ▼
       ┌────────────────────────────┐
       │  READY TO SCRAPE           │
       │  Method: Playwright or HTTP│
       └────────────┬───────────────┘
                    │
                    ▼
       ┌────────────────────────┐
       │ Scrape User Profile    │
       └────────────┬───────────┘
                    │
            ┌───────┴────────┐
            │                │
       ✓ Success     ✗ Bot Detection
            │                │
            │                ▼
            │      ┌─────────────────┐
            │      │ Switch to HTTP  │
            │      │ Retry Operation │
            │      └────────┬────────┘
            │               │
            ▼               ▼
       ┌────────────────────────────┐
       │ Get Video List             │
       └────────────┬───────────────┘
                    │
            ┌───────┴────────┐
            │                │
       ✓ Success     ✗ Bot Detection
            │                │
            │                ▼
            │      ┌─────────────────┐
            │      │ Switch to HTTP  │
            │      │ Retry Operation │
            │      └────────┬────────┘
            │               │
            ▼               ▼
       ┌────────────────────────────┐
       │ Queue Videos for Download  │
       └────────────────────────────┘
```

## Component Interaction

```
┌──────────────┐
│ Telegram Bot │
└──────┬───────┘
       │ /scrape username
       ▼
┌──────────────┐
│  FastAPI     │
│  POST /scrape│
└──────┬───────┘
       │ Create job
       ▼
┌──────────────┐
│    Redis     │◄──────────┐
│  scrape_queue│           │
└──────┬───────┘           │
       │                   │
       ▼                   │
┌──────────────┐           │
│   Worker     │           │
│  Pull job    │           │
└──────┬───────┘           │
       │                   │
       ▼                   │
┌─────────────────────┐    │
│ UnifiedScraper      │    │
│ .initialize()       │    │
│   Try Playwright ───┼────┤ Success
│   On fail → HTTP    │    │
└──────┬──────────────┘    │
       │                   │
       ▼                   │
┌─────────────────────┐    │
│ .get_user_profile() │    │
│   Try method ───────┼────┤ Success
│   On block → switch │    │ or
└──────┬──────────────┘    │ Fallback
       │                   │
       ▼                   │
┌─────────────────────┐    │
│ .scrape_videos()    │    │
│   Try method ───────┼────┤ Success
│   On block → switch │    │ or
└──────┬──────────────┘    │ Fallback
       │                   │
       ▼                   │
┌──────────────┐           │
│    Redis     │           │
│download_queue│◄──────────┘
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Worker     │
│  Downloader  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ File System  │
│ downloads/   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Telegram Bot │
│ Send video   │
│ (batch of 5) │
└──────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        JOB LIFECYCLE                         │
└─────────────────────────────────────────────────────────────┘

1. CREATE JOB
   User → Bot → API → Redis
   Status: pending
   
2. SCRAPE PHASE
   Worker picks job → Initialize Scraper
   
   Try Playwright:
   ┌─────────────────┐
   │ Playwright      │
   │ .initialize()   │
   └────────┬────────┘
            │
      ┌─────┴──────┐
      │            │
   Success      Failed
      │            │
      │            ▼
      │     ┌──────────────┐
      │     │ HTTP Scraper │
      │     │ .initialize()│
      │     └──────┬───────┘
      │            │
      └────────────┴──────► Status: scraping
                            │
                Get Profile │
                            │
                Get Videos  │
                            │
                            ▼
                   Queue Downloads
                            │
                            ▼
                   Status: downloading

3. DOWNLOAD PHASE
   Worker downloads videos (3 concurrent)
   
   For each video:
   ├─ Check if downloaded (Redis)
   ├─ Download if new
   ├─ Check if sent to user (Redis)
   └─ Send if new (batch of 5)
   
   Status: completed

4. CLEANUP
   Job marked complete
   Stats updated
```

## Technology Stack

```
┌────────────────────────────────────────────┐
│            Frontend Layer                  │
│  • python-telegram-bot (Telegram API)      │
│  • Inline keyboards & callbacks            │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│            API Layer                       │
│  • FastAPI (REST endpoints)                │
│  • Pydantic (data validation)              │
│  • Async/await                             │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│         Processing Layer                   │
│  • Redis (job queue, caching)              │
│  • Background workers                      │
│  • Async task processing                   │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│          Scraping Layer                    │
│  ┌──────────────┐  ┌──────────────┐       │
│  │ Playwright   │  │ HTTP Scraper │       │
│  ├──────────────┤  ├──────────────┤       │
│  │• TikTokApi   │  │• httpx       │       │
│  │• Chromium    │  │• BeautifulSoup│      │
│  │• Playwright  │  │• jmespath    │       │
│  └──────────────┘  └──────────────┘       │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│          Storage Layer                     │
│  • File system (downloads/)                │
│  • Redis (metadata, tracking)              │
└────────────────────────────────────────────┘
```

## Error Handling & Resilience

```
┌────────────────────────────────────────────────────┐
│              ERROR DETECTION                       │
└────────────────────────────────────────────────────┘

Playwright Errors:
├─ EmptyResponseException → Switch to HTTP
├─ "bot detected" → Switch to HTTP
├─ "captcha" → Switch to HTTP
├─ Timeout → Retry with HTTP
└─ Connection error → Retry with HTTP

HTTP Scraper Errors:
├─ Connection timeout → Retry
├─ 403 Forbidden → Add cookie/proxy
├─ 404 Not Found → User doesn't exist
└─ Parse error → TikTok changed structure

Download Errors:
├─ Network error → Retry (3 times)
├─ Disk full → Fail job
└─ Corrupt video → Skip, continue

┌────────────────────────────────────────────────────┐
│              RECOVERY STRATEGIES                   │
└────────────────────────────────────────────────────┘

1. Automatic Fallback
   Playwright fails → HTTP scraper

2. Session Recovery
   Empty response → Reinitialize sessions

3. Retry Logic
   Network errors → Retry with backoff

4. User Notification
   Job fails → Send Telegram message

5. State Preservation
   Job state in Redis → Resume after restart
```

This architecture provides:
- ✅ High reliability through fallback
- ✅ Scalability through async processing
- ✅ Resilience through error handling
- ✅ Visibility through comprehensive logging
- ✅ Flexibility through modular design
