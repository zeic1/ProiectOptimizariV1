import pandas as pd
from typing import Dict, List
from loguru import logger

from strategies.base_strategy import BaseStrategy

class Benchmark:
    """
    Simulates a 1/N (equal weight) portfolio with no rebalancing.
    This serves as a baseline to compare the AGOA strategy against.
    """
    def __init__(self, strategies: Dict[str, BaseStrategy], initial_capital: float):
        self.strategies = strategies
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        self.equity_curve = pd.Series(dtype=float)
        self.daily_pnl = []
        self.all_trades = []

        # Set up the initial 1/N allocation
        num_strategies = len(self.strategies)
        if num_strategies > 0:
            equal_allocation = self.initial_capital / num_strategies
            logger.info(f"Benchmark: Allocating {equal_allocation:.2f} to each of {num_strategies} strategies.")
            for name, strategy in self.strategies.items():
                strategy.initial_capital = equal_allocation
                strategy.current_capital = equal_allocation
                strategy.reset() # Ensure clean state

    def run_day(self, date: pd.Timestamp, data: Dict[str, pd.DataFrame]):
        """
        Runs all strategies for a single day and aggregates the P&L.
        """
        total_day_pnl = 0.0
        
        for strategy in self.strategies.values():
            result = strategy.run_day(date, data)
            total_day_pnl += result.get('daily_pnl', 0.0)
            if result.get('trades'):
                self.all_trades.extend(result['trades'])
            
        self.current_capital += total_day_pnl
        self.daily_pnl.append(total_day_pnl)
        self.equity_curve.loc[date] = self.current_capital

    def get_equity_curve(self) -> pd.Series:
        """Returns the benchmark's equity curve."""
        return self.equity_curve

    def get_metrics(self) -> Dict[str, float]:
        """
        Calculates and returns the performance metrics for the benchmark portfolio.
        """
        try:
            from core.performance_tracker import PerformanceTracker
        except ImportError:
            from performance_tracker import PerformanceTracker
            
        return PerformanceTracker.calculate_metrics(self.daily_pnl, self.all_trades, self.initial_capital)