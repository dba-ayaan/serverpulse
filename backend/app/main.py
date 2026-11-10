import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import Response

from app.core.config import settings
from app.core.database import check_database

from app.api.servers import router as servers_router
from app.api.metrics import router as metrics_router
from app.models.server import Base
from app.core.database import engine

app = FastAPI(
    title=settings.app_name,
    description="Infrastructure Monitoring Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

@app.get("/", tags=["General"])
def root():
    return {
        "application": "ServerPulse",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.get("/ready", tags=["Health"])
def readiness():
    database_ok = check_database()

    if not database_ok:
        return Response(
            content='{"status":"not_ready","database":"unavailable"}',
            status_code=503,
            media_type="application/json",
        )

    return {
        "status": "ready",
        "database": "connected",
    }


@app.get("/api/v1/prometheus/health", tags=["Monitoring"])
async def prometheus_health():
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"{settings.prometheus_url}/-/healthy"
            )
            response.raise_for_status()

        return {"prometheus": "connected"}

    except httpx.HTTPError:
        return Response(
            content='{"prometheus":"unavailable"}',
            status_code=503,
            media_type="application/json",
        )
app.include_router(servers_router)
app.include_router(metrics_router)
