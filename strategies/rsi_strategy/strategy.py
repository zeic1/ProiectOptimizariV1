import pandas as pd
import ta
from typing import Dict
from strategies.base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 14:
                signals[ticker] = 0
                continue
            rsi = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
            sig = pd.Series(0, index=df.index)
            sig.loc[rsi < 30] = 1
            sig.loc[rsi > 70] = -1
            signals[ticker] = sig
        return signals.fillna(0)