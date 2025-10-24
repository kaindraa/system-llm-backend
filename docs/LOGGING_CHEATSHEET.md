# Logging Cheatsheet - Quick Reference

## 📊 Log Viewing Commands

### 1. Real-time Console Logs (Recommended for Development)

```bash
# Follow all logs in real-time
docker logs -f system-llm-api

# Last 50 lines
docker logs --tail 50 system-llm-api

# Last 100 lines with timestamps
docker logs --tail 100 -t system-llm-api

# Since specific time
docker logs --since 10m system-llm-api  # last 10 minutes
docker logs --since 1h system-llm-api   # last 1 hour
```

### 2. File-based Logs (Inside Container)

```bash
# View entire app.log
docker exec system-llm-api cat /app/logs/app.log

# Last 50 lines
docker exec system-llm-api tail -50 /app/logs/app.log

# Follow in real-time
docker exec system-llm-api tail -f /app/logs/app.log

# Count total log lines
docker exec system-llm-api wc -l /app/logs/app.log

# View error log
docker exec system-llm-api cat /app/logs/error.log
```

### 3. Copy Logs to Host (for Analysis)

```bash
# Copy app.log to local
docker cp system-llm-api:/app/logs/app.log ./logs/app.log

# Copy error.log to local
docker cp system-llm-api:/app/logs/error.log ./logs/error.log

# View locally
cat logs/app.log
tail -f logs/app.log
```

## 🔍 Filtering Logs

### By Status Code

```bash
# Successful requests (2xx)
docker exec system-llm-api grep "Status: 2" /app/logs/app.log

# Client errors (4xx)
docker exec system-llm-api grep "Status: 4" /app/logs/app.log

# Server errors (5xx)
docker exec system-llm-api grep "Status: 5" /app/logs/app.log

# Failed requests (4xx or 5xx)
docker exec system-llm-api grep -E "Status: [45][0-9]{2}" /app/logs/app.log
```

### By HTTP Method

```bash
# GET requests only
docker exec system-llm-api grep "→ GET" /app/logs/app.log

# POST requests only
docker exec system-llm-api grep "→ POST" /app/logs/app.log

# PUT/PATCH/DELETE
docker exec system-llm-api grep -E "→ (PUT|PATCH|DELETE)" /app/logs/app.log
```

### By Endpoint

```bash
# Authentication endpoints
docker exec system-llm-api grep "/auth/" /app/logs/app.log

# Specific endpoint
docker exec system-llm-api grep "/api/v1/auth/login" /app/logs/app.log

# Health check
docker exec system-llm-api grep "/health" /app/logs/app.log
```

### By Log Level

```bash
# INFO logs only
docker exec system-llm-api grep "INFO" /app/logs/app.log

# WARNING logs
docker exec system-llm-api grep "WARNING" /app/logs/app.log

# ERROR logs
docker exec system-llm-api grep "ERROR" /app/logs/app.log

# CRITICAL logs
docker exec system-llm-api grep "CRITICAL" /app/logs/app.log

# ERROR and above
docker exec system-llm-api grep -E "(ERROR|CRITICAL)" /app/logs/app.log
```

### By Time Range

```bash
# Logs from specific date
docker exec system-llm-api grep "2025-10-24" /app/logs/app.log

# Logs from specific hour
docker exec system-llm-api grep "2025-10-24 14:" /app/logs/app.log

# Logs from specific minute
docker exec system-llm-api grep "2025-10-24 14:30:" /app/logs/app.log
```

### By Client IP

```bash
# Requests from specific IP
docker exec system-llm-api grep "Client: 172.20.0.1" /app/logs/app.log

# All unique client IPs
docker exec system-llm-api grep "Client:" /app/logs/app.log | awk '{print $NF}' | sort -u
```

### By Response Time (Performance Analysis)

```bash
# Slow requests (> 1 second)
docker exec system-llm-api grep -E "Time: [1-9]\." /app/logs/app.log

# Very slow requests (> 5 seconds)
docker exec system-llm-api grep -E "Time: [5-9]\." /app/logs/app.log

# All requests with timing
docker exec system-llm-api grep "Time:" /app/logs/app.log
```

## 📈 Log Analysis Commands

### Request Statistics

```bash
# Total number of requests
docker exec system-llm-api grep "→" /app/logs/app.log | wc -l

# Successful vs Failed
echo "Successful (✓):" && docker exec system-llm-api grep "✓" /app/logs/app.log | wc -l
echo "Failed (✗):" && docker exec system-llm-api grep "✗" /app/logs/app.log | wc -l

# Requests per endpoint
docker exec system-llm-api grep "→" /app/logs/app.log | awk '{print $8}' | sort | uniq -c | sort -rn

# Top 10 most accessed endpoints
docker exec system-llm-api grep "→" /app/logs/app.log | awk '{print $8}' | sort | uniq -c | sort -rn | head -10
```

### Error Analysis

```bash
# Count errors by status code
docker exec system-llm-api grep "Status:" /app/logs/app.log | awk '{print $(NF-3)}' | sort | uniq -c

# Most common errors
docker exec system-llm-api grep "ERROR" /app/logs/app.log | sort | uniq -c | sort -rn

# Unique error messages
docker exec system-llm-api grep "ERROR" /app/logs/app.log | cut -d'-' -f5- | sort -u
```

### Performance Metrics

```bash
# Average response time (approximate)
docker exec system-llm-api grep "Time:" /app/logs/app.log | awk '{print $(NF-3)}' | sed 's/s//' | awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'

# Slowest requests
docker exec system-llm-api grep "Time:" /app/logs/app.log | sort -t':' -k7 -rn | head -10
```

## 🎨 Log Symbols Explained

| Symbol | Meaning | Status |
|--------|---------|--------|
| `→` | Incoming request | - |
| `✓` | Successful response | < 400 |
| `✗` | Failed response | >= 400 |

## 🎨 Color Codes in Console

| Color | Level | ANSI Code |
|-------|-------|-----------|
| 🔵 Cyan | DEBUG | `[36m` |
| 🟢 Green | INFO | `[32m` |
| 🟡 Yellow | WARNING | `[33m` |
| 🔴 Red | ERROR | `[31m` |
| 🟣 Magenta | CRITICAL | `[35m` |

## 🧹 Log Maintenance

### Clear Logs

```bash
# Truncate app.log (keep file, clear content)
docker exec system-llm-api sh -c "> /app/logs/app.log"

# Truncate error.log
docker exec system-llm-api sh -c "> /app/logs/error.log"

# Remove old rotated logs
docker exec system-llm-api sh -c "rm -f /app/logs/*.log.*"
```

### Check Log Size

```bash
# Current log file sizes
docker exec system-llm-api ls -lh /app/logs/

# Total logs directory size
docker exec system-llm-api du -sh /app/logs/
```

### Backup Logs

```bash
# Backup to timestamped file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker cp system-llm-api:/app/logs/app.log ./logs/backup/app_${TIMESTAMP}.log
docker cp system-llm-api:/app/logs/error.log ./logs/backup/error_${TIMESTAMP}.log
```

## 🚨 Monitoring Commands (Production)

### Watch for Errors

```bash
# Watch error log in real-time
docker exec system-llm-api tail -f /app/logs/error.log

# Alert on new errors (basic)
watch -n 5 'docker exec system-llm-api grep "ERROR" /app/logs/app.log | tail -5'
```

### Health Check via Logs

```bash
# Check if application is running (recent logs)
docker logs --tail 1 --since 1m system-llm-api

# Count requests in last 5 minutes
docker exec system-llm-api sh -c "grep '$(date -u -d '5 minutes ago' +%Y-%m-%d)' /app/logs/app.log | grep '→' | wc -l"
```

## 💡 Pro Tips

### Combine Multiple Filters

```bash
# Failed auth requests from today
docker exec system-llm-api sh -c "grep '2025-10-24' /app/logs/app.log | grep '/auth/' | grep '✗'"

# Slow POST requests with errors
docker exec system-llm-api sh -c "grep 'POST' /app/logs/app.log | grep -E 'Time: [1-9]\.' | grep 'Status: [45]'"
```

### Export to File for Analysis

```bash
# Export filtered logs
docker exec system-llm-api grep "ERROR" /app/logs/app.log > errors_today.log

# Export with line numbers
docker exec system-llm-api grep -n "✗" /app/logs/app.log > failed_requests.log
```

### Multi-line Search

```bash
# Get context around errors (5 lines before and after)
docker exec system-llm-api grep -A 5 -B 5 "ERROR" /app/logs/app.log
```

## 🔗 Quick Access Aliases (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# View logs
alias logs='docker logs -f system-llm-api'
alias logs-tail='docker exec system-llm-api tail -f /app/logs/app.log'
alias logs-error='docker exec system-llm-api tail -f /app/logs/error.log'

# Filter logs
alias logs-failed='docker exec system-llm-api grep "✗" /app/logs/app.log'
alias logs-success='docker exec system-llm-api grep "✓" /app/logs/app.log'
alias logs-auth='docker exec system-llm-api grep "/auth/" /app/logs/app.log'
```

---

**For full documentation, see [LOGGING.md](LOGGING.md)**
