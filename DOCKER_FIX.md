# Docker Networking Fix

## Problem
Bot was trying to connect to `http://localhost:8000` but in Docker, each service has its own hostname.

## Solution
1. Added `API_BASE_URL` environment variable to configuration
2. Updated bot to use `settings.api_base_url` instead of hardcoded URL
3. In docker-compose.yml, set `API_BASE_URL=http://api:8000` for bot service

## Docker Service Hostnames
- `redis` - Redis service
- `api` - FastAPI service  
- `worker` - Background worker
- `bot` - Telegram bot

## Environment Variables

### For Docker (docker-compose.yml)
```yaml
environment:
  - REDIS_HOST=redis
  - API_BASE_URL=http://api:8000
```

### For Local Development (.env)
```bash
REDIS_HOST=localhost
API_BASE_URL=http://localhost:8000
```

## Testing
After deploying:
1. Send username to bot
2. Bot should successfully create job
3. Videos should be scraped and sent

If still getting errors, check:
- `docker-compose logs api` - API logs
- `docker-compose logs bot` - Bot logs
- `docker-compose logs worker` - Worker logs
