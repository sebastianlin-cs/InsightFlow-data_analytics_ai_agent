from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.analysis_sessions import router as analysis_sessions_router
from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

charts_dir = Path(settings.UPLOAD_DIR) / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)
app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(datasets_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(
    analysis_sessions_router,
    prefix="/api/analysis-sessions",
    tags=["analysis-sessions"],
)
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
