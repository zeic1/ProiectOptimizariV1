import pandas as pd
from loguru import logger
from typing import Dict

import config
from core.portfolio_manager import PortfolioManager
from core.benchmark import Benchmark
from core.agoa_engine import AGOAEngine
from core.performance_tracker import PerformanceTracker

class SimulationRunner:
    """
    Orchestrates the backtest over the configured date range.
    Advances time day by day, passing data to strategies, and triggers AGOA reallocations.
    """
    def __init__(self, 
                 portfolio_manager: PortfolioManager, 
                 benchmark: Benchmark, 
                 agoa_engine: AGOAEngine, 
                 data: Dict[str, pd.DataFrame]):
        self.portfolio_manager = portfolio_manager
        self.benchmark = benchmark
        self.agoa_engine = agoa_engine
        self.data = data

    def run(self, on_progress=None):
        # Gather and sort all unique trading dates across all assets in the specified window
        all_dates = set()
        for ticker, df in self.data.items():
            mask = (df.index.date >= config.SIMULATION_START_DATE) & (df.index.date <= config.SIMULATION_END_DATE)
            all_dates.update(df[mask].index.tolist())

        dates_to_run = sorted(list(all_dates))

        if not dates_to_run:
            logger.error("No dates found in data for the given simulation window.")
            return

        logger.info(f"Starting simulation from {dates_to_run[0].date()} to {dates_to_run[-1].date()}")
        total = len(dates_to_run)

        for i, date in enumerate(dates_to_run):
            self.benchmark.run_day(date, self.data)
            self.portfolio_manager.run_day(date, self.data)

            day_name = date.strftime("%A")
            if day_name in config.RECOMPUTE_DAYS:
                self._recompute_and_reallocate(date)

            if on_progress and i % 5 == 0:
                on_progress(i + 1, total)

        if on_progress:
            on_progress(total, total)
        logger.info("Simulation completed.")

    def _recompute_and_reallocate(self, current_date: pd.Timestamp):
        logger.info(f"--- Recomputation Event: {current_date.date()} ({current_date.strftime('%A')}) ---")
        
        current_vix = None
        vix_df = self.data.get('^VIX', self.data.get('_VIX'))
        if vix_df is not None and current_date in vix_df.index:
            current_vix = vix_df.loc[current_date, 'Close']
            
        lookback_weeks = config.LOOKBACK_WEEKS
        
        # OVERRIDE: Adaptive Lookback for high volatility
        if config.ENABLE_ADAPTIVE_LOOKBACK and vix_df is not None and current_vix is not None:
            past_vix = vix_df.loc[:current_date, 'Close']
            if len(past_vix) >= 90:
                vix_90d = past_vix.tail(90).mean()
                if current_vix > 1.5 * vix_90d:
                    logger.info(f"Adaptive Lookback: VIX ({current_vix:.2f}) > 1.5x 90d avg ({vix_90d:.2f}). Extending lookback to 5 weeks.")
                    lookback_weeks = 5

        lookback_days = lookback_weeks * 5  # roughly 5 trading days per week
        metrics_dict, win_rate_dict, trade_count_dict, momentum_5d_dict = {}, {}, {}, {}
        pnl_df = pd.DataFrame()
        
        # Gather unbroken metrics using the Benchmark's 1/N equal-weighted strategy instances
        for name, strat in self.benchmark.strategies.items():
            full_pnl = strat.daily_pnl
            pnl_slice = full_pnl[-lookback_days:] if len(full_pnl) >= lookback_days else full_pnl
            
            dummy_trades = [{'dummy': 1}] if len(pnl_slice) > 0 else [] 
            metrics = PerformanceTracker.calculate_metrics(pnl_slice, dummy_trades, strat.initial_capital)
            
            metrics_dict[name] = metrics
            win_rate_dict[name] = metrics.get('win_rate', 0.0)
            trade_count_dict[name] = len([p for p in pnl_slice if p != 0]) # proxy for active trading days
            momentum_5d_dict[name] = sum(full_pnl[-5:]) / strat.initial_capital if len(full_pnl) >= 5 and strat.initial_capital > 0 else 0.0
            pnl_df[name] = [0.0] * (lookback_days - len(pnl_slice)) + pnl_slice # Pad for corr matrix
            
        composite_scores = PerformanceTracker.calculate_composite_scores(metrics_dict, config)
        new_allocations = self.agoa_engine.allocate(metrics_dict, composite_scores, self.portfolio_manager.current_capital, current_vix, pnl_df.corr(), momentum_5d_dict, win_rate_dict, trade_count_dict)
        
        if new_allocations: self.portfolio_manager.reallocate(new_allocations)