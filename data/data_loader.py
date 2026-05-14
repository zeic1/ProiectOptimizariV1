import os
import pandas as pd
import yfinance as yf
from loguru import logger
import datetime
from typing import Dict, List

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

class DataLoader:
    """
    Handles downloading and caching of OHLCV data from Yahoo Finance.
    """
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def load_data(self, tickers: List[str], start_date: datetime.date, end_date: datetime.date, timeframe: str = "1d") -> Dict[str, pd.DataFrame]:
        data_dict = {}
        
        for ticker in tickers:
            # Create a safe filename (e.g., ^VIX to _VIX) to avoid filesystem issues
            safe_ticker = ticker.replace("^", "_")
            cache_file = os.path.join(CACHE_DIR, f"{safe_ticker}_{timeframe}_{start_date}_{end_date}.csv")
            
            if self.use_cache and os.path.exists(cache_file):
                logger.info(f"Loading {ticker} data from cache...")
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                data_dict[ticker] = df
            else:
                logger.info(f"Downloading {ticker} data from yfinance...")
                try:
                    df = yf.download(ticker, start=start_date, end=end_date, interval=timeframe, progress=False)
                    if not df.empty:
                        # Flatten columns if yfinance returns a MultiIndex (common in newer yfinance versions)
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = [col[0] for col in df.columns]
                        
                        df.index.name = "Date"
                        
                        if self.use_cache:
                            df.to_csv(cache_file)
                        data_dict[ticker] = df
                    else:
                        logger.warning(f"No data found for {ticker}")
                except Exception as e:
                    logger.error(f"Failed to download {ticker}: {e}")
                    
        return data_dict