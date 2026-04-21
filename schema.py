from typing import TypedDict, NotRequired, Literal


TrendState = Literal["bullish", "neutral", "bearish"]
MomentumState = Literal["strong", "mixed", "weak"]


class Fundamentals(TypedDict, total=False):
    market_cap: float | None
    pe_ratio: float | None
    revenue_growth: float | None
    profit_margin: float | None


class NewsItem(TypedDict, total=False):
    headline: str
    summary: str
    sentiment: str
    source: str
    published_at: str


class StockSnapshot(TypedDict):
    ticker: str
    company_name: str
    price: float
    change_pct: float
    volume: int | None
    trend_state: TrendState
    momentum_state: MomentumState
    fundamentals: Fundamentals
    news: list[NewsItem]
    explanation_inputs: list[str]