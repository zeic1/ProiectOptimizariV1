STRATEGY_UNIVERSES = {
    "atr_strategy": ["NVDA", "AMD", "TSLA"],
    "rsi_strategy": ["AAPL", "MSFT", "AMZN"],
    "breakout_strategy": ["SMCI", "MSTR"],
    "dynamic_stop_loss_strategy": ["SPY", "QQQ", "IWM"],
    "macd_crossover_strategy": ["XLF", "XLE", "XLK"],
    "bollinger_bands_strategy": ["JPM", "BAC", "GS"],
    "vwap_strategy": ["SPY", "AAPL", "TSLA"],
    "mean_reversion_strategy": ["GLD", "SLV", "XOM", "CVX"],
    "momentum_strategy": ["META", "GOOGL", "NFLX"],
    "gap_fade_strategy": ["SPY", "QQQ"]
}

def get_all_tickers():
    tickers = set()
    for strat_tickers in STRATEGY_UNIVERSES.values():
        tickers.update(strat_tickers)
    tickers.add("^VIX")
    return list(tickers)