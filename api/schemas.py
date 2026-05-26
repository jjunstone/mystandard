from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OptionOIRow(BaseModel):
    strike: float
    call_oi: float = Field(default=0, ge=0)
    put_oi: float = Field(default=0, ge=0)
    call_volume: float = Field(default=0, ge=0)
    put_volume: float = Field(default=0, ge=0)


class OptionChainPayload(BaseModel):
    current_price: float | None = None
    rows: list[OptionOIRow]
    update_state: bool = True


class PriceTickPayload(BaseModel):
    current_price: float = Field(gt=0)


class OrderbookPayload(BaseModel):
    bid_total: float = Field(default=0, ge=0)
    ask_total: float = Field(default=0, ge=0)
    best_bid: float | None = Field(default=None, gt=0)
    best_ask: float | None = Field(default=None, gt=0)
    bid_size: float | None = Field(default=None, ge=0)
    ask_size: float | None = Field(default=None, ge=0)


class ApiResponse(BaseModel):
    ok: bool = True
    data: dict[str, Any] | list[dict[str, Any]]
