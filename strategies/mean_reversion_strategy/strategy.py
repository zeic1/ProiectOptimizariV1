import pandas as pd
from typing import Dict
from strategies.base_strategy import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 20:
                signals[ticker] = 0
                continue
            sma = df['Close'].rolling(window=20).mean()
            std = df['Close'].rolling(window=20).std()
            z_score = (df['Close'] - sma) / std
            sig = pd.Series(0, index=df.index)
            sig.loc[z_score < -2] = 1
            sig.loc[z_score > 2] = -1
            signals[ticker] = sig
        return signals.fillna(0)