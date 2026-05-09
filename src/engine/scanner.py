"""전체 종목 스캔 및 랭킹"""

import pandas as pd
from rich.console import Console
from rich.table import Table

from src.data.us import fetch_us_stock, fetch_us_info
from src.data.korea import fetch_korea_stock
from src.data.sentiment import fetch_fear_greed, get_market_regime
from src.analysis.factors import calculate_multi_factor_score
from src.config import US_TOP, KOREA_TOP

console = Console()


def scan_us_stocks() -> list[dict]:
    console.print("\n[bold cyan]미국 주식 스캔 시작...[/bold cyan]")

    sentiment = fetch_fear_greed()
    regime = get_market_regime()

    console.print(f"  시장 심리: {sentiment.get('rating', 'N/A')} ({sentiment.get('score', 'N/A')})")
    console.print(f"  매크로 레짐: {regime.get('regime', 'N/A')} — {regime.get('description', '')}")

    results = []
    for name, ticker in US_TOP.items():
        try:
            console.print(f"  분석 중: {name} ({ticker})...", end=" ")
            price_df = fetch_us_stock(ticker, period="1y")
            if price_df.empty:
                console.print("[red]데이터 없음[/red]")
                continue

            info = fetch_us_info(ticker)
            result = calculate_multi_factor_score(price_df, info, sentiment, regime)
            result["name"] = name
            result["ticker"] = ticker
            result["market"] = "US"
            results.append(result)
            console.print(f"[green]{result['signal']}[/green] ({result['final_score']:.1f})")
        except Exception as e:
            console.print(f"[red]실패: {e}[/red]")

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results


def scan_korea_stocks() -> list[dict]:
    console.print("\n[bold cyan]한국 주식 스캔 시작...[/bold cyan]")

    sentiment = fetch_fear_greed()
    regime = get_market_regime()

    results = []
    for name, code in KOREA_TOP.items():
        try:
            console.print(f"  분석 중: {name} ({code})...", end=" ")
            price_df = fetch_korea_stock(code, days=365)
            if price_df.empty:
                console.print("[red]데이터 없음[/red]")
                continue

            result = calculate_multi_factor_score(price_df, None, sentiment, regime)
            result["name"] = name
            result["ticker"] = code
            result["market"] = "KR"
            results.append(result)
            console.print(f"[green]{result['signal']}[/green] ({result['final_score']:.1f})")
        except Exception as e:
            console.print(f"[red]실패: {e}[/red]")

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results


def print_ranking(results: list[dict], title: str = "랭킹"):
    table = Table(title=title, show_lines=True)
    table.add_column("순위", justify="center", width=4)
    table.add_column("종목", width=20)
    table.add_column("티커", width=8)
    table.add_column("가격", justify="right", width=12)
    table.add_column("점수", justify="center", width=8)
    table.add_column("판단", justify="center", width=10)
    table.add_column("기술적", justify="center", width=6)
    table.add_column("모멘텀", justify="center", width=6)
    table.add_column("밸류", justify="center", width=6)
    table.add_column("심리", justify="center", width=6)

    for i, r in enumerate(results, 1):
        score = r["final_score"]
        signal = r["signal"]

        if score >= 15:
            style = "green"
        elif score <= -15:
            style = "red"
        else:
            style = "yellow"

        factors = r.get("factor_scores", {})
        price = r.get("price", 0)
        price_str = f"${price:,.2f}" if r["market"] == "US" else f"{price:,.0f}원"

        table.add_row(
            str(i),
            r["name"],
            r["ticker"],
            price_str,
            f"[{style}]{score:.1f}[/{style}]",
            f"[{style}]{signal}[/{style}]",
            str(factors.get("기술적", 0)),
            str(factors.get("모멘텀", 0)),
            str(factors.get("밸류에이션", 0)),
            str(factors.get("심리", 0)),
        )

    console.print(table)


def scan_all():
    us_results = scan_us_stocks()
    kr_results = scan_korea_stocks()

    console.print("\n")
    print_ranking(us_results, "🇺🇸 미국 주식 멀티팩터 랭킹")
    console.print("\n")
    print_ranking(kr_results, "🇰🇷 한국 주식 멀티팩터 랭킹")

    return {"us": us_results, "kr": kr_results}
