import pandas as pd
from typing import Dict
from strategies.base_strategy import BaseStrategy

class GapFadeStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 2:
                signals[ticker] = 0
                continue
            gap = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)
            sig = pd.Series(0, index=df.index)
            sig.loc[gap > 0.02] = -1 
            sig.loc[gap < -0.02] = 1  
            signals[ticker] = sig
        return signals.fillna(0)