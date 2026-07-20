def should_promote(champion_mape: float, challenger_mape: float, margin_pct: float) -> bool:
    """Challenger must beat champion by at least margin_pct relative improvement."""
    return challenger_mape <= champion_mape * (1 - margin_pct)
