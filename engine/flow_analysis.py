from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


SAMPLE_SNAPSHOT: dict[str, Any] = {
    "as_of": "2026-05-26",
    "source": "sample-eod",
    "indices": {
        "kospi": {"value": 8047.51, "change": 201.30, "change_pct": 2.55},
        "kospi200": {"value": 1226.03, "change": 0.81, "change_pct": 0.07},
        "vkospi": {"value": 18.72, "change": -0.84},
        "basis": {"value": 0.42},
        "usdkrw": {"value": 1358.40, "change": -4.60},
    },
    "investors": [
        {
            "id": "foreign",
            "name": "외국인",
            "spot_net_bil": 842.5,
            "futures_net_contracts": 6384,
            "futures_cum_5d": 18420,
            "call_net_contracts": 28400,
            "put_net_contracts": -12800,
            "option_premium_bil": 52.1,
        },
        {
            "id": "institution",
            "name": "기관",
            "spot_net_bil": -214.2,
            "futures_net_contracts": -1180,
            "futures_cum_5d": -4680,
            "call_net_contracts": -4200,
            "put_net_contracts": 6200,
            "option_premium_bil": -11.4,
        },
        {
            "id": "individual",
            "name": "개인",
            "spot_net_bil": -612.7,
            "futures_net_contracts": -5204,
            "futures_cum_5d": -13740,
            "call_net_contracts": -24200,
            "put_net_contracts": 7600,
            "option_premium_bil": -38.8,
        },
    ],
    "options": [
        {"strike": 1185, "call_oi": 8200, "put_oi": 35100, "call_delta": 410, "put_delta": 1840, "call_volume": 3210, "put_volume": 8420},
        {"strike": 1190, "call_oi": 10400, "put_oi": 38900, "call_delta": 620, "put_delta": 2110, "call_volume": 4180, "put_volume": 9160},
        {"strike": 1195, "call_oi": 12800, "put_oi": 42300, "call_delta": 780, "put_delta": 2660, "call_volume": 4620, "put_volume": 10340},
        {"strike": 1200, "call_oi": 16600, "put_oi": 51400, "call_delta": 1260, "put_delta": 3920, "call_volume": 6230, "put_volume": 11880},
        {"strike": 1205, "call_oi": 21400, "put_oi": 46300, "call_delta": 1880, "put_delta": 3010, "call_volume": 7280, "put_volume": 9710},
        {"strike": 1210, "call_oi": 26400, "put_oi": 38200, "call_delta": 2380, "put_delta": 1880, "call_volume": 8450, "put_volume": 7420},
        {"strike": 1215, "call_oi": 33800, "put_oi": 27400, "call_delta": 3420, "put_delta": 620, "call_volume": 10320, "put_volume": 5840},
        {"strike": 1220, "call_oi": 42700, "put_oi": 21800, "call_delta": 4820, "put_delta": -240, "call_volume": 12840, "put_volume": 4620},
        {"strike": 1225, "call_oi": 51600, "put_oi": 16600, "call_delta": 5660, "put_delta": -820, "call_volume": 14320, "put_volume": 3620},
        {"strike": 1230, "call_oi": 60200, "put_oi": 12100, "call_delta": 6420, "put_delta": -1140, "call_volume": 15680, "put_volume": 2810},
        {"strike": 1235, "call_oi": 48800, "put_oi": 9300, "call_delta": 2840, "put_delta": -980, "call_volume": 11740, "put_volume": 2140},
        {"strike": 1240, "call_oi": 68400, "put_oi": 7600, "call_delta": 8120, "put_delta": -620, "call_volume": 16920, "put_volume": 1680},
        {"strike": 1245, "call_oi": 33200, "put_oi": 5200, "call_delta": 1480, "put_delta": -420, "call_volume": 8240, "put_volume": 1040},
        {"strike": 1250, "call_oi": 24600, "put_oi": 4100, "call_delta": 920, "put_delta": -260, "call_volume": 6420, "put_volume": 820},
    ],
    "leaders": [
        {"name": "SK하이닉스", "sector": "반도체", "change_pct": 4.82},
        {"name": "삼성전자", "sector": "반도체", "change_pct": 3.24},
        {"name": "한화에어로스페이스", "sector": "방산", "change_pct": 8.42},
        {"name": "현대로템", "sector": "방산", "change_pct": 6.18},
        {"name": "두산에너빌리티", "sector": "원전", "change_pct": 5.34},
    ],
    "history": [
        {"date": "05-20", "foreign_futures": 4820, "institution_futures": -940, "individual_futures": -3880, "score": 68},
        {"date": "05-21", "foreign_futures": 3120, "institution_futures": 460, "individual_futures": -3580, "score": 65},
        {"date": "05-22", "foreign_futures": -820, "institution_futures": 1260, "individual_futures": -440, "score": 49},
        {"date": "05-23", "foreign_futures": 7140, "institution_futures": -1880, "individual_futures": -5260, "score": 73},
        {"date": "05-26", "foreign_futures": 6384, "institution_futures": -1180, "individual_futures": -5204, "score": 75},
    ],
}


def analyze_snapshot(raw_snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot = deepcopy(raw_snapshot)
    options = sorted(snapshot.get("options", []), key=lambda row: _number(row.get("strike")))
    investors = snapshot.get("investors", [])
    indices = snapshot.get("indices", {})

    kospi200 = indices.get("kospi200", {})
    current_price = _number(kospi200.get("value"))
    price_change = _number(kospi200.get("change"))

    option_summary = _analyze_options(options, current_price)
    investor_cards = [_analyze_investor(row) for row in investors]
    by_id = {row["id"]: row for row in investor_cards}

    foreign = by_id.get("foreign", {})
    institution = by_id.get("institution", {})
    individual = by_id.get("individual", {})

    oi_state = _classify_oi_state(price_change, option_summary["total_oi_delta"])
    regime_score = _score_regime(foreign, institution, individual, option_summary, indices, oi_state)
    regime = _regime_from_score(regime_score)
    confidence = _confidence_label(regime_score)
    trade_plan = _build_trade_plan(regime, current_price, option_summary)
    observations = _build_observations(regime, investor_cards, option_summary, oi_state, indices)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of": snapshot.get("as_of"),
        "source": snapshot.get("source", "unknown"),
        "mode": snapshot.get("mode", "eod"),
        "indices": indices,
        "investors": investor_cards,
        "option_summary": option_summary,
        "oi_state": oi_state,
        "analysis": {
            "regime": regime,
            "score": regime_score,
            "confidence": confidence,
            "headline": _headline(regime, confidence),
            "observations": observations,
            "trade_plan": trade_plan,
        },
        "options": _decorate_options(options, option_summary),
        "leaders": snapshot.get("leaders", []),
        "history": snapshot.get("history", []),
    }


def _analyze_options(options: list[dict[str, Any]], current_price: float) -> dict[str, Any]:
    total_call_oi = sum(_number(row.get("call_oi")) for row in options)
    total_put_oi = sum(_number(row.get("put_oi")) for row in options)
    total_call_vol = sum(_number(row.get("call_volume")) for row in options)
    total_put_vol = sum(_number(row.get("put_volume")) for row in options)
    total_oi_delta = sum(_number(row.get("call_delta")) + _number(row.get("put_delta")) for row in options)

    call_wall = max(options, key=lambda row: _number(row.get("call_oi")), default={"strike": 0, "call_oi": 0})
    put_wall = max(options, key=lambda row: _number(row.get("put_oi")), default={"strike": 0, "put_oi": 0})
    max_pain = _max_pain(options)

    return {
        "total_call_oi": round(total_call_oi),
        "total_put_oi": round(total_put_oi),
        "total_call_volume": round(total_call_vol),
        "total_put_volume": round(total_put_vol),
        "total_oi_delta": round(total_oi_delta),
        "pcr_oi": _safe_ratio(total_put_oi, total_call_oi),
        "pcr_volume": _safe_ratio(total_put_vol, total_call_vol),
        "call_wall": {"strike": _number(call_wall.get("strike")), "oi": round(_number(call_wall.get("call_oi")))},
        "put_wall": {"strike": _number(put_wall.get("strike")), "oi": round(_number(put_wall.get("put_oi")))},
        "max_pain": max_pain,
        "distance_to_call_wall": round(_number(call_wall.get("strike")) - current_price, 2),
        "distance_to_put_wall": round(current_price - _number(put_wall.get("strike")), 2),
    }


def _analyze_investor(row: dict[str, Any]) -> dict[str, Any]:
    spot = _number(row.get("spot_net_bil"))
    futures = _number(row.get("futures_net_contracts"))
    futures_cum = _number(row.get("futures_cum_5d"))
    call_net = _number(row.get("call_net_contracts"))
    put_net = _number(row.get("put_net_contracts"))
    option_tilt = call_net - put_net

    score = 0
    score += _clamp(spot / 900 * 18, -18, 18)
    score += _clamp(futures / 5500 * 26, -26, 26)
    score += _clamp(futures_cum / 18000 * 16, -16, 16)
    score += _clamp(option_tilt / 45000 * 12, -12, 12)
    score = round(score)

    if score >= 32:
        posture = "강한 상방"
        tone = "bull"
    elif score >= 12:
        posture = "상방 우위"
        tone = "bull"
    elif score <= -32:
        posture = "강한 하방"
        tone = "bear"
    elif score <= -12:
        posture = "하방 우위"
        tone = "bear"
    else:
        posture = "중립"
        tone = "neutral"

    flow_text = _flow_text(spot, futures, option_tilt)
    return {
        **row,
        "score": score,
        "posture": posture,
        "tone": tone,
        "option_tilt": round(option_tilt),
        "summary": flow_text,
    }


def _score_regime(
    foreign: dict[str, Any],
    institution: dict[str, Any],
    individual: dict[str, Any],
    options: dict[str, Any],
    indices: dict[str, Any],
    oi_state: dict[str, Any],
) -> int:
    score = 50
    score += _number(foreign.get("score")) * 0.36
    score += _number(institution.get("score")) * 0.12
    score -= _number(individual.get("score")) * 0.10

    pcr_oi = _number(options.get("pcr_oi"))
    pcr_vol = _number(options.get("pcr_volume"))
    if pcr_oi < 0.85 and pcr_vol < 0.9:
        score += 5
    elif pcr_oi > 1.18 and pcr_vol > 1.1:
        score -= 5

    basis = _number(indices.get("basis", {}).get("value"))
    if basis > 0.25:
        score += 3
    elif basis < -0.25:
        score -= 3

    if oi_state.get("direction") == "long_build":
        score += 4
    elif oi_state.get("direction") == "short_build":
        score -= 4
    elif oi_state.get("direction") == "short_cover":
        score += 3
    elif oi_state.get("direction") == "long_liquidation":
        score -= 3

    return round(_clamp(score, 0, 100))


def _build_trade_plan(regime: str, price: float, options: dict[str, Any]) -> dict[str, Any]:
    call_wall = _number(options.get("call_wall", {}).get("strike"))
    put_wall = _number(options.get("put_wall", {}).get("strike"))
    max_pain = _number(options.get("max_pain"))

    if regime == "LONG":
        return {
            "bias": "상방 추종",
            "primary": round(price, 2),
            "support": round(max(put_wall, max_pain), 2),
            "target1": round(call_wall - 1.5, 2),
            "target2": round(call_wall + 5, 2),
            "stop": round(put_wall - 3, 2),
            "note": "외국인 선물 수급이 유지되면 콜벽 전까지는 눌림 우위입니다.",
        }
    if regime == "SHORT":
        return {
            "bias": "하방 경계",
            "primary": round(price, 2),
            "support": round(put_wall + 1.5, 2),
            "target1": round(put_wall + 1.5, 2),
            "target2": round(put_wall - 5, 2),
            "stop": round(call_wall + 3, 2),
            "note": "외국인 선물 매도와 풋 OI 증가가 동시에 유지될 때만 추종합니다.",
        }
    return {
        "bias": "박스 대응",
        "primary": round(price, 2),
        "support": round(put_wall + 1, 2),
        "target1": round(max_pain, 2),
        "target2": round(call_wall - 1, 2),
        "stop": round(min(put_wall - 3, max_pain - 6), 2),
        "note": "상단 콜벽과 하단 풋벽 사이 평균회귀 가능성이 큽니다.",
    }


def _build_observations(
    regime: str,
    investors: list[dict[str, Any]],
    options: dict[str, Any],
    oi_state: dict[str, Any],
    indices: dict[str, Any],
) -> list[str]:
    top = max(investors, key=lambda row: abs(_number(row.get("score"))), default={})
    pcr_oi = _number(options.get("pcr_oi"))
    pcr_vol = _number(options.get("pcr_volume"))
    basis = _number(indices.get("basis", {}).get("value"))
    return [
        f"{top.get('name', '주요 주체')} 수급 영향력이 가장 큽니다: {top.get('posture', '중립')} ({top.get('score', 0):+}pt).",
        f"OI 구조: {oi_state.get('label')}. {oi_state.get('description')}",
        f"콜벽 {options.get('call_wall', {}).get('strike')} / 풋벽 {options.get('put_wall', {}).get('strike')} / Max Pain {options.get('max_pain')} 구간을 기준으로 봅니다.",
        f"PCR은 OI {pcr_oi:.2f}, 거래량 {pcr_vol:.2f}입니다. Basis {basis:+.2f}는 {regime} 점수에 반영됐습니다.",
    ]


def _decorate_options(options: list[dict[str, Any]], summary: dict[str, Any]) -> list[dict[str, Any]]:
    max_oi = max(
        [max(_number(row.get("call_oi")), _number(row.get("put_oi"))) for row in options],
        default=1,
    )
    call_wall = _number(summary.get("call_wall", {}).get("strike"))
    put_wall = _number(summary.get("put_wall", {}).get("strike"))
    max_pain = _number(summary.get("max_pain"))

    decorated = []
    for row in options:
        strike = _number(row.get("strike"))
        decorated.append(
            {
                **row,
                "call_width": round(_number(row.get("call_oi")) / max_oi * 100, 2),
                "put_width": round(_number(row.get("put_oi")) / max_oi * 100, 2),
                "is_call_wall": strike == call_wall,
                "is_put_wall": strike == put_wall,
                "is_max_pain": strike == max_pain,
            }
        )
    return decorated


def _max_pain(options: list[dict[str, Any]]) -> float:
    if not options:
        return 0
    strikes = [_number(row.get("strike")) for row in options]
    best_strike = strikes[0]
    best_payout = float("inf")
    for settlement in strikes:
        payout = 0.0
        for row in options:
            strike = _number(row.get("strike"))
            payout += _number(row.get("call_oi")) * max(0, settlement - strike)
            payout += _number(row.get("put_oi")) * max(0, strike - settlement)
        if payout < best_payout:
            best_payout = payout
            best_strike = settlement
    return round(best_strike, 2)


def _classify_oi_state(price_change: float, oi_delta: float) -> dict[str, str]:
    if price_change >= 0 and oi_delta >= 0:
        return {
            "direction": "long_build",
            "label": "신규 롱 유입",
            "description": "가격 상승과 OI 증가가 겹쳐 새 상방 포지션 유입으로 봅니다.",
        }
    if price_change >= 0 and oi_delta < 0:
        return {
            "direction": "short_cover",
            "label": "숏커버",
            "description": "가격은 올랐지만 OI가 줄어 기존 숏 청산 성격이 섞여 있습니다.",
        }
    if price_change < 0 and oi_delta >= 0:
        return {
            "direction": "short_build",
            "label": "신규 숏 유입",
            "description": "가격 하락과 OI 증가가 겹쳐 새 하방 포지션 유입으로 봅니다.",
        }
    return {
        "direction": "long_liquidation",
        "label": "롱 청산",
        "description": "가격과 OI가 함께 줄어 기존 롱 포지션 정리 가능성이 큽니다.",
    }


def _headline(regime: str, confidence: str) -> str:
    if regime == "LONG":
        return f"외국인 주도 상방 우위 · 신뢰도 {confidence}"
    if regime == "SHORT":
        return f"하방 압력 우위 · 신뢰도 {confidence}"
    return f"방향성 혼재, 박스 대응 우위 · 신뢰도 {confidence}"


def _flow_text(spot: float, futures: float, option_tilt: float) -> str:
    parts = []
    parts.append("현물 순매수" if spot > 0 else "현물 순매도" if spot < 0 else "현물 중립")
    parts.append("선물 순매수" if futures > 0 else "선물 순매도" if futures < 0 else "선물 중립")
    parts.append("콜 우위" if option_tilt > 0 else "풋 우위" if option_tilt < 0 else "옵션 중립")
    return " / ".join(parts)


def _regime_from_score(score: int) -> str:
    if score >= 62:
        return "LONG"
    if score <= 38:
        return "SHORT"
    return "HOLD"


def _confidence_label(score: int) -> str:
    distance = abs(score - 50)
    if distance >= 24:
        return "HIGH"
    if distance >= 12:
        return "MID"
    return "LOW"


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0
    return round(numerator / denominator, 2)


def _number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except ValueError:
        return 0.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
