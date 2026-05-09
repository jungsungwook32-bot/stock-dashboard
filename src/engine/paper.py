"""페이퍼 트레이딩 (모의 매매) 엔진

실제 돈 없이 알고리즘 시그널대로 가상 매매를 기록하고 성과를 추적.
"""

import json
import pandas as pd
from datetime import datetime, date
from dataclasses import dataclass, field, asdict
from pathlib import Path

from src.config import BASE_DIR, US_TOP, KOREA_TOP

DATA_FILE = BASE_DIR / "paper_portfolio.json"


@dataclass
class Position:
    ticker: str
    name: str
    market: str  # "US" or "KR"
    shares: int
    entry_price: float
    entry_date: str
    signal_score: float = 0.0

    @property
    def entry_value(self) -> float:
        return self.shares * self.entry_price


@dataclass
class TradeRecord:
    ticker: str
    name: str
    market: str
    action: str  # "buy" or "sell"
    shares: int
    price: float
    date: str
    reason: str = ""
    pnl_pct: float | None = None
    signal_score: float = 0.0


@dataclass
class PaperPortfolio:
    initial_capital_us: float = 100_000.0
    initial_capital_kr: float = 100_000_000.0
    cash_us: float = 100_000.0
    cash_kr: float = 100_000_000.0
    positions: list[Position] = field(default_factory=list)
    trades: list[TradeRecord] = field(default_factory=list)
    created_at: str = ""
    last_updated: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")

    def save(self):
        data = {
            "initial_capital_us": self.initial_capital_us,
            "initial_capital_kr": self.initial_capital_kr,
            "cash_us": self.cash_us,
            "cash_kr": self.cash_kr,
            "positions": [asdict(p) for p in self.positions],
            "trades": [asdict(t) for t in self.trades],
            "created_at": self.created_at,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    @classmethod
    def load(cls) -> "PaperPortfolio":
        if not DATA_FILE.exists():
            return cls()
        data = json.loads(DATA_FILE.read_text())
        port = cls(
            initial_capital_us=data.get("initial_capital_us", 100_000),
            initial_capital_kr=data.get("initial_capital_kr", 100_000_000),
            cash_us=data.get("cash_us", 100_000),
            cash_kr=data.get("cash_kr", 100_000_000),
            positions=[Position(**p) for p in data.get("positions", [])],
            trades=[TradeRecord(**t) for t in data.get("trades", [])],
            created_at=data.get("created_at", ""),
            last_updated=data.get("last_updated", ""),
        )
        return port

    def get_cash(self, market: str) -> float:
        return self.cash_us if market == "US" else self.cash_kr

    def _set_cash(self, market: str, value: float):
        if market == "US":
            self.cash_us = value
        else:
            self.cash_kr = value

    def get_position(self, ticker: str) -> Position | None:
        for p in self.positions:
            if p.ticker == ticker:
                return p
        return None

    def buy(self, ticker: str, name: str, market: str, shares: int,
            price: float, reason: str = "", signal_score: float = 0.0,
            commission: float = 0.0015) -> str:
        cost = shares * price * (1 + commission)
        cash = self.get_cash(market)

        if cost > cash:
            max_shares = int(cash / (price * (1 + commission)))
            if max_shares <= 0:
                return f"잔고 부족 (필요: {cost:,.0f}, 보유: {cash:,.0f})"
            shares = max_shares
            cost = shares * price * (1 + commission)

        existing = self.get_position(ticker)
        if existing:
            total_shares = existing.shares + shares
            avg_price = (existing.shares * existing.entry_price + shares * price) / total_shares
            existing.shares = total_shares
            existing.entry_price = round(avg_price, 4)
        else:
            self.positions.append(Position(
                ticker=ticker, name=name, market=market,
                shares=shares, entry_price=price,
                entry_date=date.today().isoformat(),
                signal_score=signal_score,
            ))

        self._set_cash(market, cash - cost)
        self.trades.append(TradeRecord(
            ticker=ticker, name=name, market=market,
            action="buy", shares=shares, price=price,
            date=date.today().isoformat(), reason=reason,
            signal_score=signal_score,
        ))
        self.save()
        currency = "$" if market == "US" else "원"
        return f"{name}({ticker}) {shares}주 매수 @ {price:,.2f}{currency} (수수료 포함 {cost:,.0f}{currency})"

    def sell(self, ticker: str, shares: int | None, price: float,
             reason: str = "", commission: float = 0.0015) -> str:
        pos = self.get_position(ticker)
        if not pos:
            return f"{ticker}: 보유하고 있지 않음"

        if shares is None or shares >= pos.shares:
            shares = pos.shares

        proceeds = shares * price * (1 - commission)
        pnl_pct = (price / pos.entry_price - 1) * 100
        market = pos.market
        currency = "$" if market == "US" else "원"

        self._set_cash(market, self.get_cash(market) + proceeds)
        self.trades.append(TradeRecord(
            ticker=ticker, name=pos.name, market=market,
            action="sell", shares=shares, price=price,
            date=date.today().isoformat(), reason=reason,
            pnl_pct=round(pnl_pct, 2),
        ))

        if shares >= pos.shares:
            self.positions = [p for p in self.positions if p.ticker != ticker]
        else:
            pos.shares -= shares

        self.save()
        pnl_icon = "+" if pnl_pct > 0 else ""
        return f"{pos.name}({ticker}) {shares}주 매도 @ {price:,.2f}{currency} → {pnl_icon}{pnl_pct:.2f}%"

    def get_current_prices(self) -> dict[str, float]:
        prices = {}
        for pos in self.positions:
            try:
                if pos.market == "KR":
                    from src.data.korea import fetch_korea_stock
                    df = fetch_korea_stock(pos.ticker, days=5)
                else:
                    from src.data.us import fetch_us_stock
                    df = fetch_us_stock(pos.ticker, period="5d")
                if not df.empty:
                    prices[pos.ticker] = float(df["Close"].iloc[-1])
            except Exception:
                pass
        return prices

    def get_portfolio_summary(self) -> dict:
        prices = self.get_current_prices()

        holdings = []
        total_value_us = self.cash_us
        total_value_kr = self.cash_kr
        total_invested_us = 0.0
        total_invested_kr = 0.0

        for pos in self.positions:
            current_price = prices.get(pos.ticker, pos.entry_price)
            current_value = pos.shares * current_price
            pnl_pct = (current_price / pos.entry_price - 1) * 100
            pnl_amount = current_value - pos.entry_value

            if pos.market == "US":
                total_value_us += current_value
                total_invested_us += pos.entry_value
            else:
                total_value_kr += current_value
                total_invested_kr += pos.entry_value

            holdings.append({
                "ticker": pos.ticker,
                "name": pos.name,
                "market": pos.market,
                "shares": pos.shares,
                "entry_price": pos.entry_price,
                "current_price": current_price,
                "entry_value": pos.entry_value,
                "current_value": current_value,
                "pnl_pct": round(pnl_pct, 2),
                "pnl_amount": round(pnl_amount, 2),
                "entry_date": pos.entry_date,
            })

        us_return = (total_value_us / self.initial_capital_us - 1) * 100 if self.initial_capital_us else 0
        kr_return = (total_value_kr / self.initial_capital_kr - 1) * 100 if self.initial_capital_kr else 0

        return {
            "holdings": holdings,
            "cash_us": self.cash_us,
            "cash_kr": self.cash_kr,
            "total_value_us": total_value_us,
            "total_value_kr": total_value_kr,
            "us_return": round(us_return, 2),
            "kr_return": round(kr_return, 2),
            "total_positions": len(self.positions),
            "total_trades": len(self.trades),
            "created_at": self.created_at,
        }


def auto_trade(portfolio: PaperPortfolio | None = None, dry_run: bool = False) -> list[str]:
    """스캐너 시그널 기반 자동 모의 매매.

    - 강력매수/매수 시그널 → 매수 (자본의 10%씩)
    - 매도/강력매도 시그널이고 보유 중이면 → 매도
    """
    from src.data.sentiment import fetch_fear_greed, get_market_regime
    from src.analysis.factors import calculate_multi_factor_score
    from src.data.us import fetch_us_stock, fetch_us_info
    from src.data.korea import fetch_korea_stock

    if portfolio is None:
        portfolio = PaperPortfolio.load()

    sentiment = fetch_fear_greed()
    regime = get_market_regime()
    actions = []

    all_stocks = [(name, ticker, "US") for name, ticker in US_TOP.items()]
    all_stocks += [(name, code, "KR") for name, code in KOREA_TOP.items()]

    for name, ticker, market in all_stocks:
        try:
            if market == "US":
                price_df = fetch_us_stock(ticker, period="1y")
                try:
                    info = fetch_us_info(ticker)
                except Exception:
                    info = None
            else:
                price_df = fetch_korea_stock(ticker, days=365)
                info = None

            if price_df.empty:
                continue

            result = calculate_multi_factor_score(price_df, info, sentiment, regime)
            score = result["final_score"]
            signal = result["signal"]
            price = float(price_df["Close"].iloc[-1])

            pos = portfolio.get_position(ticker)

            if signal in ("강력 매수", "매수") and pos is None:
                cash = portfolio.get_cash(market)
                alloc = cash * 0.10
                shares = int(alloc / (price * 1.0015))
                if shares > 0:
                    if dry_run:
                        actions.append(f"[매수 예정] {name}({ticker}) {shares}주 @ {price:,.2f} (점수: {score:+.1f})")
                    else:
                        msg = portfolio.buy(ticker, name, market, shares, price,
                                            reason=f"시그널: {signal} ({score:+.1f})", signal_score=score)
                        actions.append(msg)

            elif signal in ("매도", "강력 매도") and pos is not None:
                if dry_run:
                    pnl = (price / pos.entry_price - 1) * 100
                    actions.append(f"[매도 예정] {name}({ticker}) {pos.shares}주 @ {price:,.2f} (수익: {pnl:+.1f}%)")
                else:
                    msg = portfolio.sell(ticker, None, price,
                                         reason=f"시그널: {signal} ({score:+.1f})")
                    actions.append(msg)

            elif pos is not None:
                pnl = (price / pos.entry_price - 1) * 100
                if pnl <= -7:
                    if dry_run:
                        actions.append(f"[손절 예정] {name}({ticker}) {pos.shares}주 (손실: {pnl:+.1f}%)")
                    else:
                        msg = portfolio.sell(ticker, None, price,
                                             reason=f"손절 ({pnl:+.1f}%)")
                        actions.append(msg)
                elif pnl >= 15:
                    if dry_run:
                        actions.append(f"[익절 예정] {name}({ticker}) {pos.shares}주 (수익: {pnl:+.1f}%)")
                    else:
                        msg = portfolio.sell(ticker, None, price,
                                             reason=f"익절 ({pnl:+.1f}%)")
                        actions.append(msg)

        except Exception:
            continue

    if not dry_run:
        portfolio.save()

    return actions
