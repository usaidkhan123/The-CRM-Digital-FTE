import time
from fastapi import FastAPI, Request
from prometheus_client import make_asgi_app, generate_latest
from starlette.responses import Response

from app.config import settings
from app.database import init_db
from app.routes import router
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

app = FastAPI(title="Memory Service", version="2.0.0")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
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
    return response


@app.on_event("startup")
async def startup():
    logger.info("Starting Memory Service...")
    await init_db()
    logger.info("Database initialized")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


app.include_router(router)
