import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from prometheus_client import generate_latest
from starlette.responses import Response

from app.config import settings
from app.agent import AsyncCustomerSuccessAgent
from app.consumer import start_consumer
from app.routes import router
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = AsyncCustomerSuccessAgent(gemini_api_key=settings.GEMINI_API_KEY)
    task = asyncio.create_task(start_consumer(agent))
    logger.info("Agent Service started")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Agent Service stopped")


app = FastAPI(title="Agent Service", version="2.0.0", lifespan=lifespan)


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


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


app.include_router(router)
