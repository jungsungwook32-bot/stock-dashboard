"""거시경제 데이터 수집 (FRED)"""

import pandas as pd
from datetime import datetime, timedelta

from src.config import FRED_API_KEY, FRED_SERIES


def fetch_fred(series_id: str, years: int = 5) -> pd.DataFrame:
    if not FRED_API_KEY:
        print("  [!] FRED_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return pd.DataFrame()

    from fredapi import Fred
    fred = Fred(api_key=FRED_API_KEY)

    start = datetime.now() - timedelta(days=years * 365)
    s = fred.get_series(series_id, observation_start=start)
    df = s.to_frame(name="Value")
    df.index.name = "Date"
    return df


def fetch_all_macro(years: int = 5) -> dict[str, pd.DataFrame]:
    if not FRED_API_KEY:
        print("  [!] FRED_API_KEY 없음 — 거시경제 데이터 스킵")
        return {}

    results = {}
    for name, series_id in FRED_SERIES.items():
        try:
            df = fetch_fred(series_id, years)
            if not df.empty:
                results[name] = df
        except Exception as e:
            print(f"  [!] {name}({series_id}) 실패: {e}")
    return results


def get_macro_summary() -> dict:
    if not FRED_API_KEY:
        return {"error": "FRED_API_KEY not set"}

    from fredapi import Fred
    fred = Fred(api_key=FRED_API_KEY)

    summary = {}
    for name, series_id in FRED_SERIES.items():
        try:
            s = fred.get_series(series_id)
            latest = s.dropna().iloc[-1]
            prev = s.dropna().iloc[-2] if len(s.dropna()) > 1 else None
            summary[name] = {
                "latest": round(float(latest), 4),
                "previous": round(float(prev), 4) if prev is not None else None,
                "date": str(s.dropna().index[-1].date()),
                "change": round(float(latest - prev), 4) if prev is not None else None,
            }
        except Exception as e:
            summary[name] = {"error": str(e)}
    return summary
