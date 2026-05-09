"""백테스트 엔진

과거 데이터로 멀티팩터 전략을 검증.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.analysis.technical import add_technical_indicators, rsi, macd, sma, bollinger_bands, atr

console = Console()


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    direction: str  # "long" or "short"
    reason_entry: str
    reason_exit: str

    @property
    def pnl_pct(self) -> float:
        if self.direction == "long":
            return (self.exit_price / self.entry_price - 1) * 100
        else:
            return (self.entry_price / self.exit_price - 1) * 100

    @property
    def is_win(self) -> bool:
        return self.pnl_pct > 0


@dataclass
class BacktestResult:
    name: str
    period: str
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    benchmark_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))


# ─── 전략 정의 ───


def _signal_momentum(df: pd.DataFrame) -> pd.Series:
    """듀얼 모멘텀: 60일 수익률 양수 + 20일 SMA 위에 있으면 매수"""
    close = df["Close"]
    ret_60 = close.pct_change(60)
    sma_20 = sma(close, 20)

    signal = pd.Series(0, index=df.index)
    signal[(ret_60 > 0) & (close > sma_20)] = 1
    signal[(ret_60 < -0.05) | (close < sma_20 * 0.97)] = -1
    return signal


def _signal_meanrevert(df: pd.DataFrame) -> pd.Series:
    """평균회귀: RSI 과매도에 매수, 과매수에 매도"""
    rsi_val = rsi(df["Close"], 14)

    signal = pd.Series(0, index=df.index)
    signal[rsi_val < 30] = 1
    signal[rsi_val > 70] = -1
    return signal


def _signal_golden_cross(df: pd.DataFrame) -> pd.Series:
    """골든크로스/데드크로스: 50일선이 200일선 돌파"""
    sma_50 = sma(df["Close"], 50)
    sma_200 = sma(df["Close"], 200)

    signal = pd.Series(0, index=df.index)
    signal[sma_50 > sma_200] = 1
    signal[sma_50 <= sma_200] = -1
    return signal


def _signal_bollinger(df: pd.DataFrame) -> pd.Series:
    """볼린저 밴드: 하단 이탈 시 매수, 상단 돌파 시 매도"""
    bb = bollinger_bands(df["Close"], 20, 2.0)
    close = df["Close"]

    signal = pd.Series(0, index=df.index)
    signal[close < bb["BB_Lower"]] = 1
    signal[close > bb["BB_Upper"]] = -1
    return signal


def _signal_volatility_breakout(df: pd.DataFrame, k: float = 0.5) -> pd.Series:
    """변동성 돌파 (래리 윌리엄스): 당일 가격 > 전일종가 + k*전일Range"""
    prev_close = df["Close"].shift(1)
    prev_range = (df["High"] - df["Low"]).shift(1)
    target = prev_close + k * prev_range

    signal = pd.Series(0, index=df.index)
    signal[df["High"] > target] = 1
    return signal


def _signal_multifactor(df: pd.DataFrame) -> pd.Series:
    """멀티팩터 통합 시그널: 여러 전략의 가중 합산"""
    s_mom = _signal_momentum(df) * 0.30
    s_mr = _signal_meanrevert(df) * 0.20
    s_gc = _signal_golden_cross(df) * 0.25
    s_bb = _signal_bollinger(df) * 0.15
    s_vb = _signal_volatility_breakout(df) * 0.10

    combined = s_mom + s_mr + s_gc + s_bb + s_vb

    signal = pd.Series(0, index=df.index)
    signal[combined > 0.3] = 1
    signal[combined < -0.2] = -1
    return signal


STRATEGIES = {
    "momentum": ("듀얼 모멘텀", _signal_momentum),
    "meanrevert": ("평균회귀 (RSI)", _signal_meanrevert),
    "goldencross": ("골든크로스", _signal_golden_cross),
    "bollinger": ("볼린저 밴드", _signal_bollinger),
    "breakout": ("변동성 돌파", _signal_volatility_breakout),
    "multifactor": ("멀티팩터 통합", _signal_multifactor),
}


# ─── 백테스트 엔진 ───


def run_backtest(
    df: pd.DataFrame,
    strategy_key: str = "multifactor",
    initial_capital: float = 100_000_000,
    commission: float = 0.0015,
    slippage: float = 0.001,
    stop_loss: float = 0.07,
    take_profit: float = 0.15,
) -> BacktestResult:
    if strategy_key not in STRATEGIES:
        raise ValueError(f"전략 '{strategy_key}'을 찾을 수 없습니다. 선택: {list(STRATEGIES.keys())}")

    name, signal_fn = STRATEGIES[strategy_key]
    df = df.copy()

    signal = signal_fn(df)
    close = df["Close"].values
    dates = df.index

    capital = initial_capital
    position = 0
    shares = 0
    entry_price = 0.0
    entry_date = ""
    trades = []
    equity = []

    for i in range(len(df)):
        price = close[i]
        date = str(dates[i].date()) if hasattr(dates[i], 'date') else str(dates[i])

        if position == 0 and signal.iloc[i] == 1:
            cost_per_share = price * (1 + commission + slippage)
            shares = int(capital * 0.95 / cost_per_share)
            if shares > 0:
                entry_price = price
                entry_date = date
                capital -= shares * cost_per_share
                position = 1

        elif position == 1:
            current_return = price / entry_price - 1

            sell = False
            reason = ""

            if current_return <= -stop_loss:
                sell = True
                reason = f"손절 ({current_return*100:.1f}%)"
            elif current_return >= take_profit:
                sell = True
                reason = f"익절 ({current_return*100:.1f}%)"
            elif signal.iloc[i] == -1:
                sell = True
                reason = "시그널 매도"

            if sell:
                proceeds = shares * price * (1 - commission - slippage)
                capital += proceeds
                trades.append(Trade(
                    entry_date=entry_date,
                    exit_date=date,
                    entry_price=entry_price,
                    exit_price=price,
                    direction="long",
                    reason_entry="시그널 매수",
                    reason_exit=reason,
                ))
                position = 0
                shares = 0

        current_value = capital + (shares * price if position == 1 else 0)
        equity.append(current_value)

    if position == 1:
        final_price = close[-1]
        proceeds = shares * final_price * (1 - commission - slippage)
        capital += proceeds
        trades.append(Trade(
            entry_date=entry_date,
            exit_date=str(dates[-1].date()) if hasattr(dates[-1], 'date') else str(dates[-1]),
            entry_price=entry_price,
            exit_price=final_price,
            direction="long",
            reason_entry="시그널 매수",
            reason_exit="백테스트 종료",
        ))

    equity_series = pd.Series(equity, index=dates)
    final_capital = equity[-1] if equity else initial_capital

    total_return = (final_capital / initial_capital - 1) * 100
    trading_days = len(df)
    years = trading_days / 252
    annual_return = ((final_capital / initial_capital) ** (1 / max(years, 0.01)) - 1) * 100

    benchmark_return = (close[-1] / close[0] - 1) * 100

    daily_returns = equity_series.pct_change().dropna()
    sharpe = 0.0
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

    running_max = equity_series.cummax()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100

    wins = [t for t in trades if t.is_win]
    losses = [t for t in trades if not t.is_win]
    win_rate = len(wins) / max(len(trades), 1) * 100
    avg_win = np.mean([t.pnl_pct for t in wins]) if wins else 0
    avg_loss = np.mean([t.pnl_pct for t in losses]) if losses else 0
    total_win_pnl = sum(t.pnl_pct for t in wins)
    total_loss_pnl = abs(sum(t.pnl_pct for t in losses))
    profit_factor = total_win_pnl / max(total_loss_pnl, 0.01)

    return BacktestResult(
        name=name,
        period=f"{str(dates[0].date())} ~ {str(dates[-1].date())}",
        initial_capital=initial_capital,
        final_capital=final_capital,
        total_return=total_return,
        annual_return=annual_return,
        benchmark_return=benchmark_return,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        total_trades=len(trades),
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        trades=trades,
        equity_curve=equity_series,
    )


def print_backtest_result(result: BacktestResult):
    ret_color = "green" if result.total_return > 0 else "red"
    vs_bench = result.total_return - result.benchmark_return
    vs_color = "green" if vs_bench > 0 else "red"

    console.print(Panel(
        f"[bold]전략:[/bold] {result.name}\n"
        f"[bold]기간:[/bold] {result.period}\n"
        f"[bold]초기자본:[/bold] {result.initial_capital:,.0f}원\n"
        f"[bold]최종자본:[/bold] [{ret_color}]{result.final_capital:,.0f}원[/{ret_color}]",
        title="백테스트 결과",
        border_style="cyan",
    ))

    mt = Table(title="성과 지표", show_lines=True)
    mt.add_column("지표", width=22)
    mt.add_column("값", justify="right", width=18)
    mt.add_column("평가", width=15)

    mt.add_row("총 수익률", f"[{ret_color}]{result.total_return:+.2f}%[/{ret_color}]",
               "✓" if result.total_return > 0 else "✗")
    mt.add_row("연환산 수익률", f"[{ret_color}]{result.annual_return:+.2f}%[/{ret_color}]", "")
    mt.add_row("벤치마크(B&H)", f"{result.benchmark_return:+.2f}%", "")
    mt.add_row("초과수익(α)", f"[{vs_color}]{vs_bench:+.2f}%[/{vs_color}]",
               "시장 초과" if vs_bench > 0 else "시장 미달")

    sharpe_eval = "우수" if result.sharpe_ratio > 1 else ("양호" if result.sharpe_ratio > 0.5 else "미흡")
    mt.add_row("샤프 비율", f"{result.sharpe_ratio:.2f}", sharpe_eval)

    mdd_eval = "양호" if result.max_drawdown > -15 else ("주의" if result.max_drawdown > -25 else "위험")
    mt.add_row("최대 낙폭(MDD)", f"[red]{result.max_drawdown:.2f}%[/red]", mdd_eval)

    mt.add_row("총 거래 횟수", f"{result.total_trades}회", "")
    mt.add_row("승률", f"{result.win_rate:.1f}%",
               "양호" if result.win_rate > 50 else "개선 필요")
    mt.add_row("평균 수익 (승)", f"[green]+{result.avg_win:.2f}%[/green]", "")
    mt.add_row("평균 손실 (패)", f"[red]{result.avg_loss:.2f}%[/red]", "")
    mt.add_row("손익비(Profit Factor)", f"{result.profit_factor:.2f}",
               "양호" if result.profit_factor > 1.5 else ("보통" if result.profit_factor > 1 else "미흡"))

    console.print(mt)

    if result.trades:
        console.print(f"\n[bold]최근 거래 내역 (최대 10건)[/bold]")
        tt = Table(show_lines=True)
        tt.add_column("진입일", width=12)
        tt.add_column("청산일", width=12)
        tt.add_column("진입가", justify="right", width=12)
        tt.add_column("청산가", justify="right", width=12)
        tt.add_column("수익률", justify="right", width=10)
        tt.add_column("청산 사유", width=20)

        for t in result.trades[-10:]:
            pnl_color = "green" if t.is_win else "red"
            tt.add_row(
                t.entry_date,
                t.exit_date,
                f"{t.entry_price:,.0f}",
                f"{t.exit_price:,.0f}",
                f"[{pnl_color}]{t.pnl_pct:+.2f}%[/{pnl_color}]",
                t.reason_exit,
            )
        console.print(tt)


def run_all_strategies(df: pd.DataFrame, initial_capital: float = 100_000_000):
    console.print("\n[bold cyan]전략별 비교 백테스트[/bold cyan]\n")

    results = []
    for key in STRATEGIES:
        try:
            r = run_backtest(df, strategy_key=key, initial_capital=initial_capital)
            results.append((key, r))
        except Exception as e:
            console.print(f"  [red]{key} 실패: {e}[/red]")

    results.sort(key=lambda x: x[1].total_return, reverse=True)

    ct = Table(title="전략별 성과 비교", show_lines=True)
    ct.add_column("순위", width=4, justify="center")
    ct.add_column("전략", width=18)
    ct.add_column("총수익률", justify="right", width=10)
    ct.add_column("연환산", justify="right", width=10)
    ct.add_column("샤프", justify="right", width=7)
    ct.add_column("MDD", justify="right", width=9)
    ct.add_column("거래수", justify="right", width=6)
    ct.add_column("승률", justify="right", width=7)
    ct.add_column("손익비", justify="right", width=7)

    benchmark = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
    ct.add_row(
        "-", "[dim]벤치마크(B&H)[/dim]",
        f"{benchmark:+.2f}%", "", "", "", "", "", "",
        style="dim",
    )

    for i, (key, r) in enumerate(results, 1):
        ret_color = "green" if r.total_return > benchmark else "red"
        ct.add_row(
            str(i),
            r.name,
            f"[{ret_color}]{r.total_return:+.2f}%[/{ret_color}]",
            f"{r.annual_return:+.2f}%",
            f"{r.sharpe_ratio:.2f}",
            f"{r.max_drawdown:.1f}%",
            str(r.total_trades),
            f"{r.win_rate:.0f}%",
            f"{r.profit_factor:.2f}",
        )

    console.print(ct)
    return results
