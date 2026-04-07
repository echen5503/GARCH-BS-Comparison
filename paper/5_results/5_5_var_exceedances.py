"""Section 5.5 (paper §4.5): Value-at-Risk (VaR) Exceedances"""

# - 30-day forward-looking VaR at 95% confidence
# - BS method:   EWMA_vol * sqrt(30) * 1.645  (Gaussian quantile)
# - GARCH method: 2,000-path Monte Carlo simulation, 5th percentile of path returns
# - Results by regime:
#   ┌─────────┬─────────────────┬──────────────────┬──────────────────────┐
#   │ Regime  │ Expected Target │ GARCH Exceedance │ BS (EWMA) Exceedance │
#   ├─────────┼─────────────────┼──────────────────┼──────────────────────┤
#   │ Calm    │      5.0%       │      5.8%        │        10.7%         │
#   │ Normal  │      5.0%       │      0.7%        │         2.7%         │
#   │ Panic   │      5.0%       │      0.0%        │         0.0%         │
#   └─────────┴─────────────────┴──────────────────┴──────────────────────┘
# - Calm regime: BS is complacent (EWMA drops → VaR too low); GARCH accurate
# - Normal regime: both models overestimate risk
#   · BS: 30-day trailing lag projects historical crises forward
#   · GARCH: beta=0.9137 → vol decays slowly → "phantom" tail risk
# - Panic regime: only 8 days in OOS window → statistically insignificant

CONFIDENCE_LEVEL = 0.95
N_MC_PATHS       = 2000

def compute_bs_var(ewma_vol, horizon=30, confidence=CONFIDENCE_LEVEL):
    # - z_score = scipy.stats.norm.ppf(1 - confidence)  ≈ -1.645
    # - var = ewma_vol * sqrt(horizon / 252) * abs(z_score)
    # - Return 30-day VaR as a positive loss threshold
    pass

def compute_garch_var_mc(params, sigma_sq_0, S0, horizon=30,
                          confidence=CONFIDENCE_LEVEL, n_paths=N_MC_PATHS):
    # - paths = simulate_risk_neutral_paths(params, sigma_sq_0, ...)
    # - terminal_returns = log(paths[:, -1] / S0)
    # - var = abs(np.percentile(terminal_returns, (1 - confidence)*100))
    # - Return Monte Carlo VaR threshold
    pass

def count_exceedances(actual_returns, var_thresholds):
    # - exceedances = actual_returns < -var_thresholds
    # - exceedance_rate = exceedances.mean()
    # - Return exceedance_rate, list of exceedance dates
    pass

def var_backtest_by_regime(oos_returns, garch_var, bs_var, regimes):
    # - For each regime in ['Calm', 'Normal', 'Panic']:
    #   · Filter returns and VaR series by regime
    #   · garch_rate = count_exceedances(returns, garch_var)
    #   · bs_rate    = count_exceedances(returns, bs_var)
    #   · Print table row: regime, 5.0%, garch_rate, bs_rate
    # - Save exceedance plot to VaR_exceedances.png
    pass
