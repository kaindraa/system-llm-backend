import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Extract request info
        request_id = request.headers.get("X-Request-ID", "-")
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        path = request.url.path

        # Log request
        logger.info(f"→ {method} {path} | Client: {client_host} | Request-ID: {request_id}")

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            logger.error(
                f"✗ {method} {path} | Error: {str(e)} | "
                f"Time: {process_time:.3f}s | Client: {client_host}"
            )
            raise

        # Calculate process time
        process_time = time.time() - start_time

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        if request_id != "-":
            response.headers["X-Request-ID"] = request_id

        # Log response
        status_code = response.status_code
        status_emoji = "✓" if status_code < 400 else "✗"

        logger.info(
            f"{status_emoji} {method} {path} | "
            f"Status: {status_code} | "
            f"Time: {process_time:.3f}s | "
            f"Client: {client_host}"
        )

        return response


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and log unhandled exceptions"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # Log full exception with traceback
            logger.exception(
                f"Unhandled exception in {request.method} {request.url.path}: {str(e)}"
            )

            # Re-raise the exception to be handled by FastAPI's exception handlers
            raise
