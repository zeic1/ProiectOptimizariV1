import pandas as pd
from typing import Dict, List

class BaseStrategy:
    def __init__(self, name: str, tickers: List[str], capital: float):
        self.name = name
        self.tickers = tickers
        self.initial_capital = capital
        
        # State machine attributes
        self.positions: Dict[str, Dict] = {}
        self.daily_pnl: List[float] = []
        self.trades: List[Dict] = []
        self._signals_cache: pd.DataFrame = None  # pre-computed once before simulation

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        raise NotImplementedError("Must implement generate_signals")

    def run_day(self, date: pd.Timestamp, data: Dict[str, pd.DataFrame]) -> dict:
        """
        Runs a full state-machine based backtest for a single day.
        - Manages positions (entry, exit, hold).
        - Calculates daily P&L from open positions.
        - Records executed trades.
        """
        day_pnl = 0.0
        day_trades = []

        # Use pre-computed signal cache; fall back to on-the-fly if not available.
        if self._signals_cache is not None:
            all_signals = self._signals_cache
        else:
            filtered = {t: df for t, df in data.items() if t in self.tickers}
            all_signals = self.generate_signals(filtered)

        # 2. First, calculate unrealized P&L for any existing open positions.
        positions_to_close_today = []
        for ticker, position in self.positions.items():
            if ticker not in data or date not in data[ticker].index:
                continue # Skip if no data for this day

            price_data = data[ticker].loc[:date]
            if len(price_data) < 2:
                continue # Not enough data to calculate P&L from previous day

            prev_close = price_data['Close'].iloc[-2]
            current_close = price_data['Close'].iloc[-1]
            
            # Add the day's P&L change to the total for the day
            pnl_change = (current_close - prev_close) * position['size'] * position['direction']
            day_pnl += pnl_change

        # 3. Now, iterate through tickers to act on signals for the current day.
        for ticker in self.tickers:
            # Ensure we have a signal and price data for the current date
            if ticker not in data or date not in all_signals.index or date not in data[ticker].index:
                continue

            signal = all_signals.loc[date, ticker]
            current_close = data[ticker].loc[date, 'Close']
            
            is_in_position = ticker in self.positions

            # Case 1: IN_POSITION - Check for an exit signal
            if is_in_position:
                position = self.positions[ticker]
                # Exit if signal is neutral (0) or reverses (-1 for long, 1 for short)
                if signal == 0 or signal == -position['direction']:
                    trade_pnl = (current_close - position['entry_price']) * position['size'] * position['direction']
                    
                    trade_record = {
                        'ticker': ticker, 'strategy': self.name, 'entry_date': position['entry_date'],
                        'exit_date': date, 'entry_price': position['entry_price'], 'exit_price': current_close,
                        'direction': 'long' if position['direction'] == 1 else 'short', 'size': position['size'], 'pnl': trade_pnl
                    }
                    day_trades.append(trade_record)
                    self.trades.append(trade_record)
                    positions_to_close_today.append(ticker)

            # Case 2: FLAT - Check for an entry signal
            else:
                if signal != 0: # Entry signal is present (1 for long, -1 for short)
                    # Simple sizing: risk 5% of this strategy's initial capital per trade
                    capital_per_trade = self.initial_capital * 0.05 
                    size = capital_per_trade / current_close
                    
                    if size > 0:
                        self.positions[ticker] = {
                            'entry_date': date, 'entry_price': current_close,
                            'size': size, 'direction': signal
                        }
        
        # Clean up any positions that were closed today
        for ticker in positions_to_close_today:
            if ticker in self.positions:
                del self.positions[ticker]

        self.daily_pnl.append(day_pnl)
        return {'trades': day_trades, 'daily_pnl': day_pnl, 'positions': self.positions}

    def get_metrics(self) -> dict:
        from core.performance_tracker import PerformanceTracker
        return PerformanceTracker.calculate_metrics(self.daily_pnl, self.trades, self.initial_capital)

    def reset(self):
        self.daily_pnl = []
        self.trades = []
        self.positions = {}
        self._signals_cache = None