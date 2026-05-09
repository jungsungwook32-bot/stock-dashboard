"""글로벌 뉴스 헤드라인 수집 (Google News RSS — 무료, API 키 불필요)"""

import feedparser
import re
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class Headline:
    title: str
    source: str
    published: str
    link: str
    topic: str = ""


TOPIC_QUERIES = {
    "AI_반도체": [
        "NVIDIA AI", "artificial intelligence stocks", "AI chip",
        "반도체 AI", "엔비디아", "GPU shortage",
    ],
    "지정학_전쟁": [
        "Ukraine Russia war", "Israel Hamas", "Taiwan China tension",
        "중동 전쟁", "대만 해협", "우크라이나 러시아", "북한 미사일",
    ],
    "에너지": [
        "oil price", "OPEC production", "natural gas Europe",
        "유가 급등", "원유 감산", "에너지 위기", "LNG",
    ],
    "인물_발언": [
        "Trump tariff", "Elon Musk", "Jensen Huang",
        "트럼프 관세", "일론 머스크", "젠슨 황", "파월 연준",
        "Fed Powell interest rate",
    ],
    "경제_정책": [
        "Federal Reserve rate", "interest rate decision",
        "기준금리 결정", "연준 FOMC", "ECB rate",
        "inflation CPI", "recession GDP",
    ],
    "암호화폐": [
        "Bitcoin price", "crypto crash", "비트코인",
    ],
}

KEYWORD_TO_CHAIN = {
    "tariff": "트럼프관세",
    "관세": "트럼프관세",
    "trade war": "무역전쟁",
    "무역전쟁": "무역전쟁",
    "rate hike": "금리인상",
    "금리 인상": "금리인상",
    "rate cut": "금리인하",
    "금리 인하": "금리인하",
    "oil surge": "원유급등",
    "유가 급등": "원유급등",
    "oil crash": "원유급락",
    "유가 급락": "원유급락",
    "semiconductor boom": "반도체업사이클",
    "반도체 호황": "반도체업사이클",
    "chip shortage": "공급망위기",
    "AI bubble": "AI버블",
    "AI 버블": "AI버블",
    "taiwan": "대만해협긴장",
    "대만": "대만해협긴장",
    "middle east": "중동긴장",
    "중동": "중동긴장",
    "war": "전쟁",
    "전쟁": "전쟁",
    "bank crisis": "은행위기",
    "은행 위기": "은행위기",
    "pandemic": "팬데믹",
    "inflation": "인플레이션급등",
    "인플레": "인플레이션급등",
    "QE": "양적완화",
    "양적완화": "양적완화",
    "QT": "양적긴축",
    "양적긴축": "양적긴축",
    "election": "미국대선",
    "대선": "미국대선",
    "shutdown": "정부셧다운",
    "셧다운": "정부셧다운",
    "real estate crisis": "부동산위기",
    "부동산 위기": "부동산위기",
    "yen": "일본엔저",
    "엔저": "일본엔저",
    "BOJ": "일본금리인상",
    "climate": "기후변화규제",
    "carbon": "기후변화규제",
    "crypto crash": "암호화폐폭락",
    "비트코인 폭락": "암호화폐폭락",
    "supply chain": "공급망위기",
    "공급망": "공급망위기",
    "dollar strong": "달러강세",
    "달러 강세": "달러강세",
    "drought brazil": "브라질가뭄",
    "el nino": "엘니뇨",
    "china slowdown": "중국경기둔화",
    "중국 경기": "중국경기둔화",
    "Elon Musk": "인물발언",
    "일론 머스크": "인물발언",
    "Jensen Huang": "인물발언",
    "젠슨 황": "인물발언",
    "Trump": "트럼프관세",
    "트럼프": "트럼프관세",
    "Powell": "금리인상",
    "파월": "금리인상",
}


def fetch_google_news(query: str, lang: str = "en", max_items: int = 8) -> list[Headline]:
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={lang}&gl={'US' if lang == 'en' else 'KR'}&ceid={'US:en' if lang == 'en' else 'KR:ko'}"
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:max_items]:
            source = ""
            if hasattr(entry, "source") and hasattr(entry.source, "title"):
                source = entry.source.title
            elif " - " in entry.title:
                parts = entry.title.rsplit(" - ", 1)
                if len(parts) == 2:
                    source = parts[1]

            pub_date = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pub_date = getattr(entry, "published", "")

            results.append(Headline(
                title=entry.title,
                source=source,
                published=pub_date,
                link=entry.link,
            ))
        return results
    except Exception:
        return []


def fetch_topic_news(topic: str, max_per_query: int = 5) -> list[Headline]:
    queries = TOPIC_QUERIES.get(topic, [])
    all_headlines = []
    seen_titles = set()

    for q in queries[:4]:
        lang = "ko" if any('가' <= c <= '힣' for c in q) else "en"
        for h in fetch_google_news(q, lang=lang, max_items=max_per_query):
            title_key = re.sub(r'\s+', '', h.title.lower())[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                h.topic = topic
                all_headlines.append(h)

    all_headlines.sort(key=lambda h: h.published, reverse=True)
    return all_headlines[:15]


def detect_chain_events(headlines: list[Headline]) -> list[dict]:
    detected = []
    seen_events = set()

    for h in headlines:
        title_lower = h.title.lower()
        for keyword, event in KEYWORD_TO_CHAIN.items():
            if keyword.lower() in title_lower and event not in seen_events:
                seen_events.add(event)
                detected.append({
                    "event": event,
                    "keyword": keyword,
                    "headline": h.title,
                    "source": h.source,
                    "published": h.published,
                })
    return detected


def fetch_all_topic_news() -> dict[str, list[Headline]]:
    result = {}
    for topic in TOPIC_QUERIES:
        result[topic] = fetch_topic_news(topic)
    return result
