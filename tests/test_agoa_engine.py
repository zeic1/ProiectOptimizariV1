import pytest
import pandas as pd
from core.agoa_engine import AGOAEngine
import config

@pytest.fixture
def patched_config(monkeypatch):
    monkeypatch.setattr(config, "ELITE_THRESHOLD", 0.10)
    monkeypatch.setattr(config, "SURVIVAL_THRESHOLD", 0.10)
    monkeypatch.setattr(config, "ELITE_ALLOCATION", 0.50)
    monkeypatch.setattr(config, "CORE_ALLOCATION", 0.40)
    monkeypatch.setattr(config, "SURVIVAL_ALLOCATION", 0.10)
    monkeypatch.setattr(config, "MAX_SINGLE_STRATEGY_ALLOCATION", 1.0)
    monkeypatch.setattr(config, "MIN_SINGLE_STRATEGY_ALLOCATION", 0.0)
    monkeypatch.setattr(config, "ENABLE_DRAWDOWN_CIRCUIT_BREAKER", False)
    monkeypatch.setattr(config, "ENABLE_WIN_RATE_FLOOR", False)
    monkeypatch.setattr(config, "ENABLE_TRADE_FREQUENCY_NORMALIZER", False)
    monkeypatch.setattr(config, "ENABLE_CORRELATION_PENALTY", False)
    monkeypatch.setattr(config, "ENABLE_VOLATILITY_REGIME_FILTER", False)
    monkeypatch.setattr(config, "ENABLE_MOMENTUM_BOOST", False)
    monkeypatch.setattr(config, "ENABLE_SECTOR_CONCENTRATION_CAP", False)

def test_agoa_tier_allocations(patched_config):
    engine = AGOAEngine()

    # 10 strategies with scores 0.0 to 0.9
    composite_scores = {f"strat_{i}": i / 10.0 for i in range(10)}
    metrics_dict = {f"strat_{i}": {} for i in range(10)}

    allocs = engine.allocate(
        metrics_dict=metrics_dict,
        composite_scores=composite_scores,
        total_capital=1000.0,
        current_vix=15.0,
        correlation_matrix=pd.DataFrame(),
        momentum_5d={},
        win_rates={},
        trade_counts={}
    )

    # Top 1 = Elite (50% of 1000 = 500)
    assert allocs["strat_9"] == pytest.approx(500.0)
    # Middle 7 = Core (40% of 1000 = 400)
    assert sum(allocs[f"strat_{i}"] for i in range(2, 9)) == pytest.approx(400.0)
    # Bottom 2 = Survival (10% of 1000 = 100)
    assert sum(allocs[f"strat_{i}"] for i in range(2)) == pytest.approx(100.0)

def test_agoa_circuit_breaker(patched_config, monkeypatch):
    monkeypatch.setattr(config, "ENABLE_DRAWDOWN_CIRCUIT_BREAKER", True)
    engine = AGOAEngine()

    # Give strat_0 a very high score but a terrible drawdown
    composite_scores = {"strat_0": 0.9, "strat_1": 0.5, "strat_2": 0.2}
    metrics_dict = {
        "strat_0": {'max_drawdown_pct': 0.25},  # > 20% trigger
        "strat_1": {'max_drawdown_pct': 0.05},
        "strat_2": {'max_drawdown_pct': 0.05}
    }

    allocs = engine.allocate(
        metrics_dict=metrics_dict,
        composite_scores=composite_scores,
        total_capital=1000.0,
        current_vix=15.0,
        correlation_matrix=pd.DataFrame(),
        momentum_5d={},
        win_rates={},
        trade_counts={}
    )

    # strat_1 should be promoted to Elite because strat_0 was demoted to Survival
    assert allocs["strat_1"] == pytest.approx(500.0)  # Elite
    assert "strat_0" in allocs  # It is still allocated, but heavily penalized
