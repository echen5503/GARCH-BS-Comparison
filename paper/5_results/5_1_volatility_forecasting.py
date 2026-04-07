"""Section 5.1 (paper §4.1): Volatility Forecasting — Leading vs. Trailing"""

# - Fitted params: alpha=0.0863, beta=0.9137, nu=2.95
# - alpha + beta ≈ 1.0 → IGARCH behaviour
#   · Shocks do not decay → GARCH forecast ≈ BS EWMA over extended periods
#   · Indicates static parameter fit is not fully robust for BTC
#   · True GARCH should exhibit mean reversion; this one doesn't
# - nu=2.95 < 4 → undefined kurtosis (infinite fourth moments)
#   · Explains heavy tails but exacerbates IGARCH hangover effect
# - OOS period (2023-2026) has limited Panic regimes
#   · Limits observation of model during sustained high-volatility events

ALPHA_FITTED = 0.0863
BETA_FITTED  = 0.9137
NU_FITTED    = 2.95

def compare_garch_vs_ewma(oos_garch_vol, ewma_vol, realised_vol):
    # - Compute RMSE for each model vs. realised_vol
    # - Compute mean absolute error (MAE) for each model
    # - Test lead/lag: cross-correlate vol series with realised_vol
    # - Report: GARCH persistence, EWMA lag, both vs. realised
    pass

def diagnose_igarch_behaviour(alpha, beta):
    # - persistence = alpha + beta
    # - half_life = log(0.5) / log(beta)  (days for shock to halve)
    # - If persistence >= 0.99: warn('IGARCH: shocks persist indefinitely')
    # - Return persistence, half_life
    pass

def plot_vol_comparison(dates, garch_vol, ewma_vol, realised_vol, regimes):
    # - Plot three vol series on same axes
    # - Shade background by regime (Calm=green, Normal=yellow, Panic=red)
    # - Mark major BTC price events (crashes, spikes)
    # - Save figure to figures/figure2_synthetic_vix.png
    pass
