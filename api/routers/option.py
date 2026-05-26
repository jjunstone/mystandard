from __future__ import annotations

from fastapi import APIRouter

from api.schemas import OptionChainPayload
from api.state import market_state
from engine.oim_engine import calculate_oi_barriers


router = APIRouter(prefix="/api/options", tags=["options"])


def _dump_rows(payload: OptionChainPayload) -> list[dict]:
    return [row.model_dump() if hasattr(row, "model_dump") else row.dict() for row in payload.rows]


@router.get("/oi")
def get_option_oi() -> dict:
    snapshot = market_state.snapshot()
    return {
        "ok": True,
        "data": {
            "current_price": snapshot["current_price"],
            "rows": snapshot["option_chain"],
            "barriers": snapshot["barriers"],
        },
    }


@router.post("/oi")
def update_option_oi(payload: OptionChainPayload) -> dict:
    rows = _dump_rows(payload)
    if payload.current_price is not None:
        market_state.set_price(payload.current_price)
    events = market_state.set_option_chain(rows) if payload.update_state else []
    barriers = (
        market_state.snapshot()["barriers"]
        if payload.update_state
        else calculate_oi_barriers(rows, payload.current_price)
    )
    return {
        "ok": True,
        "data": {
            "barriers": barriers,
            "events": events,
        },
    }


@router.get("/barriers")
def get_barriers() -> dict:
    return {"ok": True, "data": market_state.snapshot()["barriers"]}


@router.post("/barriers/calculate")
def calculate_barriers(payload: OptionChainPayload) -> dict:
    rows = _dump_rows(payload)
    return {"ok": True, "data": calculate_oi_barriers(rows, payload.current_price)}
