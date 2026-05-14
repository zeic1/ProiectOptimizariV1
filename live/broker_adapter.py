from abc import ABC, abstractmethod
from typing import Dict
from loguru import logger

class BrokerAdapter(ABC):
    """
    Abstract interface for live broker integrations (e.g., Alpaca, IBKR).
    """
    @abstractmethod
    def get_account_capital(self) -> float:
        pass

    @abstractmethod
    def get_current_price(self, ticker: str) -> float:
        pass

    @abstractmethod
    def execute_order(self, ticker: str, action: str, quantity: float):
        pass

    @abstractmethod
    def get_positions(self) -> Dict[str, float]:
        pass


class DummyBroker(BrokerAdapter):
    """
    A mock broker for Paper Trading simulations.
    """
    def __init__(self, initial_capital: float = 100000.0):
        self.capital = initial_capital
        self.positions = {}

    def get_account_capital(self) -> float:
        return self.capital

    def get_current_price(self, ticker: str) -> float:
        return 100.0  # Stub price

    def execute_order(self, ticker: str, action: str, quantity: float):
        logger.info(f"[PAPER BROKER] EXECUTING {action} for {quantity:.4f} shares of {ticker}")

    def get_positions(self) -> Dict[str, float]:
        return self.positions


class AlpacaBroker(BrokerAdapter):
    """
    Alpaca API implementation of the BrokerAdapter.
    Requires: pip install alpaca-trade-api
    """
    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        try:
            import alpaca_trade_api as tradeapi
        except ImportError:
            raise ImportError("Please install alpaca-trade-api via 'pip install alpaca-trade-api'")

        base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
        logger.info(f"Connected to Alpaca {'Paper' if paper else 'Live'} API")

    def get_account_capital(self) -> float:
        account = self.api.get_account()
        return float(account.equity)

    def get_current_price(self, ticker: str) -> float:
        try:
            trade = self.api.get_latest_trade(ticker)
            return float(trade.price)
        except Exception as e:
            logger.error(f"Failed to get price for {ticker}: {e}")
            return 0.0

    def execute_order(self, ticker: str, action: str, quantity: float):
        try:
            side = 'buy' if action.upper() == 'BUY' else 'sell'
            self.api.submit_order(
                symbol=ticker,
                qty=quantity,
                side=side,
                type='market',
                time_in_force='day'
            )
            logger.info(f"[ALPACA] EXECUTED {action} for {quantity:.4f} shares of {ticker}")
        except Exception as e:
            logger.error(f"[ALPACA] Order execution failed for {ticker}: {e}")

    def get_positions(self) -> Dict[str, float]:
        positions = self.api.list_positions()
        return {p.symbol: float(p.qty) for p in positions}
