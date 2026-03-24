from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import assignments, loads, videos
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.watchdog_service import start_watchdog, stop_watchdog


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    start_watchdog()
    yield
    stop_scheduler()
    stop_watchdog()


app = FastAPI(
    title="Skybox DZ",
    description="Self-hosted skydiving dropzone operations tool",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(loads.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok"}
