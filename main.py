#!/usr/bin/env python3
"""투자 알고리즘 — 메인 실행"""

import sys
from rich.console import Console
from rich.panel import Panel

console = Console()


def show_help():
    console.print(Panel(
        "[bold]사용법[/bold]\n\n"
        "  python main.py scan          전체 종목 스캔 + 랭킹\n"
        "  python main.py scan-us       미국 종목만 스캔\n"
        "  python main.py scan-kr       한국 종목만 스캔\n"
        "  python main.py stock AAPL    개별 종목 상세 분석\n"
        "  python main.py macro         거시경제 지표 요약\n"
        "  python main.py regime        현재 매크로 레짐 판단\n"
        "  python main.py sentiment     시장 심리 지표\n"
        "  python main.py chain 원유급등    이벤트 → 인과관계 체인 추적\n"
        "  python main.py chain list       등록된 이벤트 목록\n"
        "  python main.py impact NVDA      종목이 영향받는 이벤트 검색\n"
        "  python main.py backtest AAPL              종목 백테스트 (멀티팩터)\n"
        "  python main.py backtest AAPL momentum     특정 전략 백테스트\n"
        "  python main.py backtest AAPL all          전략 비교 백테스트\n"
        "  python main.py backtest AAPL all 3y       3년 데이터 비교\n\n"
        "[bold]모의 매매[/bold]\n\n"
        "  python main.py paper                 포트폴리오 현황\n"
        "  python main.py paper buy AAPL 10     종목 매수 (수량)\n"
        "  python main.py paper sell AAPL       종목 전량 매도\n"
        "  python main.py paper sell AAPL 5     종목 일부 매도\n"
        "  python main.py paper auto            시그널 기반 자동 매매\n"
        "  python main.py paper dry             자동 매매 미리보기 (실행 안 함)\n"
        "  python main.py paper history         거래 내역\n"
        "  python main.py paper reset           포트폴리오 초기화\n",
        title="투자 알고리즘",
        border_style="cyan",
    ))


def cmd_scan_all():
    from src.engine.scanner import scan_all
    scan_all()


def cmd_scan_us():
    from src.engine.scanner import scan_us_stocks, print_ranking
    results = scan_us_stocks()
    print_ranking(results, "미국 주식 멀티팩터 랭킹")


def cmd_scan_kr():
    from src.engine.scanner import scan_korea_stocks, print_ranking
    results = scan_korea_stocks()
    print_ranking(results, "한국 주식 멀티팩터 랭킹")


def cmd_stock(ticker: str):
    from src.data.us import fetch_us_stock, fetch_us_info
    from src.data.korea import fetch_korea_stock
    from src.data.sentiment import fetch_fear_greed, get_market_regime
    from src.analysis.factors import calculate_multi_factor_score
    from rich.table import Table

    console.print(f"\n[bold cyan]{ticker} 상세 분석[/bold cyan]\n")

    is_korea = ticker.isdigit() and len(ticker) == 6

    if is_korea:
        price_df = fetch_korea_stock(ticker, days=365)
        info = None
    else:
        price_df = fetch_us_stock(ticker, period="1y")
        try:
            info = fetch_us_info(ticker)
        except Exception:
            info = None

    if price_df.empty:
        console.print("[red]데이터를 가져올 수 없습니다.[/red]")
        return

    sentiment = fetch_fear_greed()
    regime = get_market_regime()
    result = calculate_multi_factor_score(price_df, info, sentiment, regime)

    score = result["final_score"]
    signal = result["signal"]
    style = "green" if score >= 15 else ("red" if score <= -15 else "yellow")

    console.print(Panel(
        f"[bold {style}]종합 점수: {score:.1f}  →  {signal}[/bold {style}]",
        title=ticker,
        border_style=style,
    ))

    # 팩터 점수
    ft = Table(title="팩터별 점수", show_lines=True)
    ft.add_column("팩터", width=15)
    ft.add_column("점수", justify="center", width=8)
    ft.add_column("가중치", justify="center", width=8)
    ft.add_column("기여", justify="center", width=8)

    factors = result["factor_scores"]
    weights = result["weights"]
    for k in factors:
        s = factors[k]
        w = weights[k]
        contrib = s * w
        color = "green" if s > 0 else ("red" if s < 0 else "white")
        ft.add_row(k, f"[{color}]{s}[/{color}]", f"{w:.0%}", f"[{color}]{contrib:.1f}[/{color}]")
    console.print(ft)

    # 기술적 상세
    if result.get("technical_details"):
        tt = Table(title="기술적 분석 상세", show_lines=True)
        tt.add_column("지표", width=15)
        tt.add_column("상태", width=35)
        for k, v in result["technical_details"].items():
            tt.add_row(k, str(v))
        console.print(tt)

    # 밸류에이션 상세
    if result.get("valuation_details"):
        vt = Table(title="밸류에이션 상세", show_lines=True)
        vt.add_column("지표", width=15)
        vt.add_column("값", width=35)
        for k, v in result["valuation_details"].items():
            vt.add_row(k, str(v))
        console.print(vt)

    # 시장 환경
    console.print(f"\n  시장 심리: {sentiment.get('rating', 'N/A')} ({sentiment.get('score', 'N/A')})")
    console.print(f"  매크로 레짐: {regime.get('regime', 'N/A')} — {regime.get('description', '')}")


def cmd_macro():
    from src.data.macro import get_macro_summary
    from rich.table import Table

    console.print("\n[bold cyan]거시경제 지표 요약[/bold cyan]\n")
    summary = get_macro_summary()

    if "error" in summary:
        console.print(f"[red]{summary['error']}[/red]")
        console.print("  .env 파일에 FRED_API_KEY를 설정하세요.")
        console.print("  발급: https://fred.stlouisfed.org/docs/api/api_key.html")
        return

    table = Table(show_lines=True)
    table.add_column("지표", width=18)
    table.add_column("최신값", justify="right", width=12)
    table.add_column("전월/전기", justify="right", width=12)
    table.add_column("변화", justify="right", width=10)
    table.add_column("기준일", width=12)

    for name, data in summary.items():
        if "error" in data:
            table.add_row(name, "[red]오류[/red]", "", "", "")
            continue
        latest = data["latest"]
        prev = data.get("previous")
        change = data.get("change")

        if change is not None:
            color = "green" if change > 0 else ("red" if change < 0 else "white")
            change_str = f"[{color}]{change:+.4f}[/{color}]"
        else:
            change_str = ""

        table.add_row(
            name,
            f"{latest:.4f}",
            f"{prev:.4f}" if prev else "",
            change_str,
            data.get("date", ""),
        )

    console.print(table)


def cmd_regime():
    from src.data.sentiment import get_market_regime
    from rich.table import Table

    console.print("\n[bold cyan]매크로 레짐 분석[/bold cyan]\n")
    regime = get_market_regime()

    r = regime.get("regime", "unknown")
    colors = {
        "골디락스": "green",
        "리플레이션": "yellow",
        "스태그플레이션": "red",
        "침체/디플레": "red",
        "전환기": "yellow",
    }
    color = colors.get(r, "white")

    console.print(Panel(
        f"[bold {color}]{r}[/bold {color}]\n{regime.get('description', '')}",
        title="현재 레짐",
        border_style=color,
    ))

    table = Table(show_lines=True)
    table.add_column("지표", width=20)
    table.add_column("값", justify="right", width=15)

    table.add_row("VIX", f"{regime.get('vix', 'N/A')}")
    table.add_row("VIX 3개월 평균", f"{regime.get('vix_avg_3m', 'N/A')}")
    table.add_row("10Y 국채금리", f"{regime.get('rate_10y', 'N/A')}%")
    table.add_row("금리 추세", f"{regime.get('rate_trend', 'N/A')}")
    table.add_row("S&P 500 3개월 수익률", f"{regime.get('sp500_3m_return', 'N/A')}%")
    console.print(table)


def cmd_sentiment():
    from src.data.sentiment import fetch_fear_greed, fetch_vix

    console.print("\n[bold cyan]시장 심리 지표[/bold cyan]\n")

    fg = fetch_fear_greed()
    score = fg.get("score")
    rating = fg.get("rating", "N/A")

    if score is not None:
        if score < 25:
            color = "red"
        elif score < 45:
            color = "yellow"
        elif score < 55:
            color = "white"
        elif score < 75:
            color = "green"
        else:
            color = "bright_green"

        bar_len = int(score / 2)
        bar = "█" * bar_len + "░" * (50 - bar_len)
        console.print(f"  Fear & Greed: [{color}]{score} — {rating}[/{color}]")
        console.print(f"  [{color}]{bar}[/{color}]")
        console.print(f"  0=극단공포 ←————————→ 100=극단탐욕\n")
    else:
        console.print(f"  Fear & Greed: {rating}")

    vix_df = fetch_vix(period="1mo")
    if not vix_df.empty:
        vix_now = vix_df["VIX"].iloc[-1]
        vix_min = vix_df["VIX"].min()
        vix_max = vix_df["VIX"].max()
        vix_avg = vix_df["VIX"].mean()
        console.print(f"  VIX 현재: {vix_now:.2f}")
        console.print(f"  VIX 1개월: 최저 {vix_min:.2f} / 평균 {vix_avg:.2f} / 최고 {vix_max:.2f}")

        if vix_now > 35:
            console.print("  [red bold]→ 극단적 공포 구간: 역사적 매수 기회[/red bold]")
        elif vix_now > 25:
            console.print("  [red]→ 공포 구간: 주의 필요[/red]")
        elif vix_now < 12:
            console.print("  [bright_green]→ 극단적 자만: 급락 주의[/bright_green]")


def cmd_chain(event: str):
    from src.engine.chain import trace_chain, get_actionable, ALL_EVENTS
    from rich.table import Table
    from rich.tree import Tree

    if event == "list":
        console.print("\n[bold cyan]등록된 이벤트 목록[/bold cyan]\n")
        for i, e in enumerate(ALL_EVENTS, 1):
            console.print(f"  {i:2d}. {e}")
        console.print(f"\n  총 {len(ALL_EVENTS)}개 이벤트")
        console.print("  사용법: python main.py chain 원유급등")
        return

    chains = trace_chain(event)
    if chains is None:
        console.print(f"\n[red]'{event}' 이벤트를 찾을 수 없습니다.[/red]")
        console.print("  등록된 이벤트 보기: python main.py chain list")
        return

    event_name = chains[0].event
    console.print(f"\n[bold cyan]인과관계 체인: {event_name}[/bold cyan]\n")

    tree = Tree(f"[bold yellow]{event_name}[/bold yellow]")

    for chain in chains:
        branch = tree.add(f"[bold]{chain.label}[/bold]")
        for impact in chain.impacts:
            dir_icon = "[green]▲[/green]" if impact.direction == "+" else "[red]▼[/red]"
            conf_color = {"A": "green", "B": "yellow", "C": "white", "D": "dim"}.get(impact.confidence, "white")
            ticker_str = f" [{', '.join(impact.tickers)}]" if impact.tickers else ""
            branch.add(
                f"{dir_icon} {impact.target} "
                f"[{conf_color}](확신도 {impact.confidence})[/{conf_color}] "
                f"— {impact.reason}{ticker_str}"
            )

    console.print(tree)

    # 투자 액션 요약
    actions = get_actionable(chains)

    if actions["long"]:
        console.print("\n[bold green]▲ 매수 검토 (확신도 A/B)[/bold green]")
        lt = Table(show_lines=True)
        lt.add_column("대상", width=20)
        lt.add_column("티커", width=25)
        lt.add_column("사유", width=30)
        lt.add_column("확신", width=4, justify="center")
        lt.add_column("차수", width=4, justify="center")
        for item in actions["long"]:
            lt.add_row(item["target"], ", ".join(item["tickers"]), item["reason"], item["confidence"], str(item["depth"]))
        console.print(lt)

    if actions["short"]:
        console.print("\n[bold red]▼ 매도/숏 검토 (확신도 A/B)[/bold red]")
        st = Table(show_lines=True)
        st.add_column("대상", width=20)
        st.add_column("티커", width=25)
        st.add_column("사유", width=30)
        st.add_column("확신", width=4, justify="center")
        st.add_column("차수", width=4, justify="center")
        for item in actions["short"]:
            st.add_row(item["target"], ", ".join(item["tickers"]), item["reason"], item["confidence"], str(item["depth"]))
        console.print(st)

    if actions["watch"]:
        console.print("\n[dim]👁 모니터링 (확신도 C/D)[/dim]")
        for item in actions["watch"]:
            console.print(f"  · {item['target']} [{', '.join(item['tickers'])}] — {item['reason']}")


def cmd_impact(ticker: str):
    from src.engine.chain import search_by_ticker
    from rich.table import Table

    console.print(f"\n[bold cyan]{ticker}에 영향을 주는 이벤트[/bold cyan]\n")

    results = search_by_ticker(ticker)
    if not results:
        console.print(f"  [yellow]'{ticker}'가 등록된 인과관계에 없습니다.[/yellow]")
        return

    table = Table(show_lines=True)
    table.add_column("이벤트", width=18)
    table.add_column("차수", width=4, justify="center")
    table.add_column("영향 대상", width=20)
    table.add_column("방향", width=4, justify="center")
    table.add_column("확신", width=4, justify="center")
    table.add_column("사유", width=35)

    for r in results:
        dir_str = "[green]▲[/green]" if r["direction"] == "+" else "[red]▼[/red]"
        table.add_row(
            r["event"],
            str(r["depth"]),
            r["target"],
            dir_str,
            r["confidence"],
            r["reason"],
        )

    console.print(table)
    console.print(f"\n  총 {len(results)}개 시나리오에서 영향받음")


def cmd_backtest(ticker: str, strategy: str = "multifactor", period: str = "2y"):
    from src.data.us import fetch_us_stock
    from src.data.korea import fetch_korea_stock
    from src.engine.backtest import (
        run_backtest, print_backtest_result, run_all_strategies, STRATEGIES,
    )

    period_map = {"1y": 365, "2y": 730, "3y": 1095, "5y": 1825, "10y": 3650}
    is_korea = ticker.isdigit() and len(ticker) == 6

    console.print(f"\n[bold cyan]{ticker} 백테스트 ({period})[/bold cyan]\n")

    if is_korea:
        days = period_map.get(period, 730)
        df = fetch_korea_stock(ticker, days=days)
    else:
        df = fetch_us_stock(ticker, period=period)

    if df.empty or len(df) < 200:
        console.print(f"[red]데이터 부족 (최소 200거래일 필요, 현재 {len(df)}일)[/red]")
        return

    console.print(f"  데이터: {len(df)}거래일")
    capital = 100_000_000 if is_korea else 100_000

    if strategy == "all":
        run_all_strategies(df, initial_capital=capital)
    elif strategy in STRATEGIES:
        result = run_backtest(df, strategy_key=strategy, initial_capital=capital)
        print_backtest_result(result)
    else:
        console.print(f"[red]전략 '{strategy}'를 찾을 수 없습니다.[/red]")
        console.print(f"  사용 가능: {', '.join(STRATEGIES.keys())}, all")


def cmd_paper(args: list[str]):
    from src.engine.paper import PaperPortfolio, auto_trade
    from rich.table import Table

    sub = args[0] if args else "status"

    if sub == "reset":
        port = PaperPortfolio()
        port.save()
        console.print("[green]포트폴리오를 초기화했습니다.[/green]")
        console.print(f"  미국 자본: ${port.cash_us:,.0f}")
        console.print(f"  한국 자본: {port.cash_kr:,.0f}원")
        return

    port = PaperPortfolio.load()

    if sub == "buy" and len(args) >= 3:
        ticker = args[1].upper()
        shares = int(args[2])

        is_korea = ticker.isdigit() and len(ticker) == 6
        market = "KR" if is_korea else "US"

        if is_korea:
            from src.data.korea import fetch_korea_stock
            df = fetch_korea_stock(ticker, days=5)
            from src.config import KOREA_TOP
            name = {v: k for k, v in KOREA_TOP.items()}.get(ticker, ticker)
        else:
            from src.data.us import fetch_us_stock, fetch_us_info
            df = fetch_us_stock(ticker, period="5d")
            from src.config import US_TOP
            name = {v: k for k, v in US_TOP.items()}.get(ticker, ticker)

        if df.empty:
            console.print(f"[red]{ticker} 가격 데이터를 가져올 수 없습니다.[/red]")
            return

        price = float(df["Close"].iloc[-1])
        msg = port.buy(ticker, name, market, shares, price, reason="수동 매수")
        console.print(f"[green]{msg}[/green]")

    elif sub == "sell" and len(args) >= 2:
        ticker = args[1].upper()
        shares = int(args[2]) if len(args) >= 3 else None

        pos = port.get_position(ticker)
        if not pos:
            console.print(f"[red]{ticker}를 보유하고 있지 않습니다.[/red]")
            return

        if pos.market == "KR":
            from src.data.korea import fetch_korea_stock
            df = fetch_korea_stock(ticker, days=5)
        else:
            from src.data.us import fetch_us_stock
            df = fetch_us_stock(ticker, period="5d")

        if df.empty:
            console.print(f"[red]{ticker} 가격 데이터를 가져올 수 없습니다.[/red]")
            return

        price = float(df["Close"].iloc[-1])
        msg = port.sell(ticker, shares, price, reason="수동 매도")
        console.print(f"[yellow]{msg}[/yellow]")

    elif sub == "auto":
        console.print("\n[bold cyan]시그널 기반 자동 모의 매매[/bold cyan]\n")
        console.print("  전 종목 분석 후 매수/매도 실행 중... (2~3분 소요)\n")
        actions = auto_trade(port)
        if actions:
            for a in actions:
                console.print(f"  {a}")
            console.print(f"\n  [green]총 {len(actions)}건 실행 완료[/green]")
        else:
            console.print("  실행할 거래가 없습니다.")

    elif sub == "dry":
        console.print("\n[bold cyan]자동 매매 미리보기 (실행 안 함)[/bold cyan]\n")
        console.print("  전 종목 분석 중... (2~3분 소요)\n")
        actions = auto_trade(port, dry_run=True)
        if actions:
            for a in actions:
                console.print(f"  {a}")
            console.print(f"\n  총 {len(actions)}건 예정 (실행하려면: python main.py paper auto)")
        else:
            console.print("  실행할 거래가 없습니다.")

    elif sub == "history":
        console.print("\n[bold cyan]거래 내역[/bold cyan]\n")
        if not port.trades:
            console.print("  거래 내역이 없습니다.")
            return

        table = Table(show_lines=True, title=f"총 {len(port.trades)}건")
        table.add_column("날짜", width=12)
        table.add_column("종목", width=18)
        table.add_column("매매", width=4, justify="center")
        table.add_column("수량", width=6, justify="right")
        table.add_column("가격", width=14, justify="right")
        table.add_column("수익률", width=8, justify="right")
        table.add_column("사유", width=25)

        for t in port.trades[-30:]:
            action_color = "green" if t.action == "buy" else "red"
            action_str = f"[{action_color}]{'매수' if t.action == 'buy' else '매도'}[/{action_color}]"
            curr = "$" if t.market == "US" else "원"
            price_str = f"{t.price:,.2f}{curr}" if t.market == "US" else f"{t.price:,.0f}{curr}"
            pnl_str = ""
            if t.pnl_pct is not None:
                pnl_color = "green" if t.pnl_pct > 0 else "red"
                pnl_str = f"[{pnl_color}]{t.pnl_pct:+.2f}%[/{pnl_color}]"

            table.add_row(t.date, f"{t.name} ({t.ticker})", action_str,
                          str(t.shares), price_str, pnl_str, t.reason)
        console.print(table)

    else:
        # 기본: 포트폴리오 현황
        console.print("\n[bold cyan]모의 포트폴리오 현황[/bold cyan]\n")
        summary = port.get_portfolio_summary()

        console.print(Panel(
            f"[bold]시작일:[/bold] {summary['created_at']}\n"
            f"[bold]보유 종목:[/bold] {summary['total_positions']}개\n"
            f"[bold]총 거래:[/bold] {summary['total_trades']}건",
            title="포트폴리오 요약",
            border_style="cyan",
        ))

        # 미국
        us_color = "green" if summary["us_return"] >= 0 else "red"
        console.print(f"\n  [bold]미국 계좌[/bold]")
        console.print(f"  현금: ${summary['cash_us']:,.2f}")
        console.print(f"  총 자산: ${summary['total_value_us']:,.2f}")
        console.print(f"  수익률: [{us_color}]{summary['us_return']:+.2f}%[/{us_color}]")

        # 한국
        kr_color = "green" if summary["kr_return"] >= 0 else "red"
        console.print(f"\n  [bold]한국 계좌[/bold]")
        console.print(f"  현금: {summary['cash_kr']:,.0f}원")
        console.print(f"  총 자산: {summary['total_value_kr']:,.0f}원")
        console.print(f"  수익률: [{kr_color}]{summary['kr_return']:+.2f}%[/{kr_color}]")

        # 보유 종목
        if summary["holdings"]:
            console.print(f"\n")
            table = Table(title="보유 종목", show_lines=True)
            table.add_column("종목", width=18)
            table.add_column("코드", width=8)
            table.add_column("수량", width=6, justify="right")
            table.add_column("매수가", width=12, justify="right")
            table.add_column("현재가", width=12, justify="right")
            table.add_column("수익률", width=8, justify="right")
            table.add_column("손익", width=14, justify="right")
            table.add_column("매수일", width=12)

            for h in summary["holdings"]:
                pnl_color = "green" if h["pnl_pct"] > 0 else "red"
                curr = "$" if h["market"] == "US" else "원"
                if h["market"] == "US":
                    ep = f"${h['entry_price']:,.2f}"
                    cp = f"${h['current_price']:,.2f}"
                    pnl_amt = f"${h['pnl_amount']:,.2f}"
                else:
                    ep = f"{h['entry_price']:,.0f}"
                    cp = f"{h['current_price']:,.0f}"
                    pnl_amt = f"{h['pnl_amount']:,.0f}"

                table.add_row(
                    h["name"], h["ticker"], str(h["shares"]),
                    ep, cp,
                    f"[{pnl_color}]{h['pnl_pct']:+.2f}%[/{pnl_color}]",
                    f"[{pnl_color}]{pnl_amt}{curr}[/{pnl_color}]",
                    h["entry_date"],
                )
            console.print(table)
        else:
            console.print("\n  보유 종목이 없습니다.")


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    cmd = sys.argv[1].lower()

    if cmd == "scan":
        cmd_scan_all()
    elif cmd == "scan-us":
        cmd_scan_us()
    elif cmd == "scan-kr":
        cmd_scan_kr()
    elif cmd == "stock" and len(sys.argv) > 2:
        cmd_stock(sys.argv[2].upper())
    elif cmd == "macro":
        cmd_macro()
    elif cmd == "regime":
        cmd_regime()
    elif cmd == "sentiment":
        cmd_sentiment()
    elif cmd == "chain" and len(sys.argv) > 2:
        cmd_chain(sys.argv[2])
    elif cmd == "chain":
        cmd_chain("list")
    elif cmd == "impact" and len(sys.argv) > 2:
        cmd_impact(sys.argv[2].upper())
    elif cmd == "backtest" and len(sys.argv) > 2:
        ticker = sys.argv[2].upper()
        strategy = sys.argv[3] if len(sys.argv) > 3 else "multifactor"
        period = sys.argv[4] if len(sys.argv) > 4 else "2y"
        cmd_backtest(ticker, strategy, period)
    elif cmd == "paper":
        cmd_paper(sys.argv[2:])
    else:
        show_help()


if __name__ == "__main__":
    main()
