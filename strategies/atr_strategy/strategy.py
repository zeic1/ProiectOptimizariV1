import pandas as pd
import ta
from typing import Dict
from strategies.base_strategy import BaseStrategy

class ATRStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 14:
                signals[ticker] = 0
                continue
            atr = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range()
            sma = ta.trend.SMAIndicator(close=df['Close'], window=14).sma_indicator()
            sig = pd.Series(0, index=df.index)
            sig.loc[df['Close'] > sma + atr] = 1
            sig.loc[df['Close'] < sma] = -1
            signals[ticker] = sig
        return signals.fillna(0)