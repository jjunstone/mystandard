from __future__ import annotations

from fastapi import APIRouter

from api.state import market_state


router = APIRouter(prefix="/api/signal", tags=["signal"])


@router.get("")
def get_signal() -> dict:
    snapshot = market_state.snapshot()
    barriers = snapshot["barriers"]
    price = snapshot["current_price"]
    put_wall = barriers["put_wall"]["strike"]
    call_wall = barriers["call_wall"]["strike"]
    oim = snapshot["oim"]

    score = 0
    reasons: list[str] = []
    if oim > 0.18:
        score += 1
        reasons.append("bid-side OIM")
    elif oim < -0.18:
        score -= 1
        reasons.append("ask-side OIM")

    if put_wall is not None and price <= put_wall:
        score -= 2
        reasons.append("put wall breached")
    elif put_wall is not None and price - put_wall <= 0.75:
        score += 1
        reasons.append("near put support")

    if call_wall is not None and call_wall - price <= 0.75:
        score -= 1
        reasons.append("near call resistance")

    regime = "LONG" if score >= 1 else "SHORT" if score <= -2 else "HOLD"
    return {
        "ok": True,
        "data": {
            "regime": regime,
            "score": score,
            "reasons": reasons,
            "barriers": barriers,
        },
    }
