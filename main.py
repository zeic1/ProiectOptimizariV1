import os
import sys
import datetime
from loguru import logger

# Ensure imports work correctly when running from the root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data.data_loader import DataLoader
from data.universe import get_all_tickers, STRATEGY_UNIVERSES

from strategies.atr_strategy.strategy import ATRStrategy
from strategies.rsi_strategy.strategy import RSIStrategy
from strategies.breakout_strategy.strategy import BreakoutStrategy
from strategies.dynamic_stop_loss_strategy.strategy import DynamicStopLossStrategy
from strategies.macd_crossover_strategy.strategy import MACDCrossoverStrategy
from strategies.bollinger_bands_strategy.strategy import BollingerBandsStrategy
from strategies.vwap_strategy.strategy import VWAPStrategy
from strategies.mean_reversion_strategy.strategy import MeanReversionStrategy
from strategies.momentum_strategy.strategy import MomentumStrategy
from strategies.gap_fade_strategy.strategy import GapFadeStrategy

from core.portfolio_manager import PortfolioManager
from core.benchmark import Benchmark
from core.agoa_engine import AGOAEngine
from core.simulation_runner import SimulationRunner
from core.report_generator import ReportGenerator

def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"simulation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logger.add(log_file, rotation="10 MB", level="INFO")
    logger.info("Logging initialized.")

def instantiate_strategies(initial_capital: float):
    return {
        "atr_strategy": ATRStrategy("atr_strategy", STRATEGY_UNIVERSES["atr_strategy"], initial_capital),
        "rsi_strategy": RSIStrategy("rsi_strategy", STRATEGY_UNIVERSES["rsi_strategy"], initial_capital),
        "breakout_strategy": BreakoutStrategy("breakout_strategy", STRATEGY_UNIVERSES["breakout_strategy"], initial_capital),
        "dynamic_stop_loss_strategy": DynamicStopLossStrategy("dynamic_stop_loss_strategy", STRATEGY_UNIVERSES["dynamic_stop_loss_strategy"], initial_capital),
        "macd_crossover_strategy": MACDCrossoverStrategy("macd_crossover_strategy", STRATEGY_UNIVERSES["macd_crossover_strategy"], initial_capital),
        "bollinger_bands_strategy": BollingerBandsStrategy("bollinger_bands_strategy", STRATEGY_UNIVERSES["bollinger_bands_strategy"], initial_capital),
        "vwap_strategy": VWAPStrategy("vwap_strategy", STRATEGY_UNIVERSES["vwap_strategy"], initial_capital),
        "mean_reversion_strategy": MeanReversionStrategy("mean_reversion_strategy", STRATEGY_UNIVERSES["mean_reversion_strategy"], initial_capital),
        "momentum_strategy": MomentumStrategy("momentum_strategy", STRATEGY_UNIVERSES["momentum_strategy"], initial_capital),
        "gap_fade_strategy": GapFadeStrategy("gap_fade_strategy", STRATEGY_UNIVERSES["gap_fade_strategy"], initial_capital)
    }

def run_full_simulation(start_date: datetime.date, end_date: datetime.date, progress_callback=None):
    """
    Encapsulates the entire simulation process.
    Returns the portfolio_manager and benchmark objects for analysis.
    progress_callback(pct: int, label: str) is called at key stages if provided.
    """
    # Set up file logging here so it works whether called from CLI or Dash background process
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"simulation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    log_sink_id = logger.add(log_file, rotation="10 MB", level="INFO")

    def _progress(pct, label):
        if progress_callback:
            progress_callback(pct, label)

    logger.info(f"--- Running Full Simulation: {start_date} to {end_date} ---")
    _progress(5, "Downloading market data...")

    # 1. Load Data
    tickers = get_all_tickers()
    data_loader = DataLoader(use_cache=True)

    # Pad the start date by 90 days to warm up indicators (e.g., 50-day SMA, 90-day VIX avg)
    padded_start_date = start_date - datetime.timedelta(days=90)

    logger.info(f"Loading data for {len(tickers)} tickers from {padded_start_date} to {end_date}")
    data = data_loader.load_data(tickers, padded_start_date, end_date, config.DATA_TIMEFRAME)

    if not data:
        logger.error("No data loaded. Exiting.")
        return None, None

    _progress(20, "Data loaded. Starting simulation...")

    # 2. Instantiate and Setup Core Components
    # Temporarily override config dates for this specific run
    original_start, original_end = config.SIMULATION_START_DATE, config.SIMULATION_END_DATE
    config.SIMULATION_START_DATE = start_date
    config.SIMULATION_END_DATE = end_date

    portfolio_manager = PortfolioManager(instantiate_strategies(0.0), config.INITIAL_CAPITAL)
    benchmark = Benchmark(instantiate_strategies(0.0), config.INITIAL_CAPITAL)

    # 3. Run Simulation — map per-day progress into the 20–88% band
    def _sim_day_progress(current, total):
        pct = 20 + int((current / total) * 68) if total > 0 else 88
        _progress(pct, f"Simulating day {current} of {total}...")

    SimulationRunner(portfolio_manager, benchmark, AGOAEngine(), data).run(on_progress=_sim_day_progress)

    # Restore original config dates
    config.SIMULATION_START_DATE, config.SIMULATION_END_DATE = original_start, original_end

    _progress(90, "Simulation complete. Building charts...")
    logger.remove(log_sink_id)
    return portfolio_manager, benchmark

def main():
    setup_logging()
    logger.info("Starting AGOA Portfolio Manager Simulation from command line")
    pm, bm = run_full_simulation(config.SIMULATION_START_DATE, config.SIMULATION_END_DATE)
    
    if pm and bm:
        ReportGenerator(pm, bm).generate_report()
        logger.info("Command-line simulation and reporting finished successfully.")

if __name__ == "__main__":
    main()