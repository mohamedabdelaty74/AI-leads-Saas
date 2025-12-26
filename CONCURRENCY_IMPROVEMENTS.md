# Concurrency Improvements

This document outlines the concurrency improvements made to the Elite Creatif SaaS platform.

## Summary of Changes

### 1. Database Connection Pooling (PostgreSQL)
**File:** `models/base.py`

Added optimized connection pool settings for PostgreSQL:
- `pool_size=20` - Maximum connections in the pool (up from default 5)
- `max_overflow=40` - Extra connections when pool is full (up from default 10)
- `pool_timeout=30` - Seconds to wait for a connection
- `pool_recycle=3600` - Recycle connections after 1 hour (prevents stale connections)
- `pool_pre_ping=True` - Verify connections before using (prevents database errors)

**Impact:** Can now handle **up to 60 concurrent database connections** (20 pool + 40 overflow)

### 2. Production Mode with Multiple Workers
**File:** `backend/main.py`

Added intelligent environment-based configuration:

#### Development Mode (default)
```bash
python backend/main.py
```
- 1 worker
- Auto-reload enabled
- Best for development

#### Production Mode
```bash
# Windows
start-production.bat

# Linux/Mac
./start-production.sh

# Or manually
set ENV=production
python backend/main.py
```

Production settings:
- **Multiple workers:** `(2 × CPU cores) + 1`
- **Concurrent requests:** Up to 1,000
- **Worker refresh:** After 10,000 requests (memory leak protection)
- **Keep-alive timeout:** 75 seconds

### 3. Concurrency Capabilities

#### Before Improvements:
- 1 worker
- 5 database connections
- Limited concurrent request handling

#### After Improvements:
**On a 4-core CPU:**
- **9 workers** (2 × 4 + 1)
- **60 database connections** (20 pool + 40 overflow)
- **1,000 max concurrent requests**
- **~360 threads** available (40 per worker × 9 workers)

## Performance Benefits

### Request Handling
✅ Multiple users can browse leads simultaneously without blocking
✅ Notification polling from multiple browsers won't slow down the API
✅ CSV uploads can run while other users query data
✅ AI email generation happens in background without affecting other requests

### Database Operations
✅ Up to 60 concurrent database queries
✅ Automatic connection recycling prevents stale connections
✅ Connection pre-ping prevents "server has gone away" errors
✅ Better handling of long-running transactions

### Load Distribution
✅ Each worker handles independent requests
✅ If one worker is busy with AI generation, others handle quick requests
✅ Automatic worker restarts prevent memory leaks
✅ Better CPU utilization across all cores

## How It Works

### Architecture

```
Client Requests
     ↓
Load Balancer (Uvicorn)
     ↓
Worker 1 (Asyncio + Thread Pool)
Worker 2 (Asyncio + Thread Pool)
Worker 3 (Asyncio + Thread Pool)
...
Worker N (Asyncio + Thread Pool)
     ↓
Database Connection Pool
     ↓
PostgreSQL Database
```

### Request Flow Example

**Scenario:** 15 users simultaneously using the app

1. **User 1-5:** Viewing leads → Workers 1-5 (database queries)
2. **User 6-10:** Browsing campaigns → Workers 6-5 (database queries, reusing workers)
3. **User 11:** Uploading CSV → Worker 1 (background task, database writes)
4. **User 12:** Generating AI email → Worker 2 (background task, AI model)
5. **User 13-15:** Getting notifications → Workers 3-5 (quick database reads)

All requests are handled **concurrently** without blocking!

## Testing Concurrency

### Test Multiple Simultaneous Requests

**Option 1: Browser Tabs**
1. Open the app in 10 different browser tabs
2. Click around simultaneously
3. All requests should complete without blocking

**Option 2: API Load Test**
```bash
# Install hey (HTTP load tester)
# Windows: Download from https://github.com/rakyll/hey
# Mac: brew install hey
# Linux: Download binary

# Test with 100 concurrent requests
hey -n 100 -c 10 http://localhost:8000/api/v1/campaigns
```

**Expected Results:**
- Development mode: Slower, requests queue
- Production mode: Faster, requests handled in parallel

## Monitoring

### Check Active Connections
```sql
-- PostgreSQL: View active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'elite_creatif_saas';

-- View connection details
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE datname = 'elite_creatif_saas';
```

### Check Worker Performance
Look for these in logs:
```
Production Mode:
  - Workers: 9 (CPU cores: 4)
```

### Monitor Request Latency
The middleware logs slow requests:
```
[WARNING] SLOW REQUEST: GET /api/v1/leads - Duration: 2500ms
```

## Recommendations

### For Development
- Keep using development mode (default)
- Auto-reload helps with rapid iteration

### For Production Deployment
1. Set `ENV=production` in environment variables
2. Use production startup scripts
3. Monitor database connection pool usage
4. Consider adding a reverse proxy (nginx/Caddy) for additional load balancing
5. Enable connection pooling at the database level (PgBouncer for PostgreSQL)

### For High Traffic
If you expect >1,000 concurrent users:

1. **Horizontal Scaling:** Deploy multiple instances behind a load balancer
2. **Database Tuning:** Increase PostgreSQL `max_connections`
3. **Caching:** Add Redis for frequently accessed data (campaigns, leads)
4. **CDN:** Serve static assets (frontend) from CDN
5. **Connection Pooler:** Use PgBouncer between API and PostgreSQL

## Troubleshooting

### "Too many connections" error
- Increase `pool_size` in `models/base.py`
- Increase `max_connections` in PostgreSQL config
- Add connection pooler (PgBouncer)

### Workers not starting
- Check if port 8000 is available
- Verify Python multiprocessing works: `python -c "import multiprocessing; print(multiprocessing.cpu_count())"`
- Check logs for errors

### Requests still slow
- Check database query performance
- Add database indexes for frequently queried fields
- Profile slow endpoints
- Consider caching frequently accessed data

## Future Improvements

Potential enhancements for even better concurrency:

1. **Async SQLAlchemy:** Convert to async database operations (requires refactoring)
2. **Redis Caching:** Cache campaigns and leads data
3. **Message Queue:** Use Celery for background tasks instead of BackgroundTasks
4. **WebSockets:** Real-time notifications instead of polling
5. **Read Replicas:** Separate read/write database connections

---

**Questions?** Check the main README or open an issue.
