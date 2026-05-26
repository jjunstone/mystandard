from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from collector.auth import KISConfig, load_kis_config


logger = logging.getLogger("kquant.kis_rest")


class KISRestClient:
    """Small REST adapter for KIS-style TR calls.

    The exact option OI TR can differ by account/product permission, so the path
    and TR id are configurable through env vars.  The rest of the app only needs
    normalized rows: strike, call_oi, put_oi.
    """

    def __init__(self, config: KISConfig | None = None, timeout: float = 5.0) -> None:
        self.config = config or load_kis_config()
        self.timeout = timeout
        self._token: str | None = None

    async def token(self) -> str:
        if self._token:
            return self._token
        if not self.config.has_credentials:
            raise RuntimeError("KIS credentials are not configured")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.config.api_base}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.config.app_key,
                    "appsecret": self.config.app_secret,
                },
            )
            response.raise_for_status()
            payload = response.json()
            self._token = payload["access_token"]
            logger.info("KIS REST token issued")
            return self._token

    async def request_tr(self, path: str, tr_id: str, params: dict[str, Any]) -> dict[str, Any]:
        access_token = await self.token()
        headers = {
            "authorization": f"Bearer {access_token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.config.api_base}{path}", headers=headers, params=params)
            response.raise_for_status()
            logger.info("KIS REST TR completed tr_id=%s status=%s", tr_id, response.status_code)
            return response.json()

    async def fetch_option_oi(self, params: dict[str, Any]) -> list[dict[str, float]]:
        path = os.getenv("KIS_OPTION_OI_PATH", "")
        tr_id = os.getenv("KIS_OPTION_OI_TR_ID", "")
        if not path or not tr_id:
            raise RuntimeError("KIS_OPTION_OI_PATH and KIS_OPTION_OI_TR_ID must be configured")
        payload = await self.request_tr(path, tr_id, params)
        return normalize_option_oi_payload(payload)


def normalize_option_oi_payload(payload: dict[str, Any]) -> list[dict[str, float]]:
    rows = payload.get("output") or payload.get("output1") or payload.get("data") or []
    if isinstance(rows, dict):
        rows = rows.get("rows") or rows.get("list") or []
    normalized: list[dict[str, float]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "strike": _number(row, "strike", "stk_prc", "acpr"),
                "call_oi": _number(row, "call_oi", "call", "call_open_interest", "clpr_oprc"),
                "put_oi": _number(row, "put_oi", "put", "put_open_interest", "ptpr_oprc"),
                "call_volume": _number(row, "call_volume", "call_vol", "clpr_vol"),
                "put_volume": _number(row, "put_volume", "put_vol", "ptpr_vol"),
            }
        )
    return [row for row in normalized if row["strike"] > 0 and (row["call_oi"] > 0 or row["put_oi"] > 0)]


def _number(row: dict[str, Any], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        try:
            return float(str(value).replace(",", "").strip())
        except ValueError:
            continue
    return 0.0
