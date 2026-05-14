import pandas as pd
from typing import Dict
from strategies.base_strategy import BaseStrategy

class MomentumStrategy(BaseStrategy):
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        signals = pd.DataFrame()
        for ticker, df in data.items():
            if len(df) < 10:
                signals[ticker] = 0
                continue
            roc = df['Close'].pct_change(periods=10)
            sig = pd.Series(0, index=df.index)
            sig.loc[roc > 0.05] = 1
            sig.loc[roc < -0.05] = -1
            signals[ticker] = sig
        return signals.fillna(0)