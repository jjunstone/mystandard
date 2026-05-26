from __future__ import annotations

from typing import Any

from api.state import market_state


def publish_price_tick(current_price: float) -> list[dict[str, Any]]:
    return market_state.set_price(current_price)


def publish_option_chain(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return market_state.set_option_chain(rows)


def publish_orderbook(
    bid_total: float,
    ask_total: float,
    best_bid: float | None = None,
    best_ask: float | None = None,
    bid_size: float | None = None,
    ask_size: float | None = None,
) -> dict[str, Any]:
    return market_state.set_orderbook(bid_total, ask_total, best_bid, best_ask, bid_size, ask_size)
