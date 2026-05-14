import pytest
import numpy as np
from types import SimpleNamespace
from core.performance_tracker import PerformanceTracker

def test_calculate_metrics():
    daily_pnl = [100.0, -50.0, 200.0, -100.0, 300.0]
    # 3 trades: 1 win, 1 loss, 1 dummy active day
    trades = [{'daily_pnl': 100}, {'daily_pnl': -50}, {'dummy': 1}]
    initial_capital = 1000.0

    metrics = PerformanceTracker.calculate_metrics(daily_pnl, trades, initial_capital)

    # Final PNL = 450. Return = 450 / 1000 = 0.45
    assert metrics['net_return_pct'] == pytest.approx(0.45)
    # Win rate: 2 wins / 3 trades = 66.67%
    assert metrics['win_rate'] == pytest.approx(2.0 / 3.0)
    # Max Drawdown should be tracked
    assert metrics['max_drawdown_pct'] > 0.0
    assert metrics['sharpe_ratio'] > 0.0

def test_calculate_composite_scores():
    # Mock config to control the exact weighting
    config = SimpleNamespace(
        SHARPE_WEIGHT=0.5,
        RETURN_WEIGHT=0.3,
        DRAWDOWN_WEIGHT=0.2
    )
    metrics_dict = {
        'strat1': {'sharpe_ratio': 1.5, 'net_return_pct': 0.05, 'max_drawdown_pct': 0.10}
    }

    # Sharpe normalized: 1.5 / 3.0 = 0.5. Weighted: 0.5 * 0.5 = 0.25
    # Net Ret normalized: 0.05 * 10 = 0.5. Weighted: 0.3 * 0.5 = 0.15
    # Max DD normalized: 0.10. Weighted: 0.2 * 0.10 = 0.02
    # Score: 0.25 + 0.15 - 0.02 = 0.38
    scores = PerformanceTracker.calculate_composite_scores(metrics_dict, config)
    assert np.isclose(scores['strat1'], 0.38)
