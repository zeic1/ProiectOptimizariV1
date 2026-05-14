import pandas as pd
from typing import Dict
from strategies.base_strategy import BaseStrategy

class BreakoutStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        window = 20
        for ticker, df in data.items():
            if len(df) < window:
                signals[ticker] = 0
                continue
            rolling_high = df['High'].shift(1).rolling(window=window).max()
            sig = pd.Series(0, index=df.index)
            sig.loc[df['Close'] > rolling_high] = 1
            sig.loc[df['Close'] < df['Close'].rolling(window=10).mean()] = -1
            signals[ticker] = sig
        return signals.fillna(0)
