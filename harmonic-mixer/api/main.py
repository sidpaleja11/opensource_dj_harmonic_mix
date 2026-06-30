from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import Database, Settings, get_db, get_settings
from .routes import library, scan, suggest
from .schemas import StatsOut

app = FastAPI(
    title="Harmonic Mixer API",
    version="0.1.0",
    # Disable Swagger UI in production by setting docs_url=None
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

app.include_router(library.router)
app.include_router(scan.router)
app.include_router(suggest.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/stats", response_model=StatsOut)
async def stats(db: Database = Depends(get_db)) -> StatsOut:
    s = db.stats()
    return StatsOut(
        total=s["total"],
        bpm_min=s["bpm_min"],
        bpm_max=s["bpm_max"],
        key_distribution=s["key_distribution"],
    )
