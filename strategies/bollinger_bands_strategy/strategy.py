import pandas as pd
import ta
from typing import Dict
from strategies.base_strategy import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 20:
                signals[ticker] = 0
                continue
            bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
            sig = pd.Series(0, index=df.index)
            sig.loc[df['Close'] < bb.bollinger_lband()] = 1
            sig.loc[df['Close'] > bb.bollinger_hband()] = -1
            signals[ticker] = sig
        return signals.fillna(0)