from schema import StockSnapshot


def build_empty_snapshot(ticker: str) -> StockSnapshot:
    return {
        "ticker": ticker.upper(),
        "company_name": ticker.upper(),
        "price": 0.0,
        "change_pct": 0.0,
        "volume": None,
        "trend_state": "neutral",
        "momentum_state": "mixed",
        "fundamentals": {},
        "news": [],
        "explanation_inputs": [],
    }