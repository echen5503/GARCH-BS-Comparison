"""Section 4.3 (paper §3.3): Regime Classification"""

# - Regimes classified organically from native BTC volatility (no VIX)
# - Metric: 30-day rolling annualised historical volatility of BTC returns
# - Thresholds derived from the full in-sample percentile distribution:
#   · Calm:   vol < 25th percentile
#   · Normal: 25th percentile <= vol <= 90th percentile
#   · Panic:  vol > 90th percentile
# - OOS window (2023-2026) contains limited Panic regimes
#   (primarily isolated to recent geopolitical tensions)

CALM_PERCENTILE   = 25
PANIC_PERCENTILE  = 90

def compute_rolling_vol(returns, window=30):
    # - rolling_vol = returns.rolling(window).std() * sqrt(252)
    # - Return annualised rolling volatility series
    pass

def classify_regimes(rolling_vol, in_sample_vol):
    # - calm_threshold  = np.percentile(in_sample_vol, CALM_PERCENTILE)
    # - panic_threshold = np.percentile(in_sample_vol, PANIC_PERCENTILE)
    # - regimes = pd.cut(rolling_vol, bins=[-inf, calm_threshold,
    #                    panic_threshold, inf],
    #                    labels=['Calm', 'Normal', 'Panic'])
    # - Return Series of regime labels aligned to rolling_vol index
    pass

def regime_summary_statistics(oos_returns, regimes):
    # - For each regime in ['Calm', 'Normal', 'Panic']:
    #   · Filter returns by regime
    #   · Compute: mean, std, skew, kurtosis, % days in regime
    # - Return summary DataFrame
    pass
