import pandas as pd
from typing import Dict
from strategies.base_strategy import BaseStrategy

class DynamicStopLossStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 20:
                signals[ticker] = 0
                continue
            sma = df['Close'].rolling(window=20).mean()
            trailing_stop = df['Close'].rolling(window=10).max() * 0.95
            sig = pd.Series(0, index=df.index)
            sig.loc[(df['Close'] > sma) & (df['Close'].shift(1) <= sma.shift(1))] = 1
            sig.loc[df['Close'] < trailing_stop] = -1
            signals[ticker] = sig
        return signals.fillna(0)
