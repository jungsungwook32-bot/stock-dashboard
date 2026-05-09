"""기술적 분석 지표 계산"""

import pandas as pd
import numpy as np


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "MACD": macd_line,
        "Signal": signal_line,
        "Histogram": histogram,
    })


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    return pd.DataFrame({
        "BB_Upper": middle + std_dev * std,
        "BB_Middle": middle,
        "BB_Lower": middle - std_dev * std,
        "BB_Width": (2 * std_dev * std) / middle * 100,
    })


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close_prev = df["Close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - close_prev).abs(),
        (low - close_prev).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Close" not in df.columns:
        return df

    close = df["Close"]

    df["SMA_20"] = sma(close, 20)
    df["SMA_50"] = sma(close, 50)
    df["SMA_200"] = sma(close, 200)
    df["EMA_12"] = ema(close, 12)
    df["EMA_26"] = ema(close, 26)

    df["RSI"] = rsi(close, 14)

    macd_df = macd(close)
    df = pd.concat([df, macd_df], axis=1)

    bb_df = bollinger_bands(close)
    df = pd.concat([df, bb_df], axis=1)

    df["ATR"] = atr(df, 14)

    df["Return_1d"] = close.pct_change()
    df["Return_5d"] = close.pct_change(5)
    df["Return_20d"] = close.pct_change(20)
    df["Return_60d"] = close.pct_change(60)
    df["Return_120d"] = close.pct_change(120)
    df["Return_250d"] = close.pct_change(250)

    df["Volatility_20d"] = df["Return_1d"].rolling(20).std() * np.sqrt(252) * 100

    df["Volume_SMA_20"] = sma(df["Volume"].astype(float), 20)
    df["Volume_Ratio"] = df["Volume"] / df["Volume_SMA_20"]

    df["52W_High"] = close.rolling(252).max()
    df["52W_Low"] = close.rolling(252).min()
    df["Pct_From_52W_High"] = (close / df["52W_High"] - 1) * 100

    return df


def get_technical_signal(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 200:
        return {"signal": "데이터 부족", "score": 0}

    latest = df.iloc[-1]
    signals = {}
    score = 0

    # RSI
    rsi_val = latest.get("RSI")
    if rsi_val is not None and not np.isnan(rsi_val):
        if rsi_val < 30:
            signals["RSI"] = f"과매도 ({rsi_val:.1f})"
            score += 20
        elif rsi_val > 70:
            signals["RSI"] = f"과매수 ({rsi_val:.1f})"
            score -= 20
        else:
            signals["RSI"] = f"중립 ({rsi_val:.1f})"

    # MACD
    macd_val = latest.get("MACD")
    signal_val = latest.get("Signal")
    if macd_val is not None and signal_val is not None:
        if not np.isnan(macd_val) and not np.isnan(signal_val):
            if macd_val > signal_val:
                signals["MACD"] = "매수 신호 (MACD > Signal)"
                score += 15
            else:
                signals["MACD"] = "매도 신호 (MACD < Signal)"
                score -= 15

    # 이동평균
    close = latest["Close"]
    sma50 = latest.get("SMA_50")
    sma200 = latest.get("SMA_200")
    if sma50 is not None and sma200 is not None:
        if not np.isnan(sma50) and not np.isnan(sma200):
            if sma50 > sma200:
                signals["이동평균"] = "골든크로스 (50일 > 200일)"
                score += 15
            else:
                signals["이동평균"] = "데드크로스 (50일 < 200일)"
                score -= 15

    # 볼린저
    bb_upper = latest.get("BB_Upper")
    bb_lower = latest.get("BB_Lower")
    if bb_upper is not None and bb_lower is not None:
        if not np.isnan(bb_upper) and not np.isnan(bb_lower):
            if close > bb_upper:
                signals["볼린저"] = "상단 돌파 (과열)"
                score -= 10
            elif close < bb_lower:
                signals["볼린저"] = "하단 이탈 (과매도)"
                score += 10
            else:
                signals["볼린저"] = "밴드 내"

    # 52주 고점 대비
    pct = latest.get("Pct_From_52W_High")
    if pct is not None and not np.isnan(pct):
        signals["52주고점대비"] = f"{pct:.1f}%"
        if pct < -30:
            score += 10
        elif pct > -5:
            score -= 5

    score = max(-100, min(100, score))
    if score >= 30:
        signal = "매수"
    elif score <= -30:
        signal = "매도"
    else:
        signal = "관망"

    return {"signal": signal, "score": score, "details": signals}
