from __future__ import annotations

from fastapi import APIRouter

from api.schemas import OrderbookPayload, PriceTickPayload
from api.state import market_state


router = APIRouter(prefix="/api/flow", tags=["flow"])


@router.get("/state")
def get_state() -> dict:
    return {"ok": True, "data": market_state.snapshot()}


@router.post("/futures/tick")
def update_futures_tick(payload: PriceTickPayload) -> dict:
    events = market_state.set_price(payload.current_price)
    return {"ok": True, "data": {"events": events, "snapshot": market_state.snapshot()}}


@router.post("/orderbook")
def update_orderbook(payload: OrderbookPayload) -> dict:
    event = market_state.set_orderbook(
        bid_total=payload.bid_total,
        ask_total=payload.ask_total,
        best_bid=payload.best_bid,
        best_ask=payload.best_ask,
        bid_size=payload.bid_size,
        ask_size=payload.ask_size,
    )
    return {"ok": True, "data": event}
