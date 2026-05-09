"""한국 주식 데이터 수집 (pykrx)"""

import pandas as pd
from datetime import datetime, timedelta
from pykrx import stock as krx

from src.config import KOREA_TOP, CACHE_DIR


def fetch_korea_stock(code: str, days: int = 365) -> pd.DataFrame:
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    df = krx.get_market_ohlcv(start, end, code)
    if df.empty:
        return df
    df.index.name = "Date"
    df.columns = ["Open", "High", "Low", "Close", "Volume", "Change"]
    return df


def fetch_korea_fundamental(code: str, days: int = 365) -> pd.DataFrame:
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    df = krx.get_market_fundamental(start, end, code)
    if df.empty:
        return df
    df.index.name = "Date"
    return df


def fetch_korea_market(days: int = 365) -> dict[str, pd.DataFrame]:
    results = {}
    for name, code in KOREA_TOP.items():
        try:
            df = fetch_korea_stock(code, days)
            if not df.empty:
                results[name] = df
        except Exception as e:
            print(f"  [!] {name}({code}) 실패: {e}")
    return results


def get_korea_snapshot() -> pd.DataFrame:
    today = datetime.now().strftime("%Y%m%d")
    tries = 0
    df = pd.DataFrame()
    while df.empty and tries < 7:
        check = (datetime.now() - timedelta(days=tries)).strftime("%Y%m%d")
        try:
            df = krx.get_market_ohlcv(check, check, "ALL")
        except Exception:
            pass
        tries += 1

    if df.empty:
        return df

    fund = pd.DataFrame()
    tries = 0
    while fund.empty and tries < 7:
        check = (datetime.now() - timedelta(days=tries)).strftime("%Y%m%d")
        try:
            fund = krx.get_market_fundamental(check, check, "ALL")
        except Exception:
            pass
        tries += 1

    if not fund.empty:
        df = df.join(fund, how="left")

    tracked_codes = set(KOREA_TOP.values())
    df = df[df.index.isin(tracked_codes)]
    code_to_name = {v: k for k, v in KOREA_TOP.items()}
    df["종목명"] = df.index.map(code_to_name)
    return df
