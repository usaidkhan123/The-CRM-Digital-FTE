import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = setup_logging("api-middleware")


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        logger.info(f"[{request_id}] {request.method} {request.url.path}")

        response = await call_next(request)
        duration = time.time() - start

        REQUEST_COUNT.labels(
            service=settings.SERVICE_NAME,
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            service=settings.SERVICE_NAME,
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        logger.info(f"[{request_id}] {response.status_code} ({duration:.3f}s)")
        response.headers["X-Request-ID"] = request_id
        return response
