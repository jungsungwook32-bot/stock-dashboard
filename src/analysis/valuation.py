"""밸류에이션 분석"""

import numpy as np


def score_valuation(info: dict) -> dict:
    score = 0
    details = {}

    # PER
    pe = info.get("pe_ratio")
    if pe is not None and pe > 0:
        if pe < 10:
            score += 25
            details["PER"] = f"{pe:.1f} (저평가)"
        elif pe < 20:
            score += 10
            details["PER"] = f"{pe:.1f} (적정)"
        elif pe < 35:
            score -= 5
            details["PER"] = f"{pe:.1f} (고평가)"
        else:
            score -= 20
            details["PER"] = f"{pe:.1f} (고평가 주의)"
    else:
        details["PER"] = "N/A (적자 또는 데이터 없음)"

    # Forward PER
    fpe = info.get("forward_pe")
    if fpe is not None and fpe > 0:
        if fpe < 15:
            score += 10
            details["Forward PER"] = f"{fpe:.1f} (매력적)"
        elif fpe < 25:
            details["Forward PER"] = f"{fpe:.1f} (적정)"
        else:
            score -= 10
            details["Forward PER"] = f"{fpe:.1f} (부담)"

    # PBR
    pb = info.get("pb_ratio")
    if pb is not None and pb > 0:
        if pb < 1:
            score += 15
            details["PBR"] = f"{pb:.2f} (순자산 대비 저평가)"
        elif pb < 3:
            score += 5
            details["PBR"] = f"{pb:.2f} (적정)"
        else:
            score -= 5
            details["PBR"] = f"{pb:.2f} (고평가)"

    # PEG
    peg = info.get("peg_ratio")
    if peg is not None and peg > 0:
        if peg < 1:
            score += 20
            details["PEG"] = f"{peg:.2f} (성장 대비 저평가)"
        elif peg < 2:
            score += 5
            details["PEG"] = f"{peg:.2f} (적정)"
        else:
            score -= 10
            details["PEG"] = f"{peg:.2f} (성장 대비 고평가)"

    # ROE
    roe = info.get("roe")
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct > 20:
            score += 15
            details["ROE"] = f"{roe_pct:.1f}% (우수)"
        elif roe_pct > 10:
            score += 5
            details["ROE"] = f"{roe_pct:.1f}% (양호)"
        elif roe_pct > 0:
            details["ROE"] = f"{roe_pct:.1f}% (보통)"
        else:
            score -= 10
            details["ROE"] = f"{roe_pct:.1f}% (적자)"

    # 배당수익률
    div = info.get("dividend_yield")
    if div is not None and div > 0:
        div_pct = div * 100
        if div_pct > 4:
            score += 10
            details["배당수익률"] = f"{div_pct:.2f}% (고배당)"
        elif div_pct > 2:
            score += 5
            details["배당수익률"] = f"{div_pct:.2f}%"
        else:
            details["배당수익률"] = f"{div_pct:.2f}%"

    # 부채비율
    de = info.get("debt_to_equity")
    if de is not None:
        if de > 200:
            score -= 15
            details["부채비율"] = f"{de:.0f}% (과다)"
        elif de > 100:
            score -= 5
            details["부채비율"] = f"{de:.0f}% (보통)"
        else:
            score += 5
            details["부채비율"] = f"{de:.0f}% (안정)"

    score = max(-100, min(100, score))
    if score >= 30:
        signal = "저평가"
    elif score <= -20:
        signal = "고평가"
    else:
        signal = "적정"

    return {"signal": signal, "score": score, "details": details}
