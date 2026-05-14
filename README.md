# AGOA Portfolio Manager

An **Adaptive Genetic Optimization Algorithm (AGOA)** that dynamically allocates capital across 10 day-trading strategies. The system simulates a 6-month period on historical market data, recomputes allocations twice a week (Wednesday and Friday), and benchmarks results against an equal-weight 1/N portfolio.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Run Simulation

```bash
python main.py
```

Reports are saved to `outputs/reports/` and logs to `outputs/logs/`.

## Configuration

Edit `config.py` to adjust:
- `INITIAL_CAPITAL` — starting capital (default: $100,000)
- `SIMULATION_START_DATE` / `SIMULATION_END_DATE` — date range (default: last 6 months)
- `ELITE_ALLOCATION`, `CORE_ALLOCATION`, `SURVIVAL_ALLOCATION` — tier capital splits
- `SHARPE_WEIGHT`, `RETURN_WEIGHT`, `DRAWDOWN_WEIGHT` — composite score weights
- `ENABLE_*` flags — toggle dynamic risk overlays (VIX filter, correlation penalty, etc.)

## Project Structure

```
agoa_portfolio_manager/
├── main.py                  # Entry point
├── config.py                # Global configuration
├── core/                    # AGOA engine, simulation, reporting
├── data/                    # Data loading (yfinance) and ticker universes
├── strategies/              # 10 trading strategies inheriting BaseStrategy
├── live/                    # Paper trading and broker adapter stubs
├── tests/                   # pytest test suite
└── outputs/                 # Generated reports and logs
```

## Strategies

| Strategy | Asset Universe |
|---|---|
| ATR | NVDA, AMD, TSLA |
| RSI | AAPL, MSFT, AMZN |
| Breakout | SMCI, MSTR |
| Dynamic Stop Loss | SPY, QQQ, IWM |
| MACD Crossover | XLF, XLE, XLK |
| Bollinger Bands | JPM, BAC, GS |
| VWAP | SPY, AAPL, TSLA |
| Mean Reversion | GLD, SLV, XOM, CVX |
| Momentum | META, GOOGL, NFLX |
| Gap Fade | Pre-market gapped stocks |

## Run Tests

```bash
pytest tests/ -v
```
