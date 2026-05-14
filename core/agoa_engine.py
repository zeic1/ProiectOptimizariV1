import pandas as pd
from typing import Dict
from loguru import logger
import config

# Strategies that share the same sector for concentration cap enforcement
SECTOR_GROUPS = {
    "equity_intraday": ["atr_strategy", "vwap_strategy"],
    "large_cap": ["rsi_strategy", "bollinger_bands_strategy"],
    "sector_etf": ["macd_crossover_strategy", "dynamic_stop_loss_strategy"],
    "growth": ["momentum_strategy", "breakout_strategy"],
    "commodities_pairs": ["mean_reversion_strategy"],
    "opportunistic": ["gap_fade_strategy"],
}
SECTOR_CAP = 0.35  # max fraction of total capital per sector group

MIN_TRADES_FOR_VALID_SHARPE = 5  # below this, apply trade frequency penalty


class AGOAEngine:
    def allocate(self, metrics_dict: Dict[str, Dict[str, float]], composite_scores: Dict[str, float],
                 total_capital: float, current_vix: float, correlation_matrix: pd.DataFrame,
                 momentum_5d: Dict[str, float], win_rates: Dict[str, float], trade_counts: Dict[str, int]) -> Dict[str, float]:

        if not composite_scores:
            return {}

        allocations = {name: 0.0 for name in composite_scores.keys()}
        strategies = list(composite_scores.keys())
        num_strats = len(strategies)

        modified_scores = composite_scores.copy()
        forced_survival = set()

        if config.ENABLE_DRAWDOWN_CIRCUIT_BREAKER:
            for name, metrics in metrics_dict.items():
                if metrics.get('max_drawdown_pct', 0) > 0.20:
                    logger.warning(f"Circuit Breaker: {name} drawdown > 20%. Forcing to Survival tier.")
                    forced_survival.add(name)

        if config.ENABLE_WIN_RATE_FLOOR:
            for name, wr in win_rates.items():
                if wr < 0.35:
                    modified_scores[name] -= 0.20

        # Penalize strategies with too few trades to have a meaningful Sharpe ratio
        if config.ENABLE_TRADE_FREQUENCY_NORMALIZER:
            for name, count in trade_counts.items():
                if count < MIN_TRADES_FOR_VALID_SHARPE:
                    penalty = 0.20 * (1.0 - count / MIN_TRADES_FOR_VALID_SHARPE)
                    modified_scores[name] -= penalty
                    logger.debug(f"Trade frequency penalty applied to {name}: {penalty:.3f} ({count} trades)")

        if config.ENABLE_CORRELATION_PENALTY and correlation_matrix is not None and not correlation_matrix.empty:
            for i in range(len(strategies)):
                for j in range(i + 1, len(strategies)):
                    s1, s2 = strategies[i], strategies[j]
                    if s1 in correlation_matrix.index and s2 in correlation_matrix.columns:
                        if correlation_matrix.loc[s1, s2] > 0.85:
                            if modified_scores[s1] < modified_scores[s2]:
                                modified_scores[s1] *= 0.85
                            else:
                                modified_scores[s2] *= 0.85

        ranked_strats = sorted(strategies, key=lambda x: modified_scores[x], reverse=True)

        elite_count = max(1, int(num_strats * config.ELITE_THRESHOLD))
        survival_count = max(1, int(num_strats * config.SURVIVAL_THRESHOLD))
        core_count = num_strats - elite_count - survival_count

        elite_alloc = config.ELITE_ALLOCATION
        survival_alloc = config.SURVIVAL_ALLOCATION

        if config.ENABLE_VOLATILITY_REGIME_FILTER and current_vix is not None and current_vix > config.VIX_HIGH_THRESHOLD:
            logger.info(f"VIX ({current_vix:.2f}) > {config.VIX_HIGH_THRESHOLD}. Applying Volatility Regime Filter.")
            elite_alloc = min(elite_alloc, 0.40)

        core_alloc = 1.0 - elite_alloc - survival_alloc

        tiers = {'Elite': [], 'Core': [], 'Survival': []}
        temp_ranked = [s for s in ranked_strats if s not in forced_survival]

        tiers['Elite'] = temp_ranked[:elite_count]
        tiers['Core'] = temp_ranked[elite_count:elite_count + core_count]
        tiers['Survival'] = temp_ranked[elite_count + core_count:] + list(forced_survival)

        def distribute(tier_strats, tier_total_pct):
            if not tier_strats:
                return
            tier_scores = []
            for s in tier_strats:
                sc = max(modified_scores[s], 0.0)
                if config.ENABLE_MOMENTUM_BOOST and s in tiers['Elite'] and momentum_5d.get(s, 0) > 0:
                    sc *= 1.2
                tier_scores.append((s, sc))

            total_score = sum(sc for _, sc in tier_scores)

            for s, sc in tier_scores:
                pct = (sc / total_score) * tier_total_pct if total_score > 0 else tier_total_pct / len(tier_strats)
                pct = max(
                    min(pct, config.MAX_SINGLE_STRATEGY_ALLOCATION),
                    config.MIN_SINGLE_STRATEGY_ALLOCATION if s in tiers['Survival'] else 0
                )
                allocations[s] = pct * total_capital

        for t, a in zip([tiers['Elite'], tiers['Core'], tiers['Survival']], [elite_alloc, core_alloc, survival_alloc]):
            distribute(t, a)

        # Sector concentration cap: redistribute excess from over-weighted sectors
        if config.ENABLE_SECTOR_CONCENTRATION_CAP and total_capital > 0:
            cap_amount = SECTOR_CAP * total_capital
            excess = 0.0
            capped_strats = set()

            for group_strats in SECTOR_GROUPS.values():
                present = [s for s in group_strats if s in allocations]
                group_total = sum(allocations[s] for s in present)
                if group_total > cap_amount:
                    scale = cap_amount / group_total
                    excess += group_total - cap_amount
                    for s in present:
                        allocations[s] *= scale
                        capped_strats.add(s)
                    logger.info(f"Sector cap applied: group {present} capped at {SECTOR_CAP*100:.0f}%")

            # Distribute excess proportionally to uncapped strategies
            if excess > 0:
                uncapped = [s for s in allocations if s not in capped_strats]
                if uncapped:
                    uncapped_total = sum(allocations[s] for s in uncapped)
                    for s in uncapped:
                        if uncapped_total > 0:
                            allocations[s] += excess * (allocations[s] / uncapped_total)
                        else:
                            allocations[s] += excess / len(uncapped)

        return allocations
