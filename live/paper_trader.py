from loguru import logger
from live.broker_adapter import DummyBroker


class PaperTrader:
    """
    Paper trading stub. Wires the AGOA portfolio manager to a DummyBroker
    for live-mode simulation without real money. Ready for broker API wiring.
    """
    def __init__(self, portfolio_manager, initial_capital: float = 100000.0):
        self.portfolio_manager = portfolio_manager
        self.broker = DummyBroker(initial_capital)

    def run_cycle(self, date, data: dict):
        self.portfolio_manager.run_day(date, data)
        allocations = {name: strat.current_capital for name, strat in self.portfolio_manager.strategies.items()}
        for ticker, amount in allocations.items():
            price = self.broker.get_current_price(ticker)
            if price > 0:
                qty = amount / price
                self.broker.execute_order(ticker, "BUY", qty)
        logger.info(f"[PaperTrader] Cycle complete for {date}")
