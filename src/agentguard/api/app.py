"""FastAPI application factory and middleware configuration."""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from agentguard.api.routes import evals, health, traces
from agentguard.core.config import get_settings
from agentguard.evaluators.nli_service import router as nli_router
from agentguard.storage.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: ensure tables exist and connect to Redis
    await init_db()
    app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield
    # Shutdown
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request latency tracking middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
        return response

    # Routers
    app.include_router(health.router)
    app.include_router(traces.router, prefix="/api/v1")
    app.include_router(evals.router, prefix="/api/v1")
    app.include_router(nli_router)

    return app


app = create_app()
