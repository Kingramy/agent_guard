"""Health and readiness diagnostic routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agentguard.core.config import get_settings
from agentguard.storage.database import get_db

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    # Check PostgreSQL
    pg_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        pg_status = f"unhealthy: {e}"

    # Check Redis
    redis_status = "connected"
    try:
        redis_client = getattr(request.app.state, "redis", None)
        if redis_client:
            await redis_client.ping()
    except Exception as e:
        redis_status = f"unhealthy: {e}"

    is_healthy = pg_status == "connected" and redis_status == "connected"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "postgres": pg_status,
        "redis": redis_status,
    }
