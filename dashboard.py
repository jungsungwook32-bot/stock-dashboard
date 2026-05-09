#!/usr/bin/env python3
"""투자 알고리즘 대시보드 — Streamlit (초보자용)"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="내 투자 도우미",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 토스 스타일 다크 테마 CSS ───
st.markdown("""
<style>
    /* ── 전체 배경 & 기본 ── */
    .stApp { background-color: #0D0D0D; }
    section[data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid rgba(255,255,255,0.04);
    }
    section[data-testid="stSidebar"] .stRadio label {
        padding: 10px 16px; border-radius: 12px; margin-bottom: 2px;
        transition: background 0.2s;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(49,130,246,0.08);
    }
    section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
        background: rgba(49,130,246,0.15); color: #3182F6;
    }

    /* ── 카드형 메트릭 ── */
    div[data-testid="stMetric"] {
        background: #1A1A1A; border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px; padding: 20px 24px;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #8E8E93; font-weight: 500; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; color: #FFFFFF; }
    div[data-testid="stMetricDelta"] svg { display: none; }
    div[data-testid="stMetricDelta"] > div { font-size: 0.9rem; font-weight: 600; }

    /* ── 카드형 컨테이너 ── */
    div[data-testid="stExpander"] {
        background: #1A1A1A; border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px; overflow: hidden;
    }
    div[data-testid="stExpander"] summary {
        padding: 16px 20px; font-weight: 600; color: #F5F5F5;
    }
    div[data-testid="stExpander"] > div[role="region"] {
        padding: 0 20px 16px;
    }

    /* ── 탭 스타일 ── */
    button[data-baseweb="tab"] {
        font-weight: 600; border-radius: 12px; padding: 8px 20px;
        color: #8E8E93;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #3182F6; background: rgba(49,130,246,0.1);
    }
    div[data-baseweb="tab-highlight"] { background-color: #3182F6; }

    /* ── 버튼 ── */
    .stButton > button {
        background: #3182F6; color: white; border: none;
        border-radius: 12px; padding: 10px 24px; font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover { background: #1B6CF2; transform: translateY(-1px); }
    .stButton > button:active { transform: translateY(0); }

    /* ── 데이터프레임 / 테이블 ── */
    div[data-testid="stDataFrame"] {
        border-radius: 16px; overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* ── 알림 카드 ── */
    div[data-testid="stAlert"] {
        border-radius: 12px; border: none;
        padding: 16px 20px;
    }

    /* ── 셀렉트박스 / 인풋 ── */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background: #1A1A1A; border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
    }

    /* ── 구분선 ── */
    hr { border-color: rgba(255,255,255,0.06); }

    /* ── 스크롤바 ── */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

    /* ── 커스텀 클래스 ── */
    .regime-card {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        padding: 24px; border-radius: 20px; text-align: center;
        font-size: 1.4rem; font-weight: 700; margin-bottom: 16px;
        border: 1px solid rgba(49,130,246,0.15);
    }
    .regime-desc { font-size: 0.9rem; font-weight: 400; color: #B0B0B0; margin-top: 6px; }
    .regime-tip { font-size: 0.8rem; font-weight: 400; margin-top: 8px; opacity: 0.75; }

    .score-strong-buy { color: #34C759; }
    .score-buy { color: #30D158; }
    .score-hold { color: #FFD60A; }
    .score-sell { color: #FF6B6B; }
    .score-strong-sell { color: #FF3B30; }

    .help-text { font-size: 0.82rem; color: #636366; margin-top: -8px; margin-bottom: 14px; }

    /* ── 타이틀 ── */
    h1 { font-weight: 800 !important; letter-spacing: -0.5px; }
    h2, h3 { font-weight: 700 !important; color: #F5F5F5; }

    /* ── 모바일 최적화 ── */
    @media (max-width: 768px) {
        div[data-testid="stMetric"] { padding: 14px 16px; }
        div[data-testid="stMetricValue"] { font-size: 1.3rem; }
        .regime-card { font-size: 1.1rem; padding: 18px; }
        h1 { font-size: 1.5rem !important; }
    }
</style>
""", unsafe_allow_html=True)

CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0D0D0D",
    plot_bgcolor="#0D0D0D",
    font=dict(family="sans-serif", color="#F5F5F5"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
    margin=dict(l=10, r=10, t=40, b=10),
    colorway=["#3182F6", "#34C759", "#FF6B6B", "#FFD60A", "#BF5AF2", "#FF9F0A", "#64D2FF", "#30D158"],
)

CHART_COLORS = {
    "blue": "#3182F6",
    "green": "#34C759",
    "red": "#FF3B30",
    "yellow": "#FFD60A",
    "purple": "#BF5AF2",
    "orange": "#FF9F0A",
    "cyan": "#64D2FF",
}


# ─── 초보자용 용어 변환 ───

REGIME_FRIENDLY = {
    "골디락스": ("안정 성장기", "경제가 잘 성장하면서 물가는 안정 — 투자하기 좋은 시기"),
    "리플레이션": ("물가 상승기", "경제는 성장하지만 물가도 오르는 중 — 원자재/가치주에 유리"),
    "스태그플레이션": ("침체 + 물가 상승", "경제는 안 좋은데 물가는 오름 — 방어적 투자 필요"),
    "침체/디플레": ("경기 침체기", "경제와 물가 모두 하락 — 안전자산(예금, 채권)이 유리"),
    "전환기": ("방향 전환 중", "시장 방향이 바뀌는 중 — 지켜보기"),
}

FACTOR_FRIENDLY = {
    "기술적": "차트 흐름",
    "모멘텀": "상승/하락세",
    "밸류에이션": "가격 적정성",
    "변동성": "위험도",
    "심리": "시장 분위기",
    "레짐": "경제 상황",
}

SIGNAL_FRIENDLY = {
    "강력 매수": "적극 매수 추천",
    "매수": "매수 고려",
    "관망": "지켜보기",
    "매도": "매도 고려",
    "강력 매도": "적극 매도 추천",
}

RATING_FRIENDLY = {
    "Extreme Fear": "극단적 공포 (투자자들이 매우 불안해함)",
    "Fear": "공포 (투자자들이 불안해함)",
    "Neutral": "보통 (특별한 감정 없음)",
    "Greed": "탐욕 (투자자들이 자신감 넘침)",
    "Extreme Greed": "극단적 탐욕 (과열 주의!)",
}

STRATEGY_FRIENDLY = {
    "momentum": "추세 추종 — 오르는 종목을 따라 사기",
    "meanrevert": "평균 회귀 — 많이 빠진 종목 반등 노리기",
    "goldencross": "이동평균 교차 — 장기 추세 전환 포착",
    "bollinger": "가격 밴드 — 비정상적으로 벗어난 가격 포착",
    "breakout": "변동성 돌파 — 급등 초기에 진입",
    "multifactor": "종합 분석 — 여러 전략을 합쳐서 판단",
}


# ─── 캐시된 데이터 로더 ───

@st.cache_data(ttl=300, show_spinner="시장 데이터를 가져오는 중...")
def load_regime():
    from src.data.sentiment import get_market_regime
    return get_market_regime()

@st.cache_data(ttl=300, show_spinner="투자 심리를 확인하는 중...")
def load_fear_greed():
    from src.data.sentiment import fetch_fear_greed
    return fetch_fear_greed()

@st.cache_data(ttl=300, show_spinner="데이터를 가져오는 중...")
def load_vix(period="3mo"):
    from src.data.sentiment import fetch_vix
    return fetch_vix(period=period)

@st.cache_data(ttl=600, show_spinner="경제 지표를 불러오는 중...")
def load_macro():
    from src.data.macro import get_macro_summary
    return get_macro_summary()

@st.cache_data(ttl=300, show_spinner="지수 데이터를 가져오는 중...")
def load_index_data(ticker, period="3mo"):
    import yfinance as yf
    t = yf.Ticker(ticker)
    df = t.history(period=period)
    if not df.empty:
        df.index = df.index.tz_localize(None)
    return df

@st.cache_data(ttl=300, show_spinner="종목 정보를 가져오는 중...")
def load_us_stock(ticker, period="1y"):
    from src.data.us import fetch_us_stock
    return fetch_us_stock(ticker, period=period)

@st.cache_data(ttl=300, show_spinner="종목 정보를 가져오는 중...")
def load_us_info(ticker):
    from src.data.us import fetch_us_info
    return fetch_us_info(ticker)

@st.cache_data(ttl=300, show_spinner="종목 정보를 가져오는 중...")
def load_kr_stock(code, days=365):
    from src.data.korea import fetch_korea_stock
    return fetch_korea_stock(code, days=days)

@st.cache_data(ttl=300, show_spinner="종목을 분석하는 중...")
def compute_factor_score(ticker, is_korea=False, period="1y"):
    from src.analysis.factors import calculate_multi_factor_score
    from src.data.sentiment import fetch_fear_greed, get_market_regime

    if is_korea:
        df = load_kr_stock(ticker, days=365)
        info = None
    else:
        df = load_us_stock(ticker, period=period)
        try:
            info = load_us_info(ticker)
        except Exception:
            info = None

    if df.empty:
        return None

    sentiment = fetch_fear_greed()
    regime = get_market_regime()
    return calculate_multi_factor_score(df, info, sentiment, regime)

@st.cache_data(ttl=600, show_spinner="모든 종목을 분석하는 중... (1~2분 걸려요)")
def scan_stocks(market):
    from src.engine.scanner import scan_us_stocks, scan_korea_stocks
    if market == "US":
        return scan_us_stocks()
    else:
        return scan_korea_stocks()

@st.cache_data(ttl=300, show_spinner="과거 데이터로 시뮬레이션 중...")
def run_cached_backtest(ticker, strategy, is_korea, period_days):
    from src.engine.backtest import run_backtest, STRATEGIES

    if is_korea:
        df = load_kr_stock(ticker, days=period_days)
    else:
        period_map = {365: "1y", 730: "2y", 1095: "3y", 1825: "5y"}
        df = load_us_stock(ticker, period=period_map.get(period_days, "2y"))

    if df.empty or len(df) < 200:
        return None

    capital = 100_000_000 if is_korea else 100_000

    if strategy == "all":
        from src.engine.backtest import STRATEGIES as strats
        results = {}
        for key in strats:
            try:
                r = run_backtest(df, strategy_key=key, initial_capital=capital)
                results[key] = r
            except Exception:
                pass
        return results
    else:
        return run_backtest(df, strategy_key=strategy, initial_capital=capital)


# ─── 동적 해석 생성기 ───

def _interpret_regime(r, regime):
    """레짐에 따른 포트폴리오 조언"""
    tips = {
        "골디락스": "주식 비중을 높여도 좋은 시기예요. 성장주(기술주)가 특히 유리합니다. 다만 너무 낙관하면 고점 매수 위험이 있으니 분할 매수가 안전해요.",
        "리플레이션": "물가가 오르면 원자재(에너지, 금속), 가치주(은행, 보험)가 유리해요. 성장주는 금리 상승 부담으로 주춤할 수 있어요. 한국 수출주는 달러 강세 시 환율 이익을 볼 수 있어요.",
        "스태그플레이션": "가장 어려운 시기예요. 주식과 채권 모두 힘들어요. 현금 비중을 늘리고, 투자한다면 필수소비재(식품, 생활용품)나 배당주 위주로 방어적으로 가세요.",
        "침체/디플레": "주식은 전반적으로 힘들지만, 금리 인하가 예상되면 채권과 성장주가 반등할 수 있어요. 역사적으로 침체기에 싸게 사면 큰 수익을 냈어요. 여유자금이 있다면 분할 매수 기회예요.",
        "전환기": "방향이 바뀌는 중이라 예측이 어려워요. 큰 베팅보다는 소액으로 분산 투자하면서 방향이 확실해질 때까지 기다리세요.",
    }
    return tips.get(r, "")

def _interpret_fg(score):
    """Fear & Greed 점수 해석"""
    if score is None:
        return ""
    if score < 20:
        return "극단적 공포 상태에요. 역사적으로 이럴 때 주식을 사면 장기적으로 큰 수익을 냈어요. 하지만 더 떨어질 수도 있으니 분할 매수가 안전해요."
    elif score < 35:
        return "투자자들이 불안해하는 중이에요. 좋은 종목을 싸게 살 기회일 수 있어요. 단, 공포의 원인(경기 침체, 금융 위기 등)이 해소되는지 확인하세요."
    elif score < 55:
        return "시장이 차분한 상태에요. 특별히 서두를 필요 없이, 평소 계획대로 투자하면 돼요."
    elif score < 75:
        return "투자자들이 자신감이 넘치는 상태예요. 주가가 이미 많이 올랐을 수 있어요. 추격 매수보다는 이미 보유 중인 종목의 수익을 일부 실현하는 것도 고려하세요."
    else:
        return "극단적 탐욕 상태에요. 역사적으로 이 수준 이후 조정(하락)이 자주 왔어요. 신규 매수는 자제하고, 보유 종목 중 많이 오른 것은 일부 매도를 고려하세요."

def _interpret_vix(vix):
    """VIX 해석"""
    if vix is None:
        return ""
    if vix < 12:
        return "시장이 극도로 안정적이에요. 하지만 너무 안일하면 갑자기 급락이 올 수 있어요. 안전자산 비중을 조금 유지하세요."
    elif vix < 20:
        return "정상 범위예요. 큰 걱정 없이 투자할 수 있는 환경이에요. 보유 종목을 유지하면서 좋은 기회를 찾으세요."
    elif vix < 30:
        return "시장이 불안해하기 시작했어요. 급하게 매수하지 말고, 떨어지면 살 종목 목록을 미리 만들어두세요. 손절선을 확인하세요."
    elif vix < 40:
        return "공포 구간이에요. 시장이 크게 흔들리고 있어요. 하지만 역사적으로 VIX 30+ 에서 매수하면 1년 후 대부분 이익이었어요. 용기 있는 분할 매수를 고려하세요."
    else:
        return "극단적 공포예요 (금융위기/팬데믹 수준). 단기적으로 더 빠질 수 있지만, 장기 투자자에게는 최고의 매수 기회가 될 수 있어요. 단, 전 재산을 넣지는 마세요."

def _interpret_rate(rate, trend):
    """10년 금리 해석"""
    if rate is None:
        return ""
    parts = []
    if rate > 5:
        parts.append(f"금리 {rate:.2f}%는 매우 높은 수준이에요. 성장주(기술주)에 부담이 크고, 예금/채권의 매력이 높아져요.")
    elif rate > 4:
        parts.append(f"금리 {rate:.2f}%는 높은 편이에요. 대출 이자 부담이 커서 부동산/고부채 기업에 불리하고, 배당주/가치주가 상대적으로 유리해요.")
    elif rate > 3:
        parts.append(f"금리 {rate:.2f}%는 보통 수준이에요. 주식과 채권 모두 적당한 환경이에요.")
    elif rate > 2:
        parts.append(f"금리 {rate:.2f}%는 낮은 편이에요. 성장주에 유리하고, 예금 이자가 적어서 주식으로 돈이 몰릴 수 있어요.")
    else:
        parts.append(f"금리 {rate:.2f}%는 매우 낮아요. 성장주/부동산에 아주 유리하지만, 경기 침체 신호일 수도 있어요.")

    if trend == "rising":
        parts.append("금리가 오르는 중이라 성장주에는 점점 불리해지고, 은행주는 유리해져요.")
    elif trend == "falling":
        parts.append("금리가 내리는 중이라 성장주/채권에 좋은 신호예요. 연준이 경기를 살리려는 것일 수 있어요.")
    return " ".join(parts)

def _interpret_sp500(ret):
    """S&P 500 3개월 수익률 해석"""
    if ret is None:
        return ""
    if ret > 10:
        return f"3개월간 {ret:+.1f}%는 매우 강한 상승이에요. 시장 전체가 좋지만 과열 위험도 있어요. 추격 매수보다 기존 수익을 지키는 전략이 좋아요."
    elif ret > 5:
        return f"3개월간 {ret:+.1f}%는 건강한 상승이에요. 추세를 따라가되, 너무 늦게 진입하지 않도록 주의하세요."
    elif ret > 0:
        return f"3개월간 {ret:+.1f}%는 소폭 상승이에요. 시장이 방향을 찾는 중이에요. 종목 선별이 중요한 시기예요."
    elif ret > -5:
        return f"3개월간 {ret:+.1f}%로 소폭 조정 중이에요. 좋은 종목을 싸게 살 기회일 수 있어요."
    elif ret > -10:
        return f"3개월간 {ret:+.1f}%는 의미 있는 하락이에요. 원인을 파악하고, 펀더멘털이 좋은 종목 위주로 분할 매수를 고려하세요."
    else:
        return f"3개월간 {ret:+.1f}%는 급락이에요. 공포에 팔기보다는 원인을 분석하세요. 일시적 충격이면 오히려 매수 기회예요. 장기적 위기면 현금 확보가 우선이에요."

def _interpret_macro_value(name, value, change):
    """FRED 지표별 현재값 기반 동적 해석"""
    if value is None:
        return ""
    v = float(value)
    c = float(change) if change else 0

    interp = {
        "기준금리": lambda: (
            f"현재 {v:.2f}%로 {'높은' if v > 4 else '보통' if v > 2.5 else '낮은'} 수준. "
            + ("금리가 올랐어요 → 대출 부담 증가, 성장주 불리, 예금 유리." if c > 0
               else "금리가 내렸어요 → 대출 부담 감소, 성장주 유리, 경기 부양 신호." if c < 0
               else "변동 없음 → 연준이 관망 중.")
        ),
        "CPI": lambda: (
            f"{'상승' if c > 0 else '하락'}했어요. "
            + ("물가가 오르면 연준이 금리를 올릴 수 있어서 주식에 불리해요." if c > 0
               else "물가가 안정되면 연준이 금리를 내릴 수 있어서 주식에 유리해요.")
        ),
        "PCE": lambda: (
            f"연준이 가장 중시하는 물가 지표가 {'올랐' if c > 0 else '내렸'}어요. "
            + ("금리 인상 가능성 ↑ → 성장주 주의." if c > 0
               else "금리 인하 기대 ↑ → 성장주에 호재.")
        ),
        "실업률": lambda: (
            f"현재 {v:.1f}%로 {'낮은(좋은)' if v < 4 else '보통' if v < 5 else '높은(나쁜)'} 수준. "
            + ("실업률 상승 → 경기 둔화 신호. 방어주 유리." if c > 0
               else "실업률 안정/하락 → 경제 건강. 소비/경기 민감주 유리." if c <= 0
               else "")
        ),
        "GDP성장률": lambda: (
            f"현재 {v:.1f}%로 {'강한 성장' if v > 3 else '보통 성장' if v > 1 else '약한 성장' if v > 0 else '경기 위축'}. "
            + ("성장 가속 → 기업 실적 개선 기대, 주식에 유리." if c > 0
               else "성장 둔화 → 실적 악화 우려, 방어적 투자 고려." if c < 0
               else "")
        ),
        "장단기금리차": lambda: (
            f"현재 {v:.2f}%p. "
            + ("마이너스(역전) → 역사적으로 12~18개월 후 경기 침체 가능성이 높아요. 주의 필요!" if v < 0
               else "플러스(정상) → 경제가 정상적으로 작동하고 있다는 신호예요." if v > 0.5
               else "0에 가까움 → 침체 경고와 정상의 경계에요. 주시하세요.")
        ),
        "소비자신뢰지수": lambda: (
            f"현재 {v:.0f}점으로 {'낙관적' if v > 80 else '보통' if v > 60 else '비관적'}. "
            + ("소비 심리 악화 → 소비/유통주에 불리." if c < 0
               else "소비 심리 개선 → 내수/소비주에 호재." if c > 0
               else "")
        ),
        "하이일드스프레드": lambda: (
            f"현재 {v:.2f}%p로 {'안정적' if v < 4 else '주의' if v < 6 else '위험'} 수준. "
            + ("스프레드 확대 → 시장이 위험을 감지. 방어적 투자 필요." if c > 0.1
               else "스프레드 축소 → 시장이 안정을 찾는 중. 위험자산에 긍정적." if c < -0.1
               else "큰 변동 없음.")
        ),
        "WTI원유": lambda: (
            f"배럴당 ${v:.1f}. "
            + ("유가 상승 → 에너지주 수혜, 항공/물류주 부담. 전체 물가 상승 압력." if c > 0
               else "유가 하락 → 소비자/항공주에 유리, 에너지주 부담." if c < 0
               else "")
        ),
        "달러인덱스": lambda: (
            f"{'달러 강세' if c > 0 else '달러 약세'}. "
            + ("달러 강세 → 한국 수출주에 환율 이익, 미국 다국적기업에 불리, 신흥국 부담." if c > 0
               else "달러 약세 → 금/원자재에 유리, 신흥국 투자에 호재." if c < 0
               else "")
        ),
        "구리": lambda: (
            f"구리 가격 {'상승' if c > 0 else '하락'}. "
            + ("구리 상승 = 경기 회복/확장 신호. 산업주/경기민감주에 긍정적." if c > 0
               else "구리 하락 = 경기 둔화 우려. 방어주/안전자산 고려." if c < 0
               else "")
        ),
    }

    fn = interp.get(name)
    return fn() if fn else ""


# ─── 페이지 렌더러 ───

def page_dashboard():
    st.title("📊 시장 현황판")
    st.markdown('<p class="help-text">지금 시장이 어떤 상태인지 한눈에 볼 수 있어요</p>', unsafe_allow_html=True)

    # 레짐
    regime = load_regime()
    r = regime.get("regime", "unknown")
    friendly_name, friendly_tip = REGIME_FRIENDLY.get(r, (r, ""))
    regime_colors = {
        "골디락스": ("#1b5e20", "#e8f5e9"),
        "리플레이션": ("#e65100", "#fff3e0"),
        "스태그플레이션": ("#b71c1c", "#ffebee"),
        "침체/디플레": ("#4a148c", "#f3e5f5"),
        "전환기": ("#37474f", "#eceff1"),
    }
    bg, fg = regime_colors.get(r, ("#37474f", "#eceff1"))
    regime_advice = _interpret_regime(r, regime)
    st.markdown(
        f'<div class="regime-card" style="background:{bg}; color:{fg};">'
        f'지금 시장 분위기: {friendly_name}'
        f'<div class="regime-desc">{friendly_tip}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if regime_advice:
        st.info(f"**내 투자에 미치는 영향:** {regime_advice}")

    # 핵심 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    fg_data = load_fear_greed()
    fg_score = fg_data.get("score")
    fg_rating = fg_data.get("rating", "N/A")
    fg_friendly = RATING_FRIENDLY.get(fg_rating, fg_rating)

    with col1:
        st.metric(
            "투자 심리",
            f"{fg_score}점" if fg_score else "N/A",
            fg_friendly,
        )
    with col2:
        vix = regime.get("vix")
        vix_status = ""
        if vix:
            if vix > 30:
                vix_status = "매우 불안"
            elif vix > 20:
                vix_status = "약간 불안"
            else:
                vix_status = "안정적"
        st.metric("시장 불안 지수", f"{vix:.1f}" if vix else "N/A", vix_status)
    with col3:
        rate = regime.get("rate_10y")
        trend = regime.get("rate_trend", "")
        trend_kr = {"rising": "상승 중", "falling": "하락 중"}.get(trend, trend)
        st.metric("미국 10년 금리", f"{rate:.2f}%" if rate else "N/A", trend_kr)
    with col4:
        sp_ret = regime.get("sp500_3m_return")
        sp_status = ""
        if sp_ret is not None:
            if sp_ret > 5:
                sp_status = "강한 상승"
            elif sp_ret > 0:
                sp_status = "소폭 상승"
            elif sp_ret > -5:
                sp_status = "소폭 하락"
            else:
                sp_status = "강한 하락"
        st.metric("미국 대표지수 (3개월)", f"{sp_ret:+.1f}%" if sp_ret is not None else "N/A", sp_status)

    # 지표별 동적 해석
    with st.expander("**이 숫자들이 내 투자에 어떤 의미인지 보기**", expanded=True):
        ic1, ic2 = st.columns(2)
        with ic1:
            fg_interp = _interpret_fg(fg_score)
            if fg_interp:
                st.markdown(f"**투자 심리 ({fg_score}점):** {fg_interp}")
            vix_interp = _interpret_vix(vix)
            if vix_interp:
                st.markdown(f"**불안 지수 (VIX {vix}):** {vix_interp}")
        with ic2:
            rate_interp = _interpret_rate(rate, trend)
            if rate_interp:
                st.markdown(f"**미국 10년 금리:** {rate_interp}")
            sp_interp = _interpret_sp500(sp_ret)
            if sp_interp:
                st.markdown(f"**S&P 500:** {sp_interp}")

    st.divider()

    # 주요 지수 차트
    st.subheader("주요 증시 흐름")
    st.markdown('<p class="help-text">최근 3개월간 주요 시장이 얼마나 올랐는지/떨어졌는지 보여줘요</p>', unsafe_allow_html=True)

    INDEX_INTERPRET = {
        "미국 S&P 500": lambda c: (
            f"미국 대형주 500개 평균이 {c:+.1f}% {'올랐' if c > 0 else '떨어졌'}어요. "
            + ("전체 시장이 좋으니 미국 주식 보유자에게 유리해요." if c > 3
               else "소폭 상승이지만 종목별 차이가 클 수 있어요." if c > 0
               else "전체적으로 하락 중이에요. 방어적 포지션을 확인하세요." if c > -5
               else "큰 폭의 하락이에요. 원인을 파악하고, 패닉 매도는 피하세요.")
        ),
        "미국 나스닥": lambda c: (
            f"기술주 중심 나스닥이 {c:+.1f}%. "
            + ("기술/AI 섹터가 강해요. NVDA, MSFT 등 보유 중이면 유리해요." if c > 5
               else "기술주가 보합 수준이에요." if c > -2
               else "기술주가 약세예요. 금리 상승이나 규제 이슈를 확인하세요.")
        ),
        "한국 코스피": lambda c: (
            f"한국 대표지수가 {c:+.1f}%. "
            + ("한국 시장이 강해요. 삼성전자, SK하이닉스 등에 긍정적." if c > 5
               else "한국 시장은 보합이에요. 외국인/기관 수급을 확인하세요." if c > -2
               else "한국 시장이 약해요. 환율(원/달러)과 반도체 업황을 확인하세요.")
        ),
    }

    indices = {"미국 S&P 500": "^GSPC", "미국 나스닥": "^IXIC", "한국 코스피": "^KS11"}
    cols = st.columns(len(indices))
    index_interps = []
    for col, (name, ticker) in zip(cols, indices.items()):
        with col:
            df = load_index_data(ticker, "3mo")
            if not df.empty:
                change = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
                color = "green" if change > 0 else "red"
                status = "상승" if change > 0 else "하락"
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index, y=df["Close"], mode="lines",
                    line=dict(color=color, width=2),
                    fill="tozeroy", fillcolor=f"rgba({'0,200,0' if change > 0 else '200,0,0'},0.1)",
                ))
                fig.update_layout(
                    title=f"{name} ({change:+.1f}% {status})",
                    height=220, margin=dict(l=10, r=10, t=40, b=10),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                interp_fn = INDEX_INTERPRET.get(name)
                if interp_fn:
                    index_interps.append(interp_fn(change))
            else:
                st.warning(f"{name} 데이터 없음")

    if index_interps:
        with st.expander("**지수 변동이 내 투자에 미치는 영향**"):
            for interp in index_interps:
                st.markdown(f"- {interp}")

    # VIX 차트
    st.subheader("시장 불안 지수 (VIX)")
    st.markdown('<p class="help-text">숫자가 높을수록 투자자들이 불안해하는 거예요. 20 이하면 안정, 30 이상이면 공포 상태</p>', unsafe_allow_html=True)
    vix_df = load_vix("6mo")
    if not vix_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=vix_df.index, y=vix_df["VIX"], mode="lines",
            line=dict(color="#ff9800", width=2),
        ))
        fig.add_hline(y=20, line_dash="dash", line_color="gray", annotation_text="보통 (20)")
        fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="공포 (30)")
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # FRED 매크로
    st.subheader("경제 지표 요약")
    st.markdown('<p class="help-text">미국 연방준비은행(FRED)에서 가져온 주요 경제 수치들이에요</p>', unsafe_allow_html=True)

    MACRO_EXPLAIN = {
        "기준금리": "중앙은행이 정한 금리. 높으면 대출 비싸고 주식에 불리",
        "CPI": "소비자물가지수. 물가가 얼마나 올랐는지 보여줌",
        "PCE": "개인소비지출 물가. 연준이 가장 중시하는 물가 지표",
        "실업률": "일할 수 있는데 일 못하는 사람 비율",
        "GDP성장률": "경제 성장 속도. 마이너스면 경기 침체",
        "10Y국채": "미국 10년 국채 금리. 시장 금리의 기준",
        "2Y국채": "미국 2년 국채 금리. 연준 정책 기대 반영",
        "장단기금리차": "10년-2년 금리 차이. 마이너스면 침체 경고",
        "M2통화량": "시중에 풀린 돈의 양 (십억 달러)",
        "소비자신뢰지수": "소비자들이 경제를 얼마나 믿는지 (높을수록 낙관)",
        "ISM제조업PMI": "제조업 경기. 50 이상이면 확장, 미만이면 위축",
        "하이일드스프레드": "위험한 채권과 안전한 채권의 금리 차이. 높으면 불안",
        "달러인덱스": "달러 가치. 높으면 달러 강세",
        "WTI원유": "원유 가격 (달러/배럴)",
        "금광업PPI": "금 관련 생산자물가 (금 시세 대용)",
        "구리": "구리 가격. 경기 선행 지표로 불림",
    }

    macro = load_macro()
    if "error" in macro:
        st.error("경제 지표를 가져올 수 없습니다. FRED API 키를 확인해주세요.")
    else:
        rows = []
        interpretations = []
        for name, data in macro.items():
            explain = MACRO_EXPLAIN.get(name, "")
            if "error" in data:
                rows.append({"지표": name, "설명": explain, "현재 값": "오류", "이전 값": "", "변화": "", "발표일": ""})
            else:
                change = data.get("change")
                rows.append({
                    "지표": name,
                    "설명": explain,
                    "현재 값": f"{data['latest']:.4f}",
                    "이전 값": f"{data['previous']:.4f}" if data.get("previous") else "",
                    "변화": f"{change:+.4f}" if change else "",
                    "발표일": data.get("date", ""),
                })
                interp = _interpret_macro_value(name, data["latest"], change)
                if interp:
                    interpretations.append((name, interp))

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        if interpretations:
            with st.expander("**각 경제 지표가 내 투자에 미치는 영향**", expanded=False):
                for iname, interp in interpretations:
                    st.markdown(f"**{iname}:** {interp}")


def page_scanner():
    st.title("🔍 종목 찾기")
    st.markdown('<p class="help-text">여러 기준으로 종목을 분석해서 지금 살 만한 주식을 찾아줘요</p>', unsafe_allow_html=True)

    market = st.radio("어느 나라 주식?", ["미국 주식", "한국 주식"], horizontal=True)
    market_key = "US" if "미국" in market else "KR"

    if st.button("전체 종목 분석하기", type="primary", use_container_width=True):
        results = scan_stocks(market_key)
        st.session_state["scan_results"] = results
        st.session_state["scan_market"] = market_key

    results = st.session_state.get("scan_results", [])
    scan_market = st.session_state.get("scan_market", "")

    if results and scan_market == market_key:
        st.markdown('<p class="help-text">점수가 높을수록 매수 추천, 낮을수록 매도 추천이에요. 초록=사볼만, 빨강=주의, 노랑=지켜보기</p>', unsafe_allow_html=True)

        rows = []
        for i, r in enumerate(results, 1):
            factors = r.get("factor_scores", {})
            signal = SIGNAL_FRIENDLY.get(r["signal"], r["signal"])
            rows.append({
                "순위": i,
                "종목명": r["name"],
                "코드": r["ticker"],
                "현재가": f"${r['price']:,.2f}" if r["market"] == "US" else f"{r['price']:,.0f}원",
                "종합점수": r["final_score"],
                "추천": signal,
                "차트흐름": factors.get("기술적", 0),
                "상승세": factors.get("모멘텀", 0),
                "적정가격": factors.get("밸류에이션", 0),
                "분위기": factors.get("심리", 0),
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df.style.apply(lambda row: [
                f"background-color: {'#1b3a1b' if row['종합점수'] >= 15 else '#3a1b1b' if row['종합점수'] <= -15 else '#3a3a1b'}"
                for _ in row
            ], axis=1),
            use_container_width=True, hide_index=True, height=600,
        )

        # 분포 차트
        fig = go.Figure()
        colors = ["#00e676" if s >= 15 else "#ef5350" if s <= -15 else "#ffa726" for s in df["종합점수"]]
        fig.add_trace(go.Bar(x=df["종목명"], y=df["종합점수"], marker_color=colors))
        fig.add_hline(y=15, line_dash="dash", line_color="green", annotation_text="매수 추천선")
        fig.add_hline(y=-15, line_dash="dash", line_color="red", annotation_text="매도 주의선")
        fig.update_layout(title="종목별 종합 점수", height=350, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # 개별 종목 상세
    st.divider()
    st.subheader("종목 자세히 보기")
    st.markdown('<p class="help-text">특정 종목을 골라서 왜 매수/매도 추천인지 자세히 볼 수 있어요</p>', unsafe_allow_html=True)

    from src.config import US_TOP, KOREA_TOP
    if market_key == "US":
        options = {f"{name} ({ticker})": ticker for name, ticker in US_TOP.items()}
    else:
        options = {f"{name} ({code})": code for name, code in KOREA_TOP.items()}

    selected = st.selectbox("분석할 종목 선택", list(options.keys()))
    if selected:
        ticker = options[selected]
        is_korea = market_key == "KR"

        result = compute_factor_score(ticker, is_korea=is_korea)
        if result is None:
            st.error("이 종목의 데이터를 가져올 수 없어요.")
            return

        score = result["final_score"]
        signal = result["signal"]
        friendly_signal = SIGNAL_FRIENDLY.get(signal, signal)
        if score >= 30:
            score_class = "score-strong-buy"
        elif score >= 15:
            score_class = "score-buy"
        elif score >= -15:
            score_class = "score-hold"
        elif score >= -30:
            score_class = "score-sell"
        else:
            score_class = "score-strong-sell"

        st.markdown(
            f'<h2 class="{score_class}" style="text-align:center;">'
            f'{friendly_signal} (종합 {score:+.1f}점)</h2>',
            unsafe_allow_html=True,
        )

        # 팩터 레이더 차트
        factors = result["factor_scores"]
        weights = result["weights"]
        labels_raw = list(factors.keys())
        labels = [FACTOR_FRIENDLY.get(k, k) for k in labels_raw]
        values = [factors[k] for k in labels_raw]
        contribs = [factors[k] * weights[k] for k in labels_raw]

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=[max(0, v) for v in values],
                theta=labels, fill="toself", name="긍정 요소",
                fillcolor="rgba(0,230,118,0.2)", line_color="#00e676",
            ))
            fig.add_trace(go.Scatterpolar(
                r=[abs(min(0, v)) for v in values],
                theta=labels, fill="toself", name="부정 요소",
                fillcolor="rgba(239,83,80,0.2)", line_color="#ef5350",
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 50])),
                title="분석 항목별 점수", height=350, showlegend=True,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            colors = ["#00e676" if c > 0 else "#ef5350" for c in contribs]
            fig.add_trace(go.Bar(x=labels, y=contribs, marker_color=colors))
            fig.update_layout(title="최종 점수에 얼마나 영향을 줬나", height=350, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        # 기술적/밸류에이션 상세
        c1, c2 = st.columns(2)
        with c1:
            if result.get("technical_details"):
                st.markdown("**차트 분석 상세**")
                st.markdown('<p class="help-text">주가 흐름에서 읽을 수 있는 신호들이에요</p>', unsafe_allow_html=True)
                tech_rows = [{"지표": k, "현재 상태": str(v)} for k, v in result["technical_details"].items()]
                st.dataframe(pd.DataFrame(tech_rows), use_container_width=True, hide_index=True)
        with c2:
            if result.get("valuation_details"):
                st.markdown("**이 가격이 적정한가?**")
                st.markdown('<p class="help-text">현재 주가가 비싼지 싼지 여러 기준으로 판단해요</p>', unsafe_allow_html=True)
                val_rows = [{"항목": k, "판단": str(v)} for k, v in result["valuation_details"].items()]
                st.dataframe(pd.DataFrame(val_rows), use_container_width=True, hide_index=True)

        # 가격 차트
        st.markdown("**최근 1년 주가 흐름**")
        if is_korea:
            price_df = load_kr_stock(ticker, 365)
        else:
            price_df = load_us_stock(ticker, "1y")

        if not price_df.empty:
            from src.analysis.technical import sma
            price_df["SMA20"] = sma(price_df["Close"], 20)
            price_df["SMA60"] = sma(price_df["Close"], 60)

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(
                x=price_df.index, open=price_df["Open"], high=price_df["High"],
                low=price_df["Low"], close=price_df["Close"], name="주가",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=price_df.index, y=price_df["SMA20"], name="20일 평균선",
                                     line=dict(color="#42a5f5", width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=price_df.index, y=price_df["SMA60"], name="60일 평균선",
                                     line=dict(color="#ffa726", width=1)), row=1, col=1)
            fig.add_trace(go.Bar(x=price_df.index, y=price_df["Volume"], name="거래량",
                                 marker_color="rgba(100,100,100,0.5)"), row=2, col=1)
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, showlegend=True,
                              margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)


def page_chain():
    st.title("🔗 무슨 일이 생기면?")
    st.markdown('<p class="help-text">세상에 큰 사건이 터지면 어떤 주식이 오르고 내리는지 추적해요</p>', unsafe_allow_html=True)

    from src.engine.chain import CAUSAL_GRAPH, trace_chain, search_by_ticker, get_actionable, ALL_EVENTS

    EVENT_FRIENDLY = {
        "금리인상": "🏦 금리 인상 (중앙은행이 금리를 올림)",
        "금리인하": "🏦 금리 인하 (중앙은행이 금리를 내림)",
        "양적완화": "💰 양적완화 (중앙은행이 돈을 풀음)",
        "양적긴축": "💰 양적긴축 (중앙은행이 돈을 거둠)",
        "인플레이션급등": "📈 인플레이션 급등 (물가가 크게 오름)",
        "원유급등": "🛢️ 유가 급등 (기름값이 크게 오름)",
        "원유급락": "🛢️ 유가 급락 (기름값이 크게 내림)",
        "반도체업사이클": "💻 반도체 호황 (반도체 수요 폭증)",
        "반도체다운사이클": "💻 반도체 불황 (반도체 수요 감소)",
        "AI버블": "🤖 AI 버블 (AI 주식 과열 후 조정)",
        "무역전쟁": "🚢 무역전쟁 (국가 간 관세 전쟁)",
        "트럼프관세": "🇺🇸 트럼프 관세 (미국 고율 관세 부과)",
        "대만해협긴장": "⚔️ 대만 해협 긴장 (군사 긴장 고조)",
        "중동긴장": "⚔️ 중동 긴장 (중동 지역 분쟁)",
        "전쟁": "⚔️ 전쟁/지정학 충격",
        "팬데믹": "🦠 전염병 대유행 (코로나 같은 상황)",
        "중국경기둔화": "🇨🇳 중국 경기 둔화 (중국 경제 침체)",
        "달러강세": "💵 달러 강세 (달러 가치 상승)",
        "일본엔저": "🇯🇵 일본 엔저 (엔화 가치 하락)",
        "일본금리인상": "🇯🇵 일본 금리 인상 (엔캐리 청산 위험)",
        "은행위기": "🏦 은행 위기 (금융 시스템 불안)",
        "부동산위기": "🏠 부동산 위기 (집값 폭락)",
        "공급망위기": "📦 공급망 위기 (물류/생산 마비)",
        "기후변화규제": "🌍 기후변화 규제 (탄소규제 강화)",
        "브라질가뭄": "🌾 브라질 가뭄 (커피/대두 생산 타격)",
        "엘니뇨": "🌊 엘니뇨 (이상기후 발생)",
        "미국대선": "🗳️ 미국 대선 (정치 불확실성)",
        "정부셧다운": "🏛️ 미국 정부 셧다운 (연방정부 폐쇄)",
        "암호화폐폭락": "₿ 암호화폐 폭락 (가상자산 급락)",
    }

    DEPTH_FRIENDLY = {
        1: "바로 영향 받는 것",
        2: "간접적으로 퍼지는 영향",
        3: "더 멀리 퍼지는 영향",
        4: "아주 약한 연결",
    }

    CONF_FRIENDLY = {
        "A": "거의 확실",
        "B": "가능성 높음",
        "C": "가능성 있음",
        "D": "약한 가능성",
    }

    EVENT_CATEGORIES = {
        "💰 금리/통화 정책": ["금리인상", "금리인하", "양적완화", "양적긴축"],
        "📈 물가/인플레": ["인플레이션급등", "원유급등", "원유급락"],
        "💻 산업/기술": ["반도체업사이클", "반도체다운사이클", "AI버블", "공급망위기"],
        "⚔️ 지정학/전쟁": ["대만해협긴장", "중동긴장", "전쟁", "무역전쟁", "트럼프관세"],
        "🌍 글로벌 경제": ["중국경기둔화", "달러강세", "일본엔저", "일본금리인상"],
        "🏦 금융 위기": ["은행위기", "부동산위기", "암호화폐폭락"],
        "🌊 기후/자연재해": ["브라질가뭄", "엘니뇨", "기후변화규제"],
        "🏛️ 정치/정책": ["미국대선", "정부셧다운"],
        "🦠 기타": ["팬데믹"],
    }

    tab1, tab2 = st.tabs(["사건 → 어디에 영향?", "내 종목은 어떤 사건에 약한가?"])

    with tab1:
        cat_col, event_col = st.columns([1, 2])
        with cat_col:
            category = st.selectbox("분야 선택", list(EVENT_CATEGORIES.keys()))
        events_in_cat = EVENT_CATEGORIES[category]
        cat_event_options = {EVENT_FRIENDLY.get(e, e): e for e in events_in_cat if e in CAUSAL_GRAPH}
        with event_col:
            selected_label = st.selectbox("어떤 사건이 일어났나요?", list(cat_event_options.keys()))
        event_options = cat_event_options
        event = event_options[selected_label]

        if event:
            chains = trace_chain(event)
            if chains:
                for chain in chains:
                    depth_label = DEPTH_FRIENDLY.get(chain.depth, f"{chain.depth}차")
                    with st.expander(f"**{depth_label}** ({len(chain.impacts)}개)", expanded=(chain.depth <= 2)):
                        for impact in chain.impacts:
                            dir_icon = "📈" if impact.direction == "+" else "📉"
                            dir_text = "오를 수 있음" if impact.direction == "+" else "내릴 수 있음"
                            conf_text = CONF_FRIENDLY.get(impact.confidence, impact.confidence)
                            tickers = f"  `{', '.join(impact.tickers)}`" if impact.tickers else ""
                            st.markdown(f"{dir_icon} **{impact.target}** — {impact.reason} ({conf_text}){tickers}")

                actions = get_actionable(chains)

                col1, col2 = st.columns(2)
                with col1:
                    if actions["long"]:
                        st.markdown("### 📈 사볼 만한 것")
                        for item in actions["long"]:
                            conf_text = CONF_FRIENDLY.get(item["confidence"], item["confidence"])
                            st.success(f"**{item['target']}** [{', '.join(item['tickers'])}]\n\n{item['reason']} ({conf_text})")
                with col2:
                    if actions["short"]:
                        st.markdown("### 📉 팔거나 피할 것")
                        for item in actions["short"]:
                            conf_text = CONF_FRIENDLY.get(item["confidence"], item["confidence"])
                            st.error(f"**{item['target']}** [{', '.join(item['tickers'])}]\n\n{item['reason']} ({conf_text})")

                if actions["watch"]:
                    st.markdown("### 👀 지켜볼 것")
                    for item in actions["watch"]:
                        st.info(f"{item['target']} [{', '.join(item['tickers'])}] — {item['reason']}")

    with tab2:
        st.markdown('<p class="help-text">종목을 선택하면 어떤 사건이 이 종목에 영향을 주는지 알려줘요</p>', unsafe_allow_html=True)

        search_method = st.radio(
            "종목 선택 방법",
            ["주요 종목에서 고르기", "내 모의 포트폴리오 종목", "직접 입력"],
            horizontal=True,
        )

        from src.config import US_TOP, KOREA_TOP
        ticker_input = ""
        if search_method == "주요 종목에서 고르기":
            market_tab = st.radio("시장", ["미국 주요 종목", "한국 주요 종목"], horizontal=True)
            if market_tab == "미국 주요 종목":
                stock_options = {f"{name} ({ticker})": ticker for name, ticker in US_TOP.items()}
            else:
                stock_options = {f"{name} ({code})": code for name, code in KOREA_TOP.items()}
            selected_stock = st.selectbox("종목 선택", list(stock_options.keys()))
            ticker_input = stock_options[selected_stock]
        elif search_method == "내 모의 포트폴리오 종목":
            from src.engine.paper import PaperPortfolio
            port = PaperPortfolio.load()
            if port.positions:
                pos_options = {f"{p.name} ({p.ticker})": p.ticker for p in port.positions}
                selected_pos = st.selectbox("보유 종목 선택", list(pos_options.keys()))
                ticker_input = pos_options[selected_pos]
            else:
                st.info("보유 중인 모의 투자 종목이 없어요. '모의 투자' 페이지에서 먼저 종목을 매수해보세요!")
        else:
            ticker_input = st.text_input("종목 코드 입력 (예: NVDA, 005930)", "").strip().upper()

        if ticker_input:
            results = search_by_ticker(ticker_input)
            if results:
                good = [r for r in results if r["direction"] == "+"]
                bad = [r for r in results if r["direction"] == "-"]
                col_g, col_b = st.columns(2)
                with col_g:
                    st.metric("좋은 영향 시나리오", f"{len(good)}개")
                with col_b:
                    st.metric("나쁜 영향 시나리오", f"{len(bad)}개")

                rows = [{
                    "사건": EVENT_FRIENDLY.get(r["event"], r["event"]),
                    "영향 단계": DEPTH_FRIENDLY.get(r["depth"], f"{r['depth']}차"),
                    "영향 대상": r["target"],
                    "방향": "📈 좋은 영향" if r["direction"] == "+" else "📉 나쁜 영향",
                    "신뢰도": CONF_FRIENDLY.get(r["confidence"], r["confidence"]),
                    "이유": r["reason"],
                } for r in results]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.caption(f"총 {len(results)}개 시나리오에서 이 종목이 영향을 받아요")

                with st.expander("이 종목이 가장 주의해야 할 사건은?"):
                    high_risk = [r for r in results if r["direction"] == "-" and r["confidence"] in ("A", "B") and r["depth"] <= 2]
                    if high_risk:
                        for r in high_risk:
                            st.error(f"**{EVENT_FRIENDLY.get(r['event'], r['event'])}** → {r['reason']} ({CONF_FRIENDLY.get(r['confidence'], r['confidence'])})")
                    else:
                        st.success("등록된 주요 위험 사건이 없어요. 비교적 안전한 종목이에요!")
            else:
                st.warning(f"'{ticker_input}'는 등록된 사건 목록에 없어요. 주요 대형주 위주로 등록되어 있어요.")


def page_backtest():
    st.title("📈 과거로 돌아가서 테스트")
    st.markdown('<p class="help-text">"만약 이 전략대로 과거에 투자했다면?" 을 시뮬레이션해요. 실제 돈이 들지 않아요!</p>', unsafe_allow_html=True)

    from src.engine.backtest import STRATEGIES

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.text_input("종목 코드", "AAPL", help="미국: AAPL, NVDA 등 / 한국: 005930 (삼성전자) 등").strip().upper()
    with col2:
        is_korea = st.checkbox("한국 종목인가요?", value=ticker.isdigit() and len(ticker) == 6)
    with col3:
        strategy = st.selectbox(
            "투자 전략",
            ["all"] + list(STRATEGIES.keys()),
            format_func=lambda x: "모든 전략 비교하기" if x == "all" else STRATEGY_FRIENDLY.get(x, x),
            help="어떤 방식으로 사고팔지 정하는 규칙이에요",
        )
    with col4:
        period_label = st.selectbox("얼마나 과거까지?", ["1년", "2년", "3년", "5년"])
        period_days = {"1년": 365, "2년": 730, "3년": 1095, "5년": 1825}[period_label]

    if st.button("시뮬레이션 시작", type="primary", use_container_width=True):
        result = run_cached_backtest(ticker, strategy, is_korea, period_days)
        if result is None:
            st.error("데이터가 부족해요 (최소 200거래일 필요). 기간을 늘려보세요.")
            return

        st.session_state["bt_result"] = result
        st.session_state["bt_strategy"] = strategy
        st.session_state["bt_ticker"] = ticker

    result = st.session_state.get("bt_result")
    bt_strategy = st.session_state.get("bt_strategy")
    bt_ticker = st.session_state.get("bt_ticker")

    if result is None:
        return

    if bt_strategy == "all" and isinstance(result, dict):
        _render_backtest_comparison(result, bt_ticker)
    elif hasattr(result, "name"):
        _render_backtest_single(result, bt_ticker)


def _render_backtest_single(r, ticker):
    is_kr = ticker.isdigit() and len(ticker) == 6
    curr = "원" if is_kr else "$"

    vs_bench = r.total_return - r.benchmark_return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "총 수익률",
            f"{r.total_return:+.2f}%",
            "이익" if r.total_return > 0 else "손실",
            help="이 전략으로 투자했다면 총 얼마를 벌었을지",
        )
    with col2:
        st.metric(
            "1년 기준 수익률",
            f"{r.annual_return:+.2f}%",
            help="1년으로 환산하면 연 몇 %인지",
        )
    with col3:
        st.metric(
            "그냥 사서 들고 있었다면?",
            f"{vs_bench:+.2f}%",
            "전략이 더 좋았음" if vs_bench > 0 else "그냥 들고 있는 게 나았음",
            help="아무것도 안 하고 그냥 보유했을 때와 비교",
        )
    with col4:
        sharpe_label = "좋음" if r.sharpe_ratio > 1 else ("보통" if r.sharpe_ratio > 0.5 else "나쁨")
        st.metric(
            "위험 대비 수익",
            f"{r.sharpe_ratio:.2f}",
            sharpe_label,
            help="위험을 감수한 만큼 수익을 잘 냈는지 (1 이상이면 양호)",
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        mdd_label = "양호" if r.max_drawdown > -15 else ("주의" if r.max_drawdown > -25 else "위험")
        st.metric(
            "최대로 떨어진 폭",
            f"{r.max_drawdown:.1f}%",
            mdd_label,
            help="투자 중 가장 많이 손해 본 순간. -20% 이상이면 위험",
        )
    with col2:
        st.metric("총 거래 횟수", f"{r.total_trades}번", help="사고판 횟수")
    with col3:
        st.metric(
            "이긴 비율",
            f"{r.win_rate:.1f}%",
            "좋음" if r.win_rate > 50 else "개선 필요",
            help="거래 중 이익을 본 비율. 50% 이상이면 양호",
        )
    with col4:
        pf_label = "좋음" if r.profit_factor > 1.5 else ("보통" if r.profit_factor > 1 else "나쁨")
        st.metric(
            "이익/손실 비율",
            f"{r.profit_factor:.2f}",
            pf_label,
            help="번 돈 / 잃은 돈. 1보다 크면 총합 이익, 1.5 이상이면 양호",
        )

    # 수익 곡선
    if not r.equity_curve.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=r.equity_curve.index, y=r.equity_curve.values,
            name=f"{r.name}", line=dict(color="#42a5f5", width=2),
        ))
        baseline = r.equity_curve.iloc[0]
        fig.add_hline(y=baseline, line_dash="dash", line_color="gray", annotation_text="처음 투자한 금액")
        fig.update_layout(title="내 돈이 어떻게 변했을까?", height=400, margin=dict(l=10, r=10, t=40, b=10),
                          yaxis_title=f"총 자산 ({curr})")
        st.plotly_chart(fig, use_container_width=True)

    # 거래 내역
    if r.trades:
        st.subheader("사고판 기록")
        st.markdown('<p class="help-text">언제 사서 언제 팔았는지, 각 거래의 결과예요</p>', unsafe_allow_html=True)
        rows = []
        for t in r.trades:
            rows.append({
                "산 날짜": t.entry_date,
                "판 날짜": t.exit_date,
                "산 가격": f"{t.entry_price:,.0f}" if is_kr else f"${t.entry_price:,.2f}",
                "판 가격": f"{t.exit_price:,.0f}" if is_kr else f"${t.exit_price:,.2f}",
                "수익률": f"{t.pnl_pct:+.2f}%",
                "결과": "이익" if t.is_win else "손실",
                "판 이유": t.reason_exit,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_backtest_comparison(results_dict, ticker):
    st.markdown('<p class="help-text">6가지 전략을 비교해요. 어떤 방법이 가장 돈을 잘 벌었는지 확인하세요</p>', unsafe_allow_html=True)

    rows = []
    equity_traces = []

    sorted_results = sorted(results_dict.items(), key=lambda x: x[1].total_return, reverse=True)

    for i, (key, r) in enumerate(sorted_results, 1):
        rows.append({
            "순위": i,
            "전략": STRATEGY_FRIENDLY.get(key, r.name),
            "총수익률": f"{r.total_return:+.2f}%",
            "1년 기준": f"{r.annual_return:+.2f}%",
            "위험대비수익": f"{r.sharpe_ratio:.2f}",
            "최대 손실": f"{r.max_drawdown:.1f}%",
            "거래 횟수": r.total_trades,
            "이긴 비율": f"{r.win_rate:.0f}%",
            "이익/손실": f"{r.profit_factor:.2f}",
        })
        if not r.equity_curve.empty:
            normalized = r.equity_curve / r.equity_curve.iloc[0] * 100
            equity_traces.append((STRATEGY_FRIENDLY.get(key, r.name).split(" — ")[0], normalized))

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if equity_traces:
        fig = go.Figure()
        colors = ["#42a5f5", "#66bb6a", "#ffa726", "#ef5350", "#ab47bc", "#26c6da"]
        for i, (name, eq) in enumerate(equity_traces):
            fig.add_trace(go.Scatter(
                x=eq.index, y=eq.values, name=name,
                line=dict(color=colors[i % len(colors)], width=2),
            ))
        fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="처음 금액 (100)")
        fig.update_layout(
            title="각 전략으로 투자했다면? (100에서 시작)",
            height=450,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis_title="내 돈 변화 (시작=100)",
        )
        st.plotly_chart(fig, use_container_width=True)


def page_paper():
    st.title("💰 내 모의 포트폴리오")
    st.markdown('<p class="help-text">가짜 돈으로 연습해요. 실제 돈은 전혀 들지 않아요!</p>', unsafe_allow_html=True)

    from src.engine.paper import PaperPortfolio, auto_trade

    port = PaperPortfolio.load()
    summary = port.get_portfolio_summary()

    # 계좌 요약
    col1, col2 = st.columns(2)
    with col1:
        us_color = "green" if summary["us_return"] >= 0 else "red"
        st.metric("미국 계좌 총 자산", f"${summary['total_value_us']:,.0f}",
                  f"{summary['us_return']:+.2f}%", help="미국 주식 계좌의 총 가치")
        st.caption(f"남은 현금: ${summary['cash_us']:,.0f}")
    with col2:
        kr_color = "green" if summary["kr_return"] >= 0 else "red"
        st.metric("한국 계좌 총 자산", f"{summary['total_value_kr']:,.0f}원",
                  f"{summary['kr_return']:+.2f}%", help="한국 주식 계좌의 총 가치")
        st.caption(f"남은 현금: {summary['cash_kr']:,.0f}원")

    st.divider()

    # 보유 종목
    st.subheader("보유 종목")
    if summary["holdings"]:
        rows = []
        for h in summary["holdings"]:
            curr = "$" if h["market"] == "US" else "원"
            if h["market"] == "US":
                ep = f"${h['entry_price']:,.2f}"
                cp = f"${h['current_price']:,.2f}"
                pnl = f"${h['pnl_amount']:,.2f}"
            else:
                ep = f"{h['entry_price']:,.0f}원"
                cp = f"{h['current_price']:,.0f}원"
                pnl = f"{h['pnl_amount']:,.0f}원"
            rows.append({
                "종목": h["name"],
                "코드": h["ticker"],
                "수량": h["shares"],
                "산 가격": ep,
                "현재 가격": cp,
                "수익률": f"{h['pnl_pct']:+.2f}%",
                "손익 금액": pnl,
                "산 날짜": h["entry_date"],
            })
        df_holdings = pd.DataFrame(rows)
        st.dataframe(
            df_holdings.style.apply(lambda row: [
                f"background-color: {'#1b3a1b' if '+' in str(row['수익률']) and row['수익률'] != '+0.00%' else '#3a1b1b' if '-' in str(row['수익률']) else ''}"
                for _ in row
            ], axis=1),
            use_container_width=True, hide_index=True,
        )

        # 보유 종목 수익률 차트
        if len(rows) > 0:
            fig = go.Figure()
            names = [r["종목"] for r in rows]
            pnls = [float(r["수익률"].replace("%", "").replace("+", "")) for r in rows]
            colors = ["#00e676" if p > 0 else "#ef5350" if p < 0 else "#ffa726" for p in pnls]
            fig.add_trace(go.Bar(x=names, y=pnls, marker_color=colors))
            fig.add_hline(y=0, line_color="gray")
            fig.update_layout(title="보유 종목별 수익률", height=300, margin=dict(l=10, r=10, t=40, b=10),
                              yaxis_title="수익률 (%)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("아직 보유 종목이 없어요. 아래에서 매수하거나 자동 매매를 해보세요!")

    st.divider()

    # 종목 추천
    st.subheader("🎯 지금 뭘 사면 좋을까?")
    st.markdown('<p class="help-text">AI가 분석한 점수가 높은 종목을 보여줘요. 점수가 높을수록 매수 추천!</p>', unsafe_allow_html=True)

    rec_market = st.radio("시장", ["미국 추천 종목", "한국 추천 종목"], horizontal=True, key="rec_market")

    if st.button("추천 종목 분석하기", use_container_width=True, key="rec_scan"):
        with st.spinner("종목 분석 중... (30초~1분 소요)"):
            from src.engine.scanner import scan_us_stocks, scan_korea_stocks
            if "미국" in rec_market:
                scan_results = scan_us_stocks()
            else:
                scan_results = scan_korea_stocks()

        if scan_results:
            st.session_state["rec_results"] = scan_results

    if "rec_results" in st.session_state and st.session_state["rec_results"]:
        scan_results = st.session_state["rec_results"]
        buy_candidates = [r for r in scan_results if r.get("signal") in ("강력 매수", "매수")]
        hold_list = [r for r in scan_results if r.get("signal") == "관망"]
        sell_list = [r for r in scan_results if r.get("signal") in ("매도", "강력 매도")]

        if buy_candidates:
            st.markdown("#### 📈 매수 추천")
            for r in buy_candidates[:5]:
                score = r.get("final_score", 0)
                signal = SIGNAL_FRIENDLY.get(r.get("signal", ""), r.get("signal", ""))
                ticker = r.get("ticker", "")
                name = r.get("name", ticker)
                price = r.get("price", 0)
                is_kr = r.get("market") == "KR" or (isinstance(ticker, str) and ticker.isdigit())
                price_str = f"{price:,.0f}원" if is_kr else f"${price:,.2f}"
                market = "KR" if is_kr else "US"

                with st.container():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{name}** ({ticker})")
                        st.caption(f"{signal} · 점수 {score:+.1f} · 현재가 {price_str}")
                    with c2:
                        buy_shares = st.number_input("수량", min_value=1, value=5, key=f"rec_qty_{ticker}")
                    with c3:
                        st.markdown("")
                        if st.button("매수", key=f"rec_buy_{ticker}", type="primary", use_container_width=True):
                            msg = port.buy(ticker, name, market, buy_shares, price,
                                           reason=f"추천 매수 ({signal})", signal_score=score)
                            st.success(msg)
                            st.rerun()

        if hold_list:
            with st.expander(f"관망 ({len(hold_list)}종목)"):
                for r in hold_list:
                    st.caption(f"{r.get('name', '')} ({r.get('ticker', '')}) — 점수 {r.get('final_score', 0):+.1f}")

        if sell_list:
            st.markdown("#### 📉 매도 추천")
            for r in sell_list:
                pos = port.get_position(r.get("ticker", ""))
                if pos:
                    st.warning(f"**{r.get('name', '')}** ({r.get('ticker', '')}) — 보유 중인데 매도 시그널이에요!")

    st.divider()

    # 매수/매도
    st.subheader("직접 사고팔기")
    st.markdown('<p class="help-text">원하는 종목을 자유롭게 매수/매도할 수 있어요</p>', unsafe_allow_html=True)

    trade_method = st.radio(
        "종목 선택",
        ["주요 종목에서 고르기", "보유 종목 매도", "직접 검색"],
        horizontal=True, key="trade_method",
    )

    from src.config import US_TOP, KOREA_TOP

    trade_ticker = ""
    trade_name = ""
    trade_market = "US"

    if trade_method == "주요 종목에서 고르기":
        market_choice = st.radio("시장", ["미국", "한국"], horizontal=True, key="trade_market_choice")
        if market_choice == "미국":
            stock_map = {f"{name} ({ticker})": (ticker, name) for name, ticker in US_TOP.items()}
        else:
            stock_map = {f"{name} ({code})": (code, name) for name, code in KOREA_TOP.items()}
        selected = st.selectbox("종목 선택", list(stock_map.keys()), key="trade_select")
        trade_ticker, trade_name = stock_map[selected]
        trade_market = "KR" if market_choice == "한국" else "US"

    elif trade_method == "보유 종목 매도":
        if port.positions:
            pos_map = {f"{p.name} ({p.ticker})": p for p in port.positions}
            selected_pos = st.selectbox("매도할 종목", list(pos_map.keys()), key="sell_select")
            pos = pos_map[selected_pos]
            trade_ticker = pos.ticker
            trade_name = pos.name
            trade_market = pos.market
            st.caption(f"보유: {pos.shares}주 · 평균 단가: {'$' if pos.market == 'US' else ''}{pos.entry_price:,.2f}{'원' if pos.market == 'KR' else ''}")
        else:
            st.info("보유 종목이 없어요.")

    else:
        trade_ticker = st.text_input("종목 코드 입력", "", placeholder="AAPL, TSLA, 005930 등",
                                     key="paper_ticker").strip().upper()
        if trade_ticker:
            is_korea = trade_ticker.isdigit() and len(trade_ticker) == 6
            trade_market = "KR" if is_korea else "US"
            if is_korea:
                trade_name = {v: k for k, v in KOREA_TOP.items()}.get(trade_ticker, trade_ticker)
            else:
                trade_name = {v: k for k, v in US_TOP.items()}.get(trade_ticker, trade_ticker)

    if trade_ticker:
        col_qty, col_action, col_exec = st.columns([1, 1, 1])
        with col_qty:
            trade_shares = st.number_input("수량", min_value=1, value=10, key="paper_shares")
        with col_action:
            if trade_method == "보유 종목 매도":
                trade_action = "매도 (팔기)"
                st.markdown(f"**매도**")
            else:
                trade_action = st.radio("매매", ["매수 (사기)", "매도 (팔기)"], horizontal=True, key="paper_action")
        with col_exec:
            st.markdown("")
            if st.button("실행", type="primary", key="paper_exec", use_container_width=True):
                try:
                    if trade_market == "KR":
                        from src.data.korea import fetch_korea_stock
                        df = fetch_korea_stock(trade_ticker, days=5)
                    else:
                        from src.data.us import fetch_us_stock
                        df = fetch_us_stock(trade_ticker, period="5d")

                    if not trade_name or trade_name == trade_ticker:
                        try:
                            import yfinance as yf
                            info = yf.Ticker(trade_ticker).info
                            trade_name = info.get("shortName", trade_ticker)
                        except Exception:
                            trade_name = trade_ticker

                    if df.empty:
                        st.error("종목 데이터를 가져올 수 없어요. 코드를 확인해주세요.")
                    else:
                        price = float(df["Close"].iloc[-1])
                        if "매수" in trade_action:
                            msg = port.buy(trade_ticker, trade_name, trade_market, trade_shares, price, reason="수동 매수")
                            st.success(msg)
                        else:
                            msg = port.sell(trade_ticker, trade_shares, price, reason="수동 매도")
                            st.success(msg)
                        st.rerun()
                except Exception as e:
                    st.error(f"오류: {e}")

    st.divider()

    # 자동 매매
    st.subheader("🤖 알고리즘 자동 매매")
    st.markdown('<p class="help-text">분석 점수가 높은 종목은 자동 매수, 낮은 종목은 자동 매도해요 (2~3분 소요)</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("미리보기 (실행 안 함)", use_container_width=True, key="paper_dry"):
            with st.spinner("전 종목 분석 중..."):
                actions = auto_trade(port, dry_run=True)
            if actions:
                for a in actions:
                    st.info(a)
                st.caption(f"총 {len(actions)}건 예정")
            else:
                st.success("현재 실행할 거래가 없어요.")
    with col2:
        if st.button("자동 매매 실행", type="primary", use_container_width=True, key="paper_auto"):
            with st.spinner("전 종목 분석 후 매매 실행 중..."):
                actions = auto_trade(port)
            if actions:
                for a in actions:
                    st.success(a)
                st.caption(f"총 {len(actions)}건 실행 완료")
                st.rerun()
            else:
                st.success("현재 실행할 거래가 없어요.")

    st.divider()

    # 거래 내역
    st.subheader("거래 기록")
    if port.trades:
        trade_rows = []
        for t in reversed(port.trades[-30:]):
            curr = "$" if t.market == "US" else "원"
            price_str = f"${t.price:,.2f}" if t.market == "US" else f"{t.price:,.0f}원"
            pnl_str = f"{t.pnl_pct:+.2f}%" if t.pnl_pct is not None else ""
            trade_rows.append({
                "날짜": t.date,
                "종목": f"{t.name} ({t.ticker})",
                "매매": "매수" if t.action == "buy" else "매도",
                "수량": t.shares,
                "가격": price_str,
                "수익률": pnl_str,
                "이유": t.reason,
            })
        st.dataframe(pd.DataFrame(trade_rows), use_container_width=True, hide_index=True)
    else:
        st.info("아직 거래 기록이 없어요.")

    # 포트폴리오 초기화
    st.divider()
    with st.expander("포트폴리오 초기화 (처음부터 다시 시작)"):
        st.warning("초기화하면 모든 보유 종목과 거래 기록이 삭제돼요.")
        if st.button("초기화", key="paper_reset"):
            new_port = PaperPortfolio()
            new_port.save()
            st.success("포트폴리오가 초기화됐어요!")
            st.rerun()


# ─── 글로벌 이슈 트래커 ───


TOPIC_FRIENDLY = {
    "AI_반도체": ("🤖 AI / 반도체", "AI 기술과 반도체 산업 동향"),
    "지정학_전쟁": ("⚔️ 전쟁 / 지정학", "국제 분쟁과 군사 긴장"),
    "에너지": ("⛽ 에너지", "원유·가스·에너지 시장"),
    "인물_발언": ("🎤 주요 인물 발언", "트럼프·머스크·파월 등 시장 영향력 있는 발언"),
    "경제_정책": ("🏦 경제 정책", "금리·통화·재정 정책"),
    "암호화폐": ("₿ 암호화폐", "비트코인·가상자산 시장"),
}

THEME_TICKERS = {
    "AI_반도체": {
        "NVDA": "NVIDIA (AI GPU 1위)",
        "AMD": "AMD (AI 칩 2위)",
        "TSM": "TSMC (파운드리 1위)",
        "AVGO": "Broadcom (AI 네트워킹)",
        "005930.KS": "삼성전자 (HBM 메모리)",
        "000660.KS": "SK하이닉스 (HBM 메모리)",
    },
    "지정학_전쟁": {
        "GLD": "금 ETF (안전자산)",
        "LMT": "록히드마틴 (방산)",
        "RTX": "RTX (방산)",
        "012450.KS": "한화에어로스페이스 (방산)",
        "329180.KS": "HD현대중공업 (조선/방산)",
    },
    "에너지": {
        "XOM": "엑슨모빌 (석유)",
        "CVX": "셰브론 (석유)",
        "^GSPC": "S&P 500 (비교용)",
    },
    "인물_발언": {
        "TSLA": "테슬라 (머스크)",
        "NVDA": "NVIDIA (젠슨 황)",
        "META": "메타 (저커버그)",
    },
    "경제_정책": {
        "TLT": "미국 장기채 ETF",
        "GLD": "금 ETF",
        "^TNX": "미국 10년 금리",
    },
    "암호화폐": {
        "BTC-USD": "비트코인",
        "ETH-USD": "이더리움",
    },
}

ENERGY_TICKERS = {
    "CL=F": "WTI 원유",
    "BZ=F": "브렌트유",
    "NG=F": "천연가스",
    "URA": "우라늄 ETF",
}


@st.cache_data(ttl=600)
def _fetch_theme_prices(tickers: dict, period: str = "3mo") -> dict:
    import yfinance as yf
    result = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if not df.empty:
                result[ticker] = df
        except Exception:
            pass
    return result


@st.cache_data(ttl=900)
def _fetch_topic_news_cached(topic: str):
    from src.data.news import fetch_topic_news
    return fetch_topic_news(topic)


@st.cache_data(ttl=900)
def _fetch_all_news_cached():
    from src.data.news import fetch_all_topic_news
    return fetch_all_topic_news()


@st.cache_data(ttl=600)
def _fetch_energy_prices():
    import yfinance as yf
    result = {}
    for ticker, name in ENERGY_TICKERS.items():
        try:
            df = yf.download(ticker, period="6mo", progress=False, auto_adjust=True)
            if not df.empty:
                result[ticker] = {"name": name, "df": df}
        except Exception:
            pass
    return result


def page_global_tracker():
    st.title("🌍 글로벌 이슈 트래커")
    st.markdown('<p class="help-text">전 세계 주요 이슈를 추적하고, 내 투자에 미치는 영향을 실시간으로 확인해요 (약 15분 간격 데이터)</p>', unsafe_allow_html=True)

    from src.data.news import detect_chain_events
    from src.engine.chain import trace_chain, get_actionable, CAUSAL_GRAPH

    # 자동 갱신 설정
    auto_col1, auto_col2 = st.columns([3, 1])
    with auto_col2:
        auto_refresh = st.checkbox("자동 새로고침 (10분)", value=False)
    if auto_refresh:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=600_000, key="global_tracker_refresh")
        except ImportError:
            st.caption("자동 새로고침을 사용하려면: pip install streamlit-autorefresh")

    # ── 뉴스 기반 이슈 감지 ──
    st.markdown("### 🚨 지금 감지된 이슈")
    st.markdown('<p class="help-text">최근 뉴스 헤드라인에서 시장에 영향을 줄 수 있는 이슈를 자동 감지해요</p>', unsafe_allow_html=True)

    all_news = _fetch_all_news_cached()
    all_headlines = []
    for topic_headlines in all_news.values():
        all_headlines.extend(topic_headlines)

    detected = detect_chain_events(all_headlines)

    if detected:
        cols = st.columns(min(len(detected), 4))
        EVENT_FRIENDLY_GLOBAL = {
            "트럼프관세": "🇺🇸 트럼프 관세",
            "무역전쟁": "🚢 무역전쟁",
            "금리인상": "📈 금리 인상",
            "금리인하": "📉 금리 인하",
            "원유급등": "🛢️ 유가 급등",
            "원유급락": "🛢️ 유가 급락",
            "대만해협긴장": "⚔️ 대만 긴장",
            "중동긴장": "⚔️ 중동 긴장",
            "전쟁": "⚔️ 전쟁",
            "인플레이션급등": "📈 인플레이션",
            "AI버블": "🤖 AI 과열",
            "반도체업사이클": "💻 반도체 호황",
            "양적완화": "💰 양적완화",
            "양적긴축": "💰 양적긴축",
            "공급망위기": "📦 공급망 위기",
            "달러강세": "💵 달러 강세",
            "중국경기둔화": "🇨🇳 중국 둔화",
            "일본엔저": "🇯🇵 엔저",
            "일본금리인상": "🇯🇵 BOJ 금리",
            "미국대선": "🗳️ 미국 대선",
            "정부셧다운": "🏛️ 셧다운",
            "암호화폐폭락": "₿ 암호화폐",
            "은행위기": "🏦 은행 위기",
            "부동산위기": "🏠 부동산",
            "팬데믹": "🦠 전염병",
            "기후변화규제": "🌍 기후규제",
            "인물발언": "🎤 인물 발언",
        }
        for i, det in enumerate(detected[:4]):
            with cols[i]:
                event_label = EVENT_FRIENDLY_GLOBAL.get(det["event"], det["event"])
                st.markdown(f"**{event_label}**")
                st.caption(f'"{det["headline"][:60]}..."' if len(det["headline"]) > 60 else f'"{det["headline"]}"')
                st.caption(f"{det['source']} · {det['published'][:10] if det['published'] else ''}")

        with st.expander("감지된 이슈가 내 투자에 미치는 영향 보기", expanded=True):
            for det in detected[:6]:
                event = det["event"]
                if event in CAUSAL_GRAPH:
                    chains = trace_chain(event)
                    if chains:
                        actions = get_actionable(chains)
                        event_label = EVENT_FRIENDLY_GLOBAL.get(event, event)
                        st.markdown(f"#### {event_label}")

                        c1, c2 = st.columns(2)
                        with c1:
                            if actions["long"]:
                                for item in actions["long"][:3]:
                                    st.success(f"📈 **{item['target']}** [{', '.join(item['tickers'][:3])}] — {item['reason']}")
                        with c2:
                            if actions["short"]:
                                for item in actions["short"][:3]:
                                    st.error(f"📉 **{item['target']}** [{', '.join(item['tickers'][:3])}] — {item['reason']}")
                        st.divider()
    else:
        st.info("현재 뉴스에서 특별한 이슈가 감지되지 않았어요. 시장이 안정적인 상태입니다.")

    # ── 테마별 뉴스 + 차트 ──
    st.markdown("### 📰 테마별 뉴스 & 관련 자산")

    selected_topic = st.selectbox(
        "관심 테마 선택",
        list(TOPIC_FRIENDLY.keys()),
        format_func=lambda x: f"{TOPIC_FRIENDLY[x][0]} — {TOPIC_FRIENDLY[x][1]}",
    )

    topic_name, topic_desc = TOPIC_FRIENDLY[selected_topic]

    news_col, chart_col = st.columns([1, 1])

    with news_col:
        st.markdown(f"#### {topic_name} 최신 뉴스")
        headlines = _fetch_topic_news_cached(selected_topic)
        if headlines:
            for h in headlines[:10]:
                source_text = f" · {h.source}" if h.source else ""
                time_text = f" · {h.published[:10]}" if h.published else ""
                st.markdown(f"- [{h.title}]({h.link}){source_text}{time_text}")
        else:
            st.caption("뉴스를 가져오지 못했어요.")

    with chart_col:
        st.markdown(f"#### {topic_name} 관련 자산 추이 (3개월)")
        tickers = THEME_TICKERS.get(selected_topic, {})
        if tickers:
            prices = _fetch_theme_prices(tickers)
            if prices:
                fig = go.Figure()
                for ticker, df in prices.items():
                    label = tickers.get(ticker, ticker)
                    close = df["Close"]
                    if hasattr(close, "columns"):
                        close = close.iloc[:, 0]
                    normalized = (close / close.iloc[0] - 1) * 100
                    fig.update_layout(**CHART_LAYOUT, height=400, yaxis_title="변동률 (%)")
                    fig.add_trace(go.Scatter(
                        x=df.index, y=normalized,
                        name=label, mode="lines",
                    ))
                fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.1)", opacity=0.5)
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("**현재 가격 & 변동:**")
                metric_cols = st.columns(min(len(prices), 3))
                for i, (ticker, df) in enumerate(prices.items()):
                    label = tickers.get(ticker, ticker)
                    close = df["Close"]
                    if hasattr(close, "columns"):
                        close = close.iloc[:, 0]
                    current = close.iloc[-1]
                    ret_3m = (close.iloc[-1] / close.iloc[0] - 1) * 100
                    with metric_cols[i % 3]:
                        short_label = label.split("(")[0].strip()
                        if ".KS" in ticker:
                            st.metric(short_label, f"{current:,.0f}원", f"{ret_3m:+.1f}%")
                        else:
                            st.metric(short_label, f"${current:,.2f}", f"{ret_3m:+.1f}%")
            else:
                st.caption("가격 데이터를 가져오지 못했어요.")

    # ── 에너지 대시보드 ──
    st.markdown("### ⛽ 에너지 시장 현황")
    st.markdown('<p class="help-text">원유·가스 가격 변동은 물가와 기업 실적에 직접 영향을 줘요</p>', unsafe_allow_html=True)

    energy_data = _fetch_energy_prices()
    if energy_data:
        e_cols = st.columns(len(energy_data))
        for i, (ticker, info) in enumerate(energy_data.items()):
            df = info["df"]
            close = df["Close"]
            if hasattr(close, "columns"):
                close = close.iloc[:, 0]
            current = close.iloc[-1]
            change_1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100 if len(close) > 22 else 0

            with e_cols[i]:
                st.metric(info["name"], f"${current:,.2f}", f"{change_1m:+.1f}% (1개월)")

        fig_energy = go.Figure()
        for ticker, info in energy_data.items():
            df = info["df"]
            close = df["Close"]
            if hasattr(close, "columns"):
                close = close.iloc[:, 0]
            normalized = (close / close.iloc[0] - 1) * 100
            fig_energy.add_trace(go.Scatter(
                x=df.index, y=normalized,
                name=info["name"], mode="lines",
            ))
        fig_energy.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.1)", opacity=0.5)
        fig_energy.update_layout(**CHART_LAYOUT, height=350, yaxis_title="변동률 (%)", title="에너지 가격 추이 (6개월)")
        st.plotly_chart(fig_energy, use_container_width=True)

        with st.expander("에너지 가격이 내 투자에 미치는 영향"):
            wti = energy_data.get("CL=F")
            if wti:
                wti_close = wti["df"]["Close"]
                if hasattr(wti_close, "columns"):
                    wti_close = wti_close.iloc[:, 0]
                wti_price = wti_close.iloc[-1]
                wti_1m = (wti_close.iloc[-1] / wti_close.iloc[-22] - 1) * 100 if len(wti_close) > 22 else 0
                if wti_price > 90:
                    st.warning(f"WTI ${wti_price:.0f}는 높은 수준이에요. 에너지주(XOM, CVX)에는 좋지만, 항공·물류주에는 부담이에요. 인플레이션 압력이 커질 수 있어요.")
                elif wti_price > 70:
                    st.info(f"WTI ${wti_price:.0f}는 보통 수준이에요. 에너지 시장이 안정적이에요.")
                else:
                    st.success(f"WTI ${wti_price:.0f}는 낮은 수준이에요. 항공·물류·소비주에 유리하지만, 에너지주에는 불리해요.")

                if wti_1m > 10:
                    st.error(f"1개월간 {wti_1m:+.1f}% 급등했어요. 인플레이션 우려가 커지고 있어요.")
                elif wti_1m < -10:
                    st.success(f"1개월간 {wti_1m:+.1f}% 급락했어요. 소비자에게는 좋지만 에너지 기업 실적이 나빠질 수 있어요.")

    # ── 지정학 리스크 지수 ──
    st.markdown("### ⚔️ 지정학 리스크 모니터")
    st.markdown('<p class="help-text">금, VIX, 방산주, 유가가 동시에 오르면 지정학 위험이 커지고 있다는 신호예요</p>', unsafe_allow_html=True)

    geo_tickers = {"GLD": "금 ETF", "^VIX": "VIX(변동성)", "LMT": "록히드마틴(방산)", "CL=F": "원유"}
    geo_prices = _fetch_theme_prices(geo_tickers, period="3mo")

    if geo_prices:
        fig_geo = go.Figure()
        for ticker, df in geo_prices.items():
            label = geo_tickers.get(ticker, ticker)
            close = df["Close"]
            if hasattr(close, "columns"):
                close = close.iloc[:, 0]
            normalized = (close / close.iloc[0] - 1) * 100
            fig_geo.add_trace(go.Scatter(
                x=df.index, y=normalized,
                name=label, mode="lines",
            ))
        fig_geo.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.1)", opacity=0.5)
        fig_geo.update_layout(**CHART_LAYOUT, height=350, yaxis_title="변동률 (%)", title="지정학 리스크 관련 자산 (3개월)")
        st.plotly_chart(fig_geo, use_container_width=True)

        all_rising = True
        for ticker, df in geo_prices.items():
            close = df["Close"]
            if hasattr(close, "columns"):
                close = close.iloc[:, 0]
            ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
            if ret < 3:
                all_rising = False

        if all_rising:
            st.error("⚠️ 금, VIX, 방산주, 유가가 모두 상승 중이에요. 지정학 리스크가 높아지고 있어요. 안전자산 비중을 늘리는 것을 고려하세요.")
        else:
            st.success("지정학 리스크 지표들이 안정적이에요. 특별한 위험 신호는 없어요.")


# ─── 사이드바 네비게이션 ───

PAGES = {
    "📊 시장 현황": page_dashboard,
    "🌍 글로벌 이슈": page_global_tracker,
    "🔍 종목 찾기": page_scanner,
    "🔗 무슨 일이 생기면?": page_chain,
    "📈 과거 시뮬레이션": page_backtest,
    "💰 모의 투자": page_paper,
}

with st.sidebar:
    st.markdown("## 💎 투자 도우미")
    st.caption("나만의 투자 분석 앱")
    st.markdown("")
    page = st.radio("메뉴", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("")
    st.markdown("")
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("무료 데이터 · Yahoo · KRX · FRED")

PAGES[page]()
