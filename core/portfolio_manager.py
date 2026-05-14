import pandas as pd
from typing import Dict, List
from loguru import logger

from strategies.base_strategy import BaseStrategy

class PortfolioManager:
    """
    Manages the collection of strategies, tracks overall portfolio capital,
    and orchestrates reallocations based on AGOA Engine decisions.
    """
    def __init__(self, strategies: Dict[str, BaseStrategy], initial_capital: float):
        self.strategies = strategies
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        self.allocations: Dict[str, float] = {}
        self.equity_curve = pd.Series(dtype=float)
        self.daily_pnl = []
        self.all_trades = []
        self.allocation_history = []

    def reallocate(self, new_allocations: Dict[str, float]):
        """
        Updates the capital allocation for each strategy.
        This effectively resets the 'initial_capital' for each strategy's
        internal P&L calculations until the next reallocation.
        """
        logger.info(f"Reallocating portfolio. New allocations: {new_allocations}")
        self.allocations = new_allocations
        for name, strategy in self.strategies.items():
            allocated_capital = self.allocations.get(name, 0.0)
            strategy.initial_capital = allocated_capital
            strategy.current_capital = allocated_capital
            # Resetting PnL history for the next evaluation window
            strategy.daily_pnl = []
            strategy.trades = []

    def run_day(self, date: pd.Timestamp, data: Dict[str, pd.DataFrame]):
        """
        Runs all strategies for a single day and aggregates the results.
        """
        total_day_pnl = 0.0
        
        for name, strategy in self.strategies.items():
            # Only run the strategy if it has capital allocated
            if self.allocations.get(name, 0.0) > 0:
                result = strategy.run_day(date, data)
                total_day_pnl += result.get('daily_pnl', 0.0)
                if result.get('trades'):
                    self.all_trades.extend(result['trades'])
        
        self.current_capital += total_day_pnl
        self.daily_pnl.append(total_day_pnl)
        
        # Use .loc for safe assignment, even if date is not in index yet
        self.equity_curve.loc[date] = self.current_capital
        
        # Record allocation history for reporting
        alloc_record = {'Date': date}
        alloc_record.update(self.allocations)
        self.allocation_history.append(alloc_record)

    def get_metrics(self) -> Dict[str, float]:
        """
        Calculates and returns the final performance metrics for the entire portfolio.
        """
        try:
            from core.performance_tracker import PerformanceTracker
        except ImportError:
            from performance_tracker import PerformanceTracker
            
        return PerformanceTracker.calculate_metrics(self.daily_pnl, self.all_trades, self.initial_capital)