import datetime

# ==========================================
# General Simulation Configuration
# ==========================================
INITIAL_CAPITAL = 500_000.0
SIMULATION_END_DATE = datetime.date.today()
SIMULATION_START_DATE = SIMULATION_END_DATE - datetime.timedelta(days=365)  # 1 year
DATA_TIMEFRAME = "1d"

# ==========================================
# AGOA Tier Configuration
# ==========================================
ELITE_THRESHOLD = 0.10        # Top X% -> Elite
SURVIVAL_THRESHOLD = 0.10     # Bottom X% -> Survival

ELITE_ALLOCATION = 0.50
CORE_ALLOCATION = 0.40
SURVIVAL_ALLOCATION = 0.10

# ==========================================
# Scoring Weights
# ==========================================
SHARPE_WEIGHT = 0.50
RETURN_WEIGHT = 0.30
DRAWDOWN_WEIGHT = 0.20

# ==========================================
# Timing and Scheduling
# ==========================================
LOOKBACK_WEEKS = 12                   # 3-month lookback suits monthly recomputation
RECOMPUTE_FREQUENCY = "monthly"       # "monthly" or "weekly"
RECOMPUTE_MONTHLY_TIMING = "last"     # "first" or "last" trading day of the month
RECOMPUTE_DAYS = ["Wednesday", "Friday"]  # used only when RECOMPUTE_FREQUENCY == "weekly"

# ==========================================
# Risk Controls
# ==========================================
MAX_SINGLE_STRATEGY_ALLOCATION = 0.60   # Hard cap
MIN_SINGLE_STRATEGY_ALLOCATION = 0.02   # Floor for Survival tier

# ==========================================
# Dynamic Indicator-Based Overrides
# ==========================================
ENABLE_VOLATILITY_REGIME_FILTER = True   # If VIX > threshold, reduce Elite allocation, raise Survival
VIX_HIGH_THRESHOLD = 25
ENABLE_MOMENTUM_BOOST = True             # Boost Elite allocation if 5d momentum is still positive
ENABLE_CORRELATION_PENALTY = True        # Penalize strategies with >0.85 correlation to each other
ENABLE_SECTOR_CONCENTRATION_CAP = True   # Max 35% of capital in same sector strategies
ENABLE_DRAWDOWN_CIRCUIT_BREAKER = True   # If any strategy drawdown > 20%, force to Survival tier
ENABLE_ADAPTIVE_LOOKBACK = True          # Extend lookback to 5 weeks in high-volatility regimes
ENABLE_WIN_RATE_FLOOR = True             # Penalty if win rate < 35%
ENABLE_TRADE_FREQUENCY_NORMALIZER = True # Normalize score by trade count