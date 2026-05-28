from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from engine.flow_analysis import SAMPLE_SNAPSHOT, analyze_snapshot


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT_PATH = ROOT_DIR / "db" / "eod_snapshot.json"

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env")
except Exception:
    pass


def load_raw_snapshot() -> dict[str, Any]:
    configured_path = os.getenv("KQUANT_EOD_SNAPSHOT")
    snapshot_path = Path(configured_path) if configured_path else DEFAULT_SNAPSHOT_PATH
    if not snapshot_path.is_absolute():
        snapshot_path = ROOT_DIR / snapshot_path
    if snapshot_path.exists():
        with snapshot_path.open("r", encoding="utf-8") as file:
            snapshot = json.load(file)
        snapshot.setdefault("source", f"file:{snapshot_path.name}")
        snapshot.setdefault("mode", "eod")
        return snapshot

    snapshot = dict(SAMPLE_SNAPSHOT)
    snapshot["mode"] = "sample"
    return snapshot


def load_dashboard_payload() -> dict[str, Any]:
    return analyze_snapshot(load_raw_snapshot())
