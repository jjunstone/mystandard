"""In-memory market state shared by REST routes and WebSocket streams."""

from __future__ import annotations

import random
import os
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from engine.oim_engine import build_mock_chain, calculate_oi_barriers, calculate_oim, micro_price


class MarketStateStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self.mode = os.getenv("KQUANT_MODE", "mock").strip().lower() or "mock"
        self.current_price = 353.72
        self.option_chain = build_mock_chain(self.current_price)
        self.oim = 0.0
        self.micro_price: float | None = None
        self.bid_total = 0.0
        self.ask_total = 0.0
        self.sequence = 0
        self.updated_at = datetime.now(timezone.utc)
        self.barriers = calculate_oi_barriers(self.option_chain, self.current_price, self.updated_at)

    def _touch(self) -> None:
        self.sequence += 1
        self.updated_at = datetime.now(timezone.utc)

    def _recalculate(self) -> None:
        self.barriers = calculate_oi_barriers(self.option_chain, self.current_price, self.updated_at)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "type": "snapshot",
                "mode": self.mode,
                "sequence": self.sequence,
                "timestamp": self.updated_at.isoformat(),
                "current_price": round(self.current_price, 2),
                "oim": round(self.oim, 4),
                "micro_price": None if self.micro_price is None else round(self.micro_price, 4),
                "bid_total": round(self.bid_total, 2),
                "ask_total": round(self.ask_total, 2),
                "barriers": deepcopy(self.barriers),
                "option_chain": deepcopy(self.option_chain),
            }

    def set_price(self, price: float) -> list[dict[str, Any]]:
        with self._lock:
            self.current_price = round(float(price), 2)
            self._touch()
            self._recalculate()
            return [
                self.futures_tick_event(),
                deepcopy(self.barriers),
                self.oi_snapshot_event(),
            ]

    def set_option_chain(self, chain: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._lock:
            self.option_chain = deepcopy(chain)
            self._touch()
            self._recalculate()
            return [deepcopy(self.barriers), self.oi_snapshot_event()]

    def set_orderbook(
        self,
        bid_total: float,
        ask_total: float,
        best_bid: float | None = None,
        best_ask: float | None = None,
        bid_size: float | None = None,
        ask_size: float | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self.bid_total = float(bid_total or 0)
            self.ask_total = float(ask_total or 0)
            self.oim = calculate_oim(self.bid_total, self.ask_total)
            self.micro_price = micro_price(best_bid, best_ask, bid_size, ask_size)
            self._touch()
            return self.orderbook_event()

    def futures_tick_event(self) -> dict[str, Any]:
        return {
            "type": "futures_tick",
            "sequence": self.sequence,
            "timestamp": self.updated_at.isoformat(),
            "FUTS_PRPR": round(self.current_price, 2),
            "current_price": round(self.current_price, 2),
        }

    def orderbook_event(self) -> dict[str, Any]:
        return {
            "type": "orderbook",
            "sequence": self.sequence,
            "timestamp": self.updated_at.isoformat(),
            "bid_total": round(self.bid_total, 2),
            "ask_total": round(self.ask_total, 2),
            "oim": round(self.oim, 4),
            "micro_price": None if self.micro_price is None else round(self.micro_price, 4),
        }

    def oi_snapshot_event(self) -> dict[str, Any]:
        return {
            "type": "oi_snapshot",
            "sequence": self.sequence,
            "timestamp": self.updated_at.isoformat(),
            "current_price": round(self.current_price, 2),
            "oi_data": deepcopy(self.barriers["oi_data"]),
            "put_wall": deepcopy(self.barriers["put_wall"]),
            "call_wall": deepcopy(self.barriers["call_wall"]),
            "max_pain": self.barriers["max_pain"],
            "gamma_flip": self.barriers["gamma_flip"],
            "put_call_ratio": self.barriers["put_call_ratio"],
            "alerts": deepcopy(self.barriers["alerts"]),
        }

    def next_mock_events(self) -> list[dict[str, Any]]:
        with self._lock:
            drift = random.uniform(-0.16, 0.18)
            self.current_price = round(max(330.0, min(380.0, self.current_price + drift)), 2)

            chain = build_mock_chain(self.current_price)
            for row in chain:
                row["call_oi"] = round(row["call_oi"] * random.uniform(0.985, 1.015), 0)
                row["put_oi"] = round(row["put_oi"] * random.uniform(0.985, 1.015), 0)
            self.option_chain = chain

            base = 28_000
            imbalance = random.uniform(-0.22, 0.22)
            self.bid_total = round(base * (1 + imbalance) + random.uniform(-1800, 1800), 0)
            self.ask_total = round(base * (1 - imbalance) + random.uniform(-1800, 1800), 0)
            self.oim = calculate_oim(self.bid_total, self.ask_total)
            self.micro_price = round(self.current_price + (self.oim * 0.35), 4)
            self._touch()
            self._recalculate()
            return [
                self.futures_tick_event(),
                self.orderbook_event(),
                deepcopy(self.barriers),
                self.oi_snapshot_event(),
            ]


market_state = MarketStateStore()
