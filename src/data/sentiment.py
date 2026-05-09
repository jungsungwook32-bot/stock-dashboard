"""시장 심리 지표 수집"""

import pandas as pd
import requests
import yfinance as yf


def fetch_vix(period: str = "1y") -> pd.DataFrame:
    t = yf.Ticker("^VIX")
    df = t.history(period=period)
    if df.empty:
        return df
    df.index = df.index.tz_localize(None)
    return df[["Close"]].rename(columns={"Close": "VIX"})


def fetch_fear_greed() -> dict:
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            score = data.get("fear_and_greed", {}).get("score")
            rating = data.get("fear_and_greed", {}).get("rating")
            return {"score": score, "rating": rating}
    except Exception:
        pass

    return _estimate_fear_greed_from_vix()


def _estimate_fear_greed_from_vix() -> dict:
    try:
        vix_df = fetch_vix(period="5d")
        if vix_df.empty:
            return {"score": None, "rating": "unavailable", "source": "estimated"}
        vix = vix_df["VIX"].iloc[-1]
        if vix > 35:
            score, rating = max(0, 50 - (vix - 20) * 2.5), "Extreme Fear"
        elif vix > 25:
            score, rating = 50 - (vix - 20) * 3, "Fear"
        elif vix > 18:
            score, rating = 50, "Neutral"
        elif vix > 12:
            score, rating = 50 + (20 - vix) * 3, "Greed"
        else:
            score, rating = min(100, 50 + (20 - vix) * 5), "Extreme Greed"
        return {"score": round(score), "rating": rating, "vix": round(vix, 2), "source": "vix_estimated"}
    except Exception:
        return {"score": None, "rating": "unavailable"}


def get_market_regime() -> dict:
    """현재 매크로 레짐 판단 (VIX + 금리 방향 기반 간이 판단)"""
    try:
        vix_df = fetch_vix(period="3mo")
        if vix_df.empty:
            return {"regime": "unknown"}

        vix_now = vix_df["VIX"].iloc[-1]
        vix_avg = vix_df["VIX"].mean()

        tnx = yf.Ticker("^TNX").history(period="3mo")
        if not tnx.empty:
            tnx.index = tnx.index.tz_localize(None)
            rate_now = tnx["Close"].iloc[-1]
            rate_3m_ago = tnx["Close"].iloc[0]
            rate_trend = "rising" if rate_now > rate_3m_ago else "falling"
        else:
            rate_now = None
            rate_trend = "unknown"

        sp = yf.Ticker("^GSPC").history(period="3mo")
        if not sp.empty:
            sp.index = sp.index.tz_localize(None)
            sp_return = (sp["Close"].iloc[-1] / sp["Close"].iloc[0] - 1) * 100
        else:
            sp_return = 0

        if sp_return > 3 and rate_trend == "falling":
            regime = "골디락스"
            desc = "성장↑ 인플레↓ — 공격적 배분 유리"
        elif sp_return > 0 and rate_trend == "rising":
            regime = "리플레이션"
            desc = "성장↑ 인플레↑ — 원자재/가치주 유리"
        elif sp_return < 0 and rate_trend == "rising":
            regime = "스태그플레이션"
            desc = "성장↓ 인플레↑ — 방어적 배분 필요"
        elif sp_return < -3 and rate_trend == "falling":
            regime = "침체/디플레"
            desc = "성장↓ 인플레↓ — 안전자산 선호"
        else:
            regime = "전환기"
            desc = "방향성 불명확 — 관망"

        return {
            "regime": regime,
            "description": desc,
            "vix": round(vix_now, 2),
            "vix_avg_3m": round(vix_avg, 2),
            "rate_10y": round(rate_now, 2) if rate_now else None,
            "rate_trend": rate_trend,
            "sp500_3m_return": round(sp_return, 2),
        }
    except Exception as e:
        return {"regime": "error", "detail": str(e)}
