import pandas as pd
import ta
from typing import Dict
from strategies.base_strategy import BaseStrategy

class VWAPStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 14:
                signals[ticker] = 0
                continue
            vwap = ta.volume.VolumeWeightedAveragePrice(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume']).volume_weighted_average_price()
            sig = pd.Series(0, index=df.index)
            sig.loc[(df['Close'] > vwap) & (df['Close'].shift(1) <= vwap.shift(1))] = 1
            sig.loc[(df['Close'] < vwap) & (df['Close'].shift(1) >= vwap.shift(1))] = -1
            signals[ticker] = sig
        return signals.fillna(0)
