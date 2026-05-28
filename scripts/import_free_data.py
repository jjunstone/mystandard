from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT_DIR / "db" / "free_inputs"
DEFAULT_OUTPUT = ROOT_DIR / "db" / "eod_snapshot.json"

INVESTOR_IDS = {
    "외국인": "foreign",
    "외인": "foreign",
    "foreign": "foreign",
    "기관": "institution",
    "institution": "institution",
    "개인": "individual",
    "individual": "individual",
}

INVESTOR_NAMES = {
    "foreign": "외국인",
    "institution": "기관",
    "individual": "개인",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build db/eod_snapshot.json from free daily CSV inputs.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    snapshot = write_snapshot(args.input_dir, args.output)
    print(f"wrote {args.output}")
    print(f"as_of={snapshot['as_of']} investors={len(snapshot['investors'])} options={len(snapshot['options'])}")


def write_snapshot(input_dir: Path = DEFAULT_INPUT_DIR, output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    snapshot = build_snapshot(input_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot


def build_snapshot(input_dir: Path) -> dict[str, Any]:
    indices_rows = read_csv(input_dir / "indices.csv")
    investor_rows = read_csv(input_dir / "investors.csv")
    option_rows = read_csv(input_dir / "options.csv")
    leader_rows = read_csv(input_dir / "leaders.csv") if (input_dir / "leaders.csv").exists() else []
    history_rows = read_csv(input_dir / "history.csv") if (input_dir / "history.csv").exists() else []

    if not indices_rows:
        raise ValueError("indices.csv needs at least one row.")
    if not investor_rows:
        raise ValueError("investors.csv needs 외국인/기관/개인 rows.")
    if not option_rows:
        raise ValueError("options.csv needs strike-level OI rows.")

    as_of = first_value(indices_rows[0], "as_of", "date", default="")
    if not as_of:
        as_of = first_value(investor_rows[0], "as_of", "date", default="")

    return {
        "as_of": as_of,
        "source": "free-csv",
        "mode": "eod",
        "indices": parse_indices(indices_rows[0]),
        "investors": parse_investors(investor_rows),
        "options": parse_options(option_rows),
        "leaders": parse_leaders(leader_rows),
        "history": parse_history(history_rows),
    }


def parse_indices(row: dict[str, str]) -> dict[str, Any]:
    return {
        "kospi": {
            "value": number(first_value(row, "kospi", "KOSPI")),
            "change": number(first_value(row, "kospi_change", "KOSPI_change")),
            "change_pct": number(first_value(row, "kospi_change_pct", "KOSPI_change_pct")),
        },
        "kospi200": {
            "value": number(first_value(row, "kospi200", "KOSPI200")),
            "change": number(first_value(row, "kospi200_change", "KOSPI200_change")),
            "change_pct": number(first_value(row, "kospi200_change_pct", "KOSPI200_change_pct")),
        },
        "vkospi": {
            "value": number(first_value(row, "vkospi", "VKOSPI"), default=0),
            "change": number(first_value(row, "vkospi_change", "VKOSPI_change"), default=0),
        },
        "basis": {"value": number(first_value(row, "basis"), default=0)},
        "usdkrw": {
            "value": number(first_value(row, "usdkrw", "USD_KRW"), default=0),
            "change": number(first_value(row, "usdkrw_change", "USD_KRW_change"), default=0),
        },
    }


def parse_investors(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    parsed = []
    for row in rows:
        label = first_value(row, "investor", "name", "투자자")
        investor_id = INVESTOR_IDS.get(label.strip(), label.strip())
        parsed.append(
            {
                "id": investor_id,
                "name": INVESTOR_NAMES.get(investor_id, label),
                "spot_net_bil": money_to_bil(row, "spot_net_bil", "spot_net_eok", "현물순매수"),
                "futures_net_contracts": number(first_value(row, "futures_net_contracts", "선물순매수")),
                "futures_cum_5d": number(first_value(row, "futures_cum_5d", "선물5일누적"), default=0),
                "call_net_contracts": number(first_value(row, "call_net_contracts", "콜순매수"), default=0),
                "put_net_contracts": number(first_value(row, "put_net_contracts", "풋순매수"), default=0),
                "option_premium_bil": money_to_bil(row, "option_premium_bil", "option_premium_eok", "옵션순매수"),
            }
        )
    return sorted(parsed, key=lambda row: ["foreign", "institution", "individual"].index(row["id"]) if row["id"] in ["foreign", "institution", "individual"] else 99)


def parse_options(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "strike": number(first_value(row, "strike", "행사가")),
                "call_oi": number(first_value(row, "call_oi", "콜미결제")),
                "put_oi": number(first_value(row, "put_oi", "풋미결제")),
                "call_delta": number(first_value(row, "call_delta", "콜미결제증감"), default=0),
                "put_delta": number(first_value(row, "put_delta", "풋미결제증감"), default=0),
                "call_volume": number(first_value(row, "call_volume", "콜거래량"), default=0),
                "put_volume": number(first_value(row, "put_volume", "풋거래량"), default=0),
            }
            for row in rows
        ],
        key=lambda row: row["strike"],
    )


def parse_leaders(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "name": first_value(row, "name", "종목명"),
            "sector": first_value(row, "sector", "업종", default=""),
            "change_pct": number(first_value(row, "change_pct", "등락률"), default=0),
        }
        for row in rows
    ]


def parse_history(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "date": first_value(row, "date", "일자"),
            "foreign_futures": number(first_value(row, "foreign_futures", "외국인선물"), default=0),
            "institution_futures": number(first_value(row, "institution_futures", "기관선물"), default=0),
            "individual_futures": number(first_value(row, "individual_futures", "개인선물"), default=0),
            "score": number(first_value(row, "score", "점수"), default=50),
        }
        for row in rows
    ]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [{clean_key(k): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(file)]


def clean_key(key: str | None) -> str:
    return (key or "").strip().replace(" ", "_")


def first_value(row: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(clean_key(key))
        if value not in (None, ""):
            return value
    return default


def money_to_bil(row: dict[str, str], bil_key: str, eok_key: str, korean_key: str) -> float:
    bil = first_value(row, bil_key)
    if bil:
        return number(bil)
    eok = first_value(row, eok_key, korean_key)
    return number(eok, default=0) / 10


def number(value: str | int | float, default: float = 0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(",", "").replace("%", "").replace("−", "-").strip()
    if cleaned in ("", "-"):
        return default
    return float(cleaned)


if __name__ == "__main__":
    main()
