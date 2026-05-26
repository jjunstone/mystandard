from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable
from typing import Any

import websockets

from collector.auth import KISConfig, load_kis_config
from collector.publisher import publish_orderbook, publish_price_tick


logger = logging.getLogger("kquant.kis_ws")


class KISWebSocketClient:
    """Generic websocket collector shell.

    It intentionally logs connection state only, not live quote payloads.
    Product-specific subscribe packets can be supplied from the caller once the
    exact KIS TR ids and symbols are confirmed.
    """

    def __init__(self, config: KISConfig | None = None) -> None:
        self.config = config or load_kis_config()

    async def run(self, subscribe_packets: Iterable[dict[str, Any]]) -> None:
        async with websockets.connect(self.config.ws_base) as ws:
            logger.info("KIS websocket connected")
            for packet in subscribe_packets:
                await ws.send(json.dumps(packet, ensure_ascii=False))
            async for raw in ws:
                self.handle_message(raw)

    def handle_message(self, raw: str | bytes) -> None:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return
        event_type = data.get("type") or data.get("tr_id")
        if event_type in {"futures_tick", "H0IFCNT0"}:
            price = data.get("current_price") or data.get("FUTS_PRPR") or data.get("futs_prpr")
            if price is not None:
                publish_price_tick(float(price))
        elif event_type in {"orderbook", "H0IFASP0"}:
            bid_total = data.get("bid_total") or data.get("bidp_rsqn") or 0
            ask_total = data.get("ask_total") or data.get("askp_rsqn") or 0
            publish_orderbook(float(bid_total), float(ask_total))


async def run_forever(subscribe_packets: Iterable[dict[str, Any]]) -> None:
    client = KISWebSocketClient()
    while True:
        try:
            await client.run(subscribe_packets)
        except Exception:
            logger.exception("KIS websocket collector restarted")
            await asyncio.sleep(3)
