from __future__ import annotations

import asyncio
import contextlib
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.state import market_state


router = APIRouter(tags=["websocket"])
logger = logging.getLogger("kquant.websocket")


@router.websocket("/ws/stream")
async def stream_market_state(websocket: WebSocket) -> None:
    await websocket.accept()
    peer = websocket.client.host if websocket.client else "unknown"
    logger.info("websocket connected peer=%s", peer)
    try:
        await websocket.send_json(market_state.snapshot())
        while True:
            events = market_state.next_mock_events() if market_state.mode == "mock" else [market_state.snapshot()]
            for event in events:
                await websocket.send_json(event)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("websocket disconnected peer=%s", peer)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("websocket stream failed peer=%s", peer)
        with contextlib.suppress(Exception):
            await websocket.close(code=1011)
