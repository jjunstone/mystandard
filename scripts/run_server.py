from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))
    load_dotenv()
    host = os.getenv("KQUANT_HOST", "127.0.0.1")
    port = int(os.getenv("KQUANT_PORT", "8000"))
    access_log = _bool_env("KQUANT_ACCESS_LOG", False)
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,
        access_log=access_log,
        log_level=os.getenv("KQUANT_LOG_LEVEL", "info"),
    )
