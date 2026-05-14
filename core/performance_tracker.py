import numpy as np
import pandas as pd
from typing import Dict, List


class PerformanceTracker:
    @staticmethod
    def calculate_metrics(daily_pnl: List[float], trades: List[Dict], initial_capital: float) -> Dict[str, float]:
        if not daily_pnl or initial_capital <= 0:
            return {
                'net_return_pct': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown_pct': 0.0,
                'win_rate': 0.0, 'volatility': 0.0,
                'profit_factor': 0.0, 'calmar_ratio': 0.0, 'avg_trade_duration': 0.0,
            }

        pnl_series = pd.Series(daily_pnl)
        equity_curve = initial_capital + pnl_series.cumsum()

        net_return_pct = (equity_curve.iloc[-1] - initial_capital) / initial_capital

        mean_pnl = pnl_series.mean()
        std_pnl = pnl_series.std()
        sharpe_ratio = (mean_pnl / std_pnl) * np.sqrt(252) if std_pnl > 0 else 0.0

        running_max = equity_curve.cummax()
        drawdown = (running_max - equity_curve) / running_max
        max_drawdown_pct = float(drawdown.max()) if len(drawdown) > 0 else 0.0

        volatility = std_pnl / initial_capital * np.sqrt(252) if initial_capital > 0 else 0.0

        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0.0

        gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

        # Calmar ratio: annualized return / max drawdown
        annualized_return = net_return_pct * (252 / len(daily_pnl)) if daily_pnl else 0.0
        calmar_ratio = annualized_return / max_drawdown_pct if max_drawdown_pct > 0 else 0.0

        # Average trade duration in days (uses 'duration' key if present in trade dicts)
        durations = [t.get('duration', 0) for t in trades if 'duration' in t]
        avg_trade_duration = float(np.mean(durations)) if durations else 0.0

        return {
            'net_return_pct': float(net_return_pct),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown_pct': float(max_drawdown_pct),
            'win_rate': float(win_rate),
            'volatility': float(volatility),
            'profit_factor': float(profit_factor) if profit_factor != float('inf') else float('inf'),
            'calmar_ratio': float(calmar_ratio),
            'avg_trade_duration': float(avg_trade_duration),
        }

    @staticmethod
    def calculate_composite_scores(metrics_dict: Dict[str, Dict[str, float]], config) -> Dict[str, float]:
        scores = {}
        if not metrics_dict:
            return scores

        sharpes = [m.get('sharpe_ratio', 0) for m in metrics_dict.values()]
        returns = [m.get('net_return_pct', 0) for m in metrics_dict.values()]
        drawdowns = [m.get('max_drawdown_pct', 0) for m in metrics_dict.values()]

        def normalize(values):
            min_val, max_val = min(values), max(values)
            if min_val == max_val:
                return [0.5 for _ in values]
            return [(v - min_val) / (max_val - min_val) for v in values]

        norm_sharpes = normalize(sharpes)
        norm_returns = normalize(returns)
        norm_drawdowns = normalize(drawdowns)

        for idx, (name, _) in enumerate(metrics_dict.items()):
            score = (config.SHARPE_WEIGHT * norm_sharpes[idx]) + \
                    (config.RETURN_WEIGHT * norm_returns[idx]) - \
                    (config.DRAWDOWN_WEIGHT * norm_drawdowns[idx])
            scores[name] = score

        return scores
