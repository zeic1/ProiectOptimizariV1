import os
import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from loguru import logger

import config
from core.performance_tracker import PerformanceTracker

class ReportGenerator:
    def __init__(self, portfolio_manager, benchmark):
        self.portfolio_manager = portfolio_manager
        self.benchmark = benchmark

    def generate_report(self):
        logger.info("Generating reports via Plotly...")
        
        # Ensure the outputs/reports directory exists
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = os.path.join(report_dir, f"report_{timestamp}")
        
        # Generate and Save Interactive Charts
        self._plot_equity_curves(base_filename)
        self._plot_allocation_heatmap(base_filename)
        self._plot_monthly_pnl(base_filename)
        self._plot_drawdowns(base_filename)
        
        # Print Summary Console Tables
        self._print_performance_summary()
        
        logger.info(f"Reports successfully generated and saved to {report_dir}")

    def get_equity_curve_fig(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.portfolio_manager.equity_curve.index, 
                                 y=self.portfolio_manager.equity_curve.values, 
                                 mode='lines', name='AGOA Portfolio'))
        fig.add_trace(go.Scatter(x=self.benchmark.equity_curve.index, 
                                 y=self.benchmark.equity_curve.values, 
                                 mode='lines', name='1/N Benchmark'))
        fig.update_layout(title="Equity Curve: AGOA vs Benchmark", 
                          xaxis_title="Date", yaxis_title="Portfolio Value ($)")
        return fig

    def _plot_equity_curves(self, base_filename):
        fig = self.get_equity_curve_fig()
        fig.write_html(f"{base_filename}_equity.html")

    def get_allocation_heatmap_fig(self):
        history = self.portfolio_manager.allocation_history
        if not history: return go.Figure().update_layout(title="No Allocation History Available")
        
        df = pd.DataFrame(history).set_index('Date').fillna(0)
        realloc_events = df.drop_duplicates()
        
        fig = px.imshow(realloc_events.T, aspect="auto", color_continuous_scale='Viridis',
                        title="Strategy Allocation Heatmap Over Time (Reallocation Events)")
        fig.update_layout(xaxis_title="Recomputation Date", yaxis_title="Strategy")
        return fig

    def _plot_allocation_heatmap(self, base_filename):
        fig = self.get_allocation_heatmap_fig()
        fig.write_html(f"{base_filename}_allocations.html")

    def get_monthly_pnl_fig(self):
        if self.portfolio_manager.equity_curve.empty:
            return go.Figure().update_layout(title="No P&L Data Available")
        
        pm_dates = self.portfolio_manager.equity_curve.index
        pm_pnl = pd.Series(self.portfolio_manager.daily_pnl, index=pm_dates)
        bm_pnl = pd.Series(self.benchmark.daily_pnl, index=self.benchmark.equity_curve.index)
        
        pm_monthly = pm_pnl.resample('ME').sum()
        bm_monthly = bm_pnl.resample('ME').sum()
        
        months = pm_monthly.index.strftime('%Y-%m')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=months, y=pm_monthly.values, name='AGOA Portfolio'))
        fig.add_trace(go.Bar(x=months, y=bm_monthly.values, name='1/N Benchmark'))
        fig.update_layout(title="Monthly P&L Breakdown", xaxis_title="Month", 
                          yaxis_title="PnL ($)", barmode='group')
        return fig

    def _plot_monthly_pnl(self, base_filename):
        fig = self.get_monthly_pnl_fig()
        fig.write_html(f"{base_filename}_monthly_pnl.html")

    def get_drawdown_fig(self):
        pm_eq = self.portfolio_manager.equity_curve
        bm_eq = self.benchmark.equity_curve
        
        if pm_eq.empty or bm_eq.empty:
            return go.Figure().update_layout(title="No Equity Data for Drawdown Calculation")
        
        pm_dd = (pm_eq - pm_eq.cummax()) / pm_eq.cummax()
        bm_dd = (bm_eq - bm_eq.cummax()) / bm_eq.cummax()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=pm_dd.index, y=pm_dd.values, mode='lines', name='AGOA Drawdown', fill='tozeroy'))
        fig.add_trace(go.Scatter(x=bm_dd.index, y=bm_dd.values, mode='lines', name='Benchmark Drawdown', fill='tozeroy'))
        fig.update_layout(title="Rolling Max Drawdown", xaxis_title="Date", 
                          yaxis_title="Drawdown (%)", yaxis_tickformat='.2%')
        return fig

    def _plot_drawdowns(self, base_filename):
        fig = self.get_drawdown_fig()
        fig.write_html(f"{base_filename}_drawdown.html")

    def _print_performance_summary(self):
        pm_metrics = self.portfolio_manager.get_metrics()
        bm_metrics = self.benchmark.get_metrics()
        
        logger.info("="*65)
        logger.info("                 === 6-MONTH PERFORMANCE SUMMARY ===")
        logger.info("="*65)
        logger.info(f"AGOA Final Return:      {pm_metrics.get('net_return_pct', 0)*100:6.2f}%")
        logger.info(f"1/N Benchmark Return:   {bm_metrics.get('net_return_pct', 0)*100:6.2f}%")
        logger.info(f"AGOA Sharpe:            {pm_metrics.get('sharpe_ratio', 0):6.2f}  |  Benchmark Sharpe:   {bm_metrics.get('sharpe_ratio', 0):6.2f}")
        logger.info(f"AGOA Max DD:            {pm_metrics.get('max_drawdown_pct', 0)*100:6.2f}%  |  Benchmark Max DD:   {bm_metrics.get('max_drawdown_pct', 0)*100:6.2f}%")
        logger.info(f"AGOA Win Rate:          {pm_metrics.get('win_rate', 0)*100:6.2f}%  |  Benchmark Win Rate: {bm_metrics.get('win_rate', 0)*100:6.2f}%")
        
        logger.info("-" * 65)
        logger.info("PER-STRATEGY FINAL METRICS (Measured via 1/N Continuous Benchmark)")
        for name, strat in self.benchmark.strategies.items():
            sm = PerformanceTracker.calculate_metrics(strat.daily_pnl, strat.trades, strat.initial_capital)
            logger.info(f"{name.ljust(28)} | Ret: {sm.get('net_return_pct', 0)*100:6.2f}% | "
                        f"Sharpe: {sm.get('sharpe_ratio', 0):5.2f} | "
                        f"DD: {sm.get('max_drawdown_pct', 0)*100:5.2f}% | "
                        f"Win: {sm.get('win_rate', 0)*100:5.2f}%")
                        
        history = self.portfolio_manager.allocation_history
        if history:
            df = pd.DataFrame(history).set_index('Date').fillna(0)
            realloc_events = df.drop_duplicates()
            tier_counts = {name: {'Elite': 0, 'Core': 0, 'Survival': 0} for name in self.benchmark.strategies.keys()}
            
            for _, row in realloc_events.iterrows():
                sorted_strats = row.sort_values(ascending=False)
                elite_count = max(1, int(len(sorted_strats) * config.ELITE_THRESHOLD))
                survival_count = max(1, int(len(sorted_strats) * config.SURVIVAL_THRESHOLD))
                for i, strat in enumerate(sorted_strats.index):
                    if i < elite_count: tier_counts[strat]['Elite'] += 1
                    elif i >= len(sorted_strats) - survival_count: tier_counts[strat]['Survival'] += 1
                    else: tier_counts[strat]['Core'] += 1
            
            logger.info("-" * 65)
            logger.info("TIER HISTORY (Rank Classification per Reallocation Event)")
            for name, counts in tier_counts.items():
                logger.info(f"{name.ljust(28)} | Elite: {counts['Elite']:2d} | "
                            f"Core: {counts['Core']:2d} | Survival: {counts['Survival']:2d}")
        logger.info("="*65)