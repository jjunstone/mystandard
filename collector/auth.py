from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class KISConfig:
    app_key: str
    app_secret: str
    account: str
    api_base: str
    ws_base: str
    mode: str = "mock"

    @property
    def has_credentials(self) -> bool:
        return bool(self.app_key and self.app_secret)


def load_kis_config() -> KISConfig:
    load_dotenv()
    return KISConfig(
        app_key=os.getenv("KIS_APP_KEY", ""),
        app_secret=os.getenv("KIS_APP_SECRET", ""),
        account=os.getenv("KIS_ACCOUNT", ""),
        api_base=os.getenv("KIS_API_BASE", "https://openapi.koreainvestment.com:9443").rstrip("/"),
        ws_base=os.getenv("KIS_WS_BASE", "ws://ops.koreainvestment.com:21000").rstrip("/"),
        mode=os.getenv("KQUANT_MODE", "mock"),
    )
