import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

KOREA_TOP = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "삼성바이오로직스": "207940",
    "현대자동차": "005380",
    "기아": "000270",
    "셀트리온": "068270",
    "KB금융": "105560",
    "POSCO홀딩스": "005490",
    "신한지주": "055550",
    "NAVER": "035420",
    "하나금융지주": "086790",
    "삼성SDI": "006400",
    "현대모비스": "012330",
    "LG화학": "051910",
    "카카오": "035720",
    "한화에어로스페이스": "012450",
    "HD현대중공업": "329180",
    "KT&G": "033780",
    "삼성물산": "028260",
}

US_TOP = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "Broadcom": "AVGO",
    "JPMorgan": "JPM",
    "Visa": "V",
    "UnitedHealth": "UNH",
    "Eli Lilly": "LLY",
    "Walmart": "WMT",
    "Mastercard": "MA",
    "Netflix": "NFLX",
    "AMD": "AMD",
    "Costco": "COST",
    "Coca-Cola": "KO",
    "ExxonMobil": "XOM",
    "Lockheed Martin": "LMT",
}

US_INDEX = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX",
    "US 10Y": "^TNX",
}

KOREA_INDEX = {
    "KOSPI": "1001",
    "KOSDAQ": "2001",
}

FRED_SERIES = {
    "기준금리": "FEDFUNDS",
    "CPI": "CPIAUCSL",
    "PCE": "PCEPI",
    "실업률": "UNRATE",
    "GDP성장률": "A191RL1Q225SBEA",
    "10Y국채": "GS10",
    "2Y국채": "GS2",
    "장단기금리차": "T10Y2Y",
    "M2통화량": "M2SL",
    "소비자신뢰지수": "UMCSENT",
    "ISM제조업PMI": "MANEMP",
    "하이일드스프레드": "BAMLH0A0HYM2",
    "달러인덱스": "DTWEXBGS",
    "WTI원유": "DCOILWTICO",
    "금광업PPI": "PCU21222122",
    "구리": "PCOPPUSDM",
}
