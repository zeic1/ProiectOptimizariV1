import pytest
import pandas as pd
import datetime
from unittest.mock import MagicMock

import config
from core.simulation_runner import SimulationRunner
from core.portfolio_manager import PortfolioManager
from core.benchmark import Benchmark
from core.agoa_engine import AGOAEngine
from strategies.base_strategy import BaseStrategy

class DummyStrategy(BaseStrategy):
    def generate_signals(self, data): return pd.DataFrame()
    def run_day(self, date, data): return {'trades': [], 'daily_pnl': 10.0, 'positions': {}}
    def get_metrics(self): return {}

@pytest.fixture
def mock_data():
    # Generate 14 days of sequential data spanning a Wednesday and a Friday
    dates = pd.date_range(start='2024-01-01', periods=14, freq='B')
    df = pd.DataFrame({'Close': [100]*14, 'Open': [100]*14, 'High': [100]*14, 'Low': [100]*14, 'Volume': [1000]*14}, index=dates)
    return {'AAPL': df}

def test_simulation_runner_smoke(mock_data, monkeypatch):
    # Narrow simulation window specifically to our mock data range
    monkeypatch.setattr(config, "SIMULATION_START_DATE", datetime.date(2024, 1, 1))
    monkeypatch.setattr(config, "SIMULATION_END_DATE", datetime.date(2024, 1, 14))

    strats_pm = {"dummy1": DummyStrategy("dummy1", ["AAPL"], 1000)}
    strats_bm = {"dummy1": DummyStrategy("dummy1", ["AAPL"], 1000)}

    pm = PortfolioManager(strats_pm, 1000.0)
    bm = Benchmark(strats_bm, 1000.0)
    agoa = AGOAEngine()

    # We mock the allocate method so we can assert it was called for Wednesday/Friday
    agoa.allocate = MagicMock(return_value={"dummy1": 1000.0})

    runner = SimulationRunner(pm, bm, agoa, mock_data)
    runner.run()

    # Over a 2-week block (10 business days), we should have run 10 times.
    assert len(pm.daily_pnl) == 10
    assert len(bm.daily_pnl) == 10

    # PM started with 1000, 10 days of +10 pnl = 1100
    assert pm.current_capital == 1100.0

    # Allocate should have been called (Wednesdays + Fridays)
    assert agoa.allocate.call_count > 0
