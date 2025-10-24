# Logging System Documentation

## Overview

The System LLM application uses a comprehensive logging system that provides:
- **Colored console output** for development
- **File-based logging** with rotation
- **Request/Response logging** middleware
- **Separate error logs** for critical issues
- **Structured log format** for easy parsing

## Log Files

All logs are stored in the `logs/` directory:

| File | Purpose | Level | Rotation |
|------|---------|-------|----------|
| `app.log` | All application logs | DEBUG (dev) / INFO (prod) | 10 MB, 5 backups |
| `error.log` | Errors and exceptions only | ERROR | 10 MB, 5 backups |

## Log Levels

- **DEBUG**: Detailed information for debugging (only in development)
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical issues requiring immediate attention

## Log Format

```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message
```

Example:
```
2025-10-24 01:22:34 - system_llm.app.main - INFO - 🚀 System LLM is starting...
```

## Using the Logger

### Basic Usage

```python
from app.core.logging import get_logger

# Get logger for your module
logger = get_logger(__name__)

# Log messages
logger.debug("Debugging information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical issue")
```

### Logging Exceptions

```python
try:
    # Some code that might fail
    risky_operation()
except Exception as e:
    # Log exception with full traceback
    logger.exception(f"Failed to perform operation: {str(e)}")
```

### Structured Logging

```python
# Log with context
logger.info(
    f"User {user_id} performed action {action} | "
    f"Status: {status} | Duration: {duration}s"
)
```

## Request Logging

All HTTP requests are automatically logged with the following information:
- HTTP method
- URL path
- Client IP address
- Request ID (if provided)
- Response status code
- Processing time

Example:
```
→ GET /api/v1/auth/login | Client: 172.20.0.1 | Request-ID: -
✓ GET /api/v1/auth/login | Status: 200 | Time: 0.045s | Client: 172.20.0.1
```

**Symbols:**
- `→` - Incoming request
- `✓` - Successful response (status < 400)
- `✗` - Failed response (status >= 400)

## Console Colors

In development mode, console logs are color-coded:

- 🔵 **Cyan** - DEBUG
- 🟢 **Green** - INFO
- 🟡 **Yellow** - WARNING
- 🔴 **Red** - ERROR
- 🟣 **Magenta** - CRITICAL

## Configuration

Logging is configured in [app/core/logging.py](../app/core/logging.py) and initialized at application startup.

**Settings controlled by environment:**
- `DEBUG=True` → Log level: DEBUG
- `DEBUG=False` → Log level: INFO

## Viewing Logs

### In Docker Container

```bash
# View real-time logs
docker logs -f system-llm-api

# View last 100 lines
docker logs --tail 100 system-llm-api

# View app.log file
docker exec system-llm-api cat /app/logs/app.log

# View error.log file
docker exec system-llm-api cat /app/logs/error.log
```

### On Host Machine

```bash
# Copy logs from container
docker cp system-llm-api:/app/logs/app.log ./logs/app.log

# View with tail
tail -f logs/app.log

# Search logs
grep "ERROR" logs/app.log
```

## Best Practices

### ✅ DO

- Use appropriate log levels
- Include context in log messages
- Log exceptions with `logger.exception()`
- Use structured format for important events
- Log user actions for audit trail

```python
# Good
logger.info(f"User {user.id} logged in | IP: {ip_address}")
logger.error(f"Database query failed | Query: {query} | Error: {str(e)}")
```

### ❌ DON'T

- Log sensitive information (passwords, tokens)
- Use print() statements (use logger instead)
- Log in tight loops (causes performance issues)
- Log the same information multiple times

```python
# Bad
print("This won't be logged to file")
logger.info(f"Password: {password}")  # Never log passwords!
```

## Middleware

The application uses two logging middlewares:

1. **RequestLoggingMiddleware**: Logs all HTTP requests/responses
2. **ErrorLoggingMiddleware**: Catches and logs unhandled exceptions

These are configured in [app/main.py](../app/main.py).

## Troubleshooting

### Logs not appearing in files

1. Check if logs directory exists:
   ```bash
   docker exec system-llm-api ls -la /app/logs/
   ```

2. Check file permissions:
   ```bash
   docker exec system-llm-api ls -la /app/logs/
   ```

3. Restart the container:
   ```bash
   docker-compose restart api
   ```

### Too many log files

The log rotation is set to keep 5 backup files. If you need to clean up:

```bash
# Remove old logs
docker exec system-llm-api sh -c "rm /app/logs/*.log.*"
```

## Production Considerations

For production deployment:

1. **Log Aggregation**: Consider using log aggregation tools (ELK, Splunk, CloudWatch)
2. **Log Level**: Set `DEBUG=False` to reduce log volume
3. **Monitoring**: Set up alerts for ERROR and CRITICAL logs
4. **Retention**: Implement log retention policy
5. **Privacy**: Ensure no PII (Personally Identifiable Information) is logged

## Related Files

- [app/core/logging.py](../app/core/logging.py) - Logging configuration
- [app/middleware/logging.py](../app/middleware/logging.py) - Request logging middleware
- [app/main.py](../app/main.py) - Logging initialization
