from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routers import flow, option, signal, snapshot
from api.websocket import router as websocket_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="K-QUANT OI Barrier Terminal",
    version="0.1.0",
    description="Realtime open-interest barrier monitor for KOSPI 200 futures/options.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = BASE_DIR / "dashboard"

app.include_router(option.router)
app.include_router(flow.router)
app.include_router(snapshot.router)
app.include_router(signal.router)
app.include_router(websocket_router)
app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/oi_barriers.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
