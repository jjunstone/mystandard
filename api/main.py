from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from collector.eod_provider import load_dashboard_payload
from scripts.import_free_data import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT, write_snapshot


ROOT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_FILE = ROOT_DIR / "dashboard" / "kquant_v2.html"

app = FastAPI(title="K-Quant Daily Flow Terminal", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "null"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(DASHBOARD_FILE)


@app.get("/kquant_v2.html")
def dashboard_alias() -> FileResponse:
    return FileResponse(DASHBOARD_FILE)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard_data() -> dict:
    return load_dashboard_payload()


@app.post("/api/import-free-data")
def import_free_data(request: Request) -> dict:
    client_host = request.client.host if request.client else ""
    if client_host not in {"127.0.0.1", "::1", "localhost"}:
        return {"ok": False, "error": "local requests only"}
    snapshot = write_snapshot(DEFAULT_INPUT_DIR, DEFAULT_OUTPUT)
    return {
        "ok": True,
        "as_of": snapshot["as_of"],
        "source": snapshot["source"],
        "dashboard": load_dashboard_payload(),
    }
