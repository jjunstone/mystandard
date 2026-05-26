"""Open-interest barrier calculations for KOSPI 200 options.

The engine is intentionally independent from any broker API.  Feed it a chain
of strikes with call/put open interest and it returns the levels the dashboard
needs: put wall, call wall, max pain, distance to spot, and normalized rows for
the OI bar chart.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp
from typing import Any, Iterable


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if not value:
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _round_price(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


@dataclass(frozen=True)
class OptionOI:
    strike: float
    call_oi: float
    put_oi: float
    call_volume: float = 0.0
    put_volume: float = 0.0

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "OptionOI":
        return cls(
            strike=_to_float(row.get("strike") or row.get("stk_prc")),
            call_oi=_to_float(row.get("call_oi", row.get("call", row.get("callOpenInterest")))),
            put_oi=_to_float(row.get("put_oi", row.get("put", row.get("putOpenInterest")))),
            call_volume=_to_float(row.get("call_volume", row.get("callVolume"))),
            put_volume=_to_float(row.get("put_volume", row.get("putVolume"))),
        )


@dataclass(frozen=True)
class BarrierLevel:
    kind: str
    strike: float | None
    open_interest: float
    strength: float
    distance: float | None
    distance_pct: float | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "strike": _round_price(self.strike),
            "open_interest": round(self.open_interest, 2),
            "strength": round(self.strength, 4),
            "distance": _round_price(self.distance),
            "distance_pct": None if self.distance_pct is None else round(self.distance_pct, 4),
            "status": self.status,
        }


def _status_for(kind: str, strike: float | None, current_price: float | None) -> str:
    if strike is None or current_price is None:
        return "unknown"
    distance = strike - current_price
    if abs(distance) <= 0.25:
        return "touch"
    if kind == "call_wall":
        return "breached" if current_price > strike else "above_spot"
    if kind == "put_wall":
        return "breached" if current_price < strike else "below_spot"
    return "unknown"


def _distance(strike: float | None, current_price: float | None) -> tuple[float | None, float | None]:
    if strike is None or current_price in (None, 0):
        return None, None
    distance = strike - current_price
    return distance, distance / current_price * 100


def _wall_strength(open_interest: float, side_total: float) -> float:
    if side_total <= 0:
        return 0.0
    return max(0.0, min(1.0, open_interest / side_total))


def _choose_wall(
    rows: list[OptionOI],
    side: str,
    current_price: float | None,
    min_side_oi: float = 0.0,
) -> OptionOI | None:
    if not rows:
        return None
    if side == "call":
        candidates = [row for row in rows if row.call_oi >= min_side_oi]
        if current_price is not None:
            above = [row for row in candidates if row.strike >= current_price]
            candidates = above or candidates
        return max(candidates, key=lambda row: (row.call_oi, -abs(row.strike - (current_price or row.strike))))
    candidates = [row for row in rows if row.put_oi >= min_side_oi]
    if current_price is not None:
        below = [row for row in candidates if row.strike <= current_price]
        candidates = below or candidates
    return max(candidates, key=lambda row: (row.put_oi, -abs(row.strike - (current_price or row.strike))))


def _max_pain(rows: list[OptionOI]) -> float | None:
    if not rows:
        return None
    best_strike: float | None = None
    best_pain: float | None = None
    strikes = [row.strike for row in rows]
    for settlement in strikes:
        pain = 0.0
        for row in rows:
            pain += row.call_oi * max(settlement - row.strike, 0.0)
            pain += row.put_oi * max(row.strike - settlement, 0.0)
        if best_pain is None or pain < best_pain:
            best_pain = pain
            best_strike = settlement
    return best_strike


def _gamma_flip_proxy(rows: list[OptionOI]) -> float | None:
    """Cheap proxy until a real Greeks feed is attached.

    It marks where cumulative put dominance changes into call dominance.
    """

    if not rows:
        return None
    running = 0.0
    previous: tuple[float, float] | None = None
    for row in rows:
        running += row.call_oi - row.put_oi
        if previous is not None and previous[1] <= 0 < running:
            return row.strike
        previous = (row.strike, running)
    return min(rows, key=lambda row: abs(row.call_oi - row.put_oi)).strike


def normalize_chain(chain: Iterable[OptionOI | dict[str, Any]]) -> list[OptionOI]:
    rows: list[OptionOI] = []
    for item in chain:
        row = item if isinstance(item, OptionOI) else OptionOI.from_mapping(item)
        if row.strike > 0 and (row.call_oi > 0 or row.put_oi > 0):
            rows.append(row)
    return sorted(rows, key=lambda row: row.strike)


def calculate_oi_barriers(
    chain: Iterable[OptionOI | dict[str, Any]],
    current_price: float | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    rows = normalize_chain(chain)
    if not rows:
        raise ValueError("option chain is empty")

    total_call_oi = sum(row.call_oi for row in rows)
    total_put_oi = sum(row.put_oi for row in rows)
    total_oi = total_call_oi + total_put_oi
    call_wall_row = _choose_wall(rows, "call", current_price)
    put_wall_row = _choose_wall(rows, "put", current_price)
    call_dist, call_dist_pct = _distance(call_wall_row.strike if call_wall_row else None, current_price)
    put_dist, put_dist_pct = _distance(put_wall_row.strike if put_wall_row else None, current_price)

    call_wall = BarrierLevel(
        kind="call_wall",
        strike=call_wall_row.strike if call_wall_row else None,
        open_interest=call_wall_row.call_oi if call_wall_row else 0.0,
        strength=_wall_strength(call_wall_row.call_oi if call_wall_row else 0.0, total_call_oi),
        distance=call_dist,
        distance_pct=call_dist_pct,
        status=_status_for("call_wall", call_wall_row.strike if call_wall_row else None, current_price),
    )
    put_wall = BarrierLevel(
        kind="put_wall",
        strike=put_wall_row.strike if put_wall_row else None,
        open_interest=put_wall_row.put_oi if put_wall_row else 0.0,
        strength=_wall_strength(put_wall_row.put_oi if put_wall_row else 0.0, total_put_oi),
        distance=put_dist,
        distance_pct=put_dist_pct,
        status=_status_for("put_wall", put_wall_row.strike if put_wall_row else None, current_price),
    )

    max_pain = _max_pain(rows)
    gamma_flip = _gamma_flip_proxy(rows)
    highlighted = {
        value
        for value in (call_wall.strike, put_wall.strike, max_pain)
        if value is not None
    }
    max_side_oi = max(max(row.call_oi, row.put_oi) for row in rows) or 1.0
    oi_data = [
        {
            "strike": _round_price(row.strike),
            "call": round(row.call_oi, 2),
            "put": round(row.put_oi, 2),
            "call_oi": round(row.call_oi, 2),
            "put_oi": round(row.put_oi, 2),
            "total_oi": round(row.call_oi + row.put_oi, 2),
            "net_oi": round(row.put_oi - row.call_oi, 2),
            "intensity": round(max(row.call_oi, row.put_oi) / max_side_oi, 4),
            "highlight": row.strike in highlighted,
        }
        for row in rows
    ]

    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else None
    now = timestamp or datetime.now(timezone.utc)
    dominant_side = "put" if total_put_oi > total_call_oi else "call"
    if abs(total_put_oi - total_call_oi) / max(total_oi, 1.0) < 0.05:
        dominant_side = "balanced"

    return {
        "type": "barriers",
        "timestamp": now.isoformat(),
        "underlying_price": _round_price(current_price),
        "current_price": _round_price(current_price),
        "put_wall": put_wall.to_dict(),
        "call_wall": call_wall.to_dict(),
        "max_pain": _round_price(max_pain),
        "gamma_flip": _round_price(gamma_flip),
        "total_call_oi": round(total_call_oi, 2),
        "total_put_oi": round(total_put_oi, 2),
        "put_call_ratio": None if pcr is None else round(pcr, 4),
        "dominant_side": dominant_side,
        "oi_data": oi_data,
        "range": {
            "support": _round_price(put_wall.strike),
            "resistance": _round_price(call_wall.strike),
            "width": _round_price((call_wall.strike - put_wall.strike) if call_wall.strike and put_wall.strike else None),
        },
        "alerts": build_barrier_alerts(current_price, put_wall, call_wall),
    }


def build_barrier_alerts(
    current_price: float | None,
    put_wall: BarrierLevel,
    call_wall: BarrierLevel,
    touch_threshold: float = 0.75,
) -> list[dict[str, Any]]:
    if current_price is None:
        return []
    alerts: list[dict[str, Any]] = []
    for wall in (put_wall, call_wall):
        if wall.strike is None or wall.distance is None:
            continue
        abs_distance = abs(wall.distance)
        if wall.status == "breached":
            severity = "danger"
            message = f"{wall.kind} breached at {wall.strike:.2f}"
        elif abs_distance <= touch_threshold:
            severity = "watch"
            message = f"{wall.kind} near touch: {abs_distance:.2f}pt"
        else:
            continue
        alerts.append(
            {
                "kind": wall.kind,
                "severity": severity,
                "strike": _round_price(wall.strike),
                "distance": _round_price(wall.distance),
                "message": message,
            }
        )
    return alerts


def calculate_oim(bid_total: Any, ask_total: Any) -> float:
    bid = max(_to_float(bid_total), 0.0)
    ask = max(_to_float(ask_total), 0.0)
    denominator = bid + ask
    if denominator <= 0:
        return 0.0
    return round(max(-1.0, min(1.0, (bid - ask) / denominator)), 4)


def micro_price(best_bid: Any, best_ask: Any, bid_size: Any, ask_size: Any) -> float | None:
    bid = _to_float(best_bid)
    ask = _to_float(best_ask)
    bid_qty = max(_to_float(bid_size), 0.0)
    ask_qty = max(_to_float(ask_size), 0.0)
    total_qty = bid_qty + ask_qty
    if bid <= 0 or ask <= 0 or total_qty <= 0:
        return None
    return round((ask * bid_qty + bid * ask_qty) / total_qty, 4)


def build_mock_chain(current_price: float = 353.72) -> list[dict[str, float]]:
    """Deterministic mock chain shaped like real option OI walls."""

    rows: list[dict[str, float]] = []
    for strike in [345, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 360]:
        call_base = 900 + max(strike - current_price, -1.5) * 180
        put_base = 900 + max(current_price - strike, -1.5) * 170
        call_wall_boost = 5200 * exp(-((strike - 355.0) ** 2) / 1.1)
        put_wall_boost = 4700 * exp(-((strike - 350.0) ** 2) / 1.25)
        max_pain_boost = 1400 * exp(-((strike - 352.5) ** 2) / 1.8)
        rows.append(
            {
                "strike": float(strike),
                "call_oi": round(max(call_base, 100) + call_wall_boost + max_pain_boost, 0),
                "put_oi": round(max(put_base, 100) + put_wall_boost + max_pain_boost, 0),
                "call_volume": round(max(call_base, 100) * 0.18, 0),
                "put_volume": round(max(put_base, 100) * 0.18, 0),
            }
        )
    return rows
