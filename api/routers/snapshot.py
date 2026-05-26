from __future__ import annotations

from fastapi import APIRouter

from api.state import market_state


router = APIRouter(prefix="/api/snapshot", tags=["snapshot"])


@router.get("")
def get_snapshot() -> dict:
    return {"ok": True, "data": market_state.snapshot()}
