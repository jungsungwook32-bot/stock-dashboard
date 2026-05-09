"""미국 주식 데이터 수집 (yfinance)"""

import pandas as pd
import yfinance as yf

from src.config import US_TOP, US_INDEX


def fetch_us_stock(ticker: str, period: str = "1y") -> pd.DataFrame:
    t = yf.Ticker(ticker)
    df = t.history(period=period)
    if df.empty:
        return df
    df.index = df.index.tz_localize(None)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def fetch_us_info(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info
    return {
        "name": info.get("shortName", ""),
        "sector": info.get("sector", ""),
        "market_cap": info.get("marketCap", 0),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "pb_ratio": info.get("priceToBook"),
        "peg_ratio": info.get("pegRatio"),
        "dividend_yield": info.get("dividendYield"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "beta": info.get("beta"),
    }


def fetch_us_market(period: str = "1y") -> dict[str, pd.DataFrame]:
    results = {}
    for name, ticker in US_TOP.items():
        try:
            df = fetch_us_stock(ticker, period)
            if not df.empty:
                results[name] = df
        except Exception as e:
            print(f"  [!] {name}({ticker}) 실패: {e}")
    return results


def fetch_us_index(period: str = "1y") -> dict[str, pd.DataFrame]:
    results = {}
    for name, ticker in US_INDEX.items():
        try:
            df = fetch_us_stock(ticker, period)
            if not df.empty:
                results[name] = df
        except Exception as e:
            print(f"  [!] {name} 실패: {e}")
    return results


def get_us_snapshot() -> pd.DataFrame:
    rows = []
    for name, ticker in US_TOP.items():
        try:
            info = fetch_us_info(ticker)
            info["ticker"] = ticker
            info["display_name"] = name
            rows.append(info)
        except Exception as e:
            print(f"  [!] {name}({ticker}) 실패: {e}")
    return pd.DataFrame(rows)
