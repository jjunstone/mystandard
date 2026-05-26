from __future__ import annotations

import asyncio
import logging
from typing import Any

from collector.publisher import publish_option_chain
from collector.rest_client import KISRestClient


logger = logging.getLogger("kquant.scheduler")


async def poll_option_oi(params: dict[str, Any], interval_seconds: float = 15.0) -> None:
    client = KISRestClient()
    while True:
        try:
            rows = await client.fetch_option_oi(params)
            publish_option_chain(rows)
            logger.info("option OI snapshot updated rows=%s", len(rows))
        except Exception:
            logger.exception("option OI polling failed")
        await asyncio.sleep(interval_seconds)
