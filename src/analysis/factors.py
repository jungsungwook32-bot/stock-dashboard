"""멀티팩터 스코어링 엔진"""

import numpy as np
import pandas as pd

from .technical import add_technical_indicators, get_technical_signal
from .valuation import score_valuation


def _momentum_score(df: pd.DataFrame) -> int:
    if df.empty or len(df) < 120:
        return 0

    latest = df.iloc[-1]
    score = 0

    r60 = latest.get("Return_60d")
    if r60 is not None and not np.isnan(r60):
        if r60 > 0.15:
            score += 25
        elif r60 > 0.05:
            score += 15
        elif r60 > -0.05:
            score += 0
        elif r60 > -0.15:
            score -= 15
        else:
            score -= 25

    r120 = latest.get("Return_120d")
    if r120 is not None and not np.isnan(r120):
        if r120 > 0.2:
            score += 20
        elif r120 > 0.05:
            score += 10
        elif r120 < -0.2:
            score -= 20
        elif r120 < -0.05:
            score -= 10

    # 최근 1개월은 제외 (단기 반전 효과)
    r20 = latest.get("Return_20d")
    if r20 is not None and not np.isnan(r20):
        if r20 > 0.1:
            score -= 5
        elif r20 < -0.1:
            score += 5

    return max(-100, min(100, score))


def _volatility_score(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    latest = df.iloc[-1]
    vol = latest.get("Volatility_20d")
    if vol is None or np.isnan(vol):
        return 0

    if vol < 15:
        return 10
    elif vol < 25:
        return 5
    elif vol < 40:
        return -5
    elif vol < 60:
        return -15
    else:
        return -25


def calculate_multi_factor_score(
    price_df: pd.DataFrame,
    info: dict | None = None,
    sentiment: dict | None = None,
    regime: dict | None = None,
) -> dict:
    price_df = add_technical_indicators(price_df.copy())

    tech = get_technical_signal(price_df)
    tech_score = tech["score"]

    mom_score = _momentum_score(price_df)

    vol_score = _volatility_score(price_df)

    val_score = 0
    val_details = {}
    if info:
        val = score_valuation(info)
        val_score = val["score"]
        val_details = val["details"]

    sent_score = 0
    if sentiment:
        fg = sentiment.get("score")
        if fg is not None:
            if fg < 20:
                sent_score = 30
            elif fg < 35:
                sent_score = 15
            elif fg > 80:
                sent_score = -25
            elif fg > 65:
                sent_score = -10
            else:
                sent_score = 0

    regime_adj = 0
    if regime:
        r = regime.get("regime", "")
        if r == "골디락스":
            regime_adj = 10
        elif r == "리플레이션":
            regime_adj = 0
        elif r == "스태그플레이션":
            regime_adj = -15
        elif r in ("침체/디플레", "침체"):
            regime_adj = -20

    weights = {
        "기술적": 0.20,
        "모멘텀": 0.20,
        "밸류에이션": 0.25,
        "변동성": 0.05,
        "심리": 0.15,
        "레짐": 0.15,
    }

    raw_scores = {
        "기술적": tech_score,
        "모멘텀": mom_score,
        "밸류에이션": val_score,
        "변동성": vol_score,
        "심리": sent_score,
        "레짐": regime_adj,
    }

    final_score = sum(raw_scores[k] * weights[k] for k in weights)
    final_score = max(-100, min(100, final_score))

    if final_score >= 30:
        signal = "강력 매수"
    elif final_score >= 15:
        signal = "매수"
    elif final_score >= -15:
        signal = "관망"
    elif final_score >= -30:
        signal = "매도"
    else:
        signal = "강력 매도"

    return {
        "final_score": round(final_score, 1),
        "signal": signal,
        "factor_scores": raw_scores,
        "weights": weights,
        "technical_details": tech.get("details", {}),
        "valuation_details": val_details,
        "price": round(float(price_df["Close"].iloc[-1]), 2) if not price_df.empty else None,
    }
