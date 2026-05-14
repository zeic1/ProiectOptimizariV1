import pandas as pd
import ta
from typing import Dict
from strategies.base_strategy import BaseStrategy

class MACDCrossoverStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 26:
                signals[ticker] = 0
                continue
            macd = ta.trend.MACD(close=df['Close'])
            macd_line = macd.macd()
            signal_line = macd.macd_signal()
            sig = pd.Series(0, index=df.index)
            sig.loc[(macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))] = 1
            sig.loc[(macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))] = -1
            signals[ticker] = sig
        return signals.fillna(0)
