"""Section 2.3: Jumps, Structural Shifts, and Heavy Tails"""

# - BTC suffers severe microstructural shocks from exogenous macro events
# - Flovik (2024): models trained on historical data fail when new regimes emerge
#   · Distribution shifts must be quantified explicitly
# - Chen & Kuo-Shing (2024): ARJI-GARCH on BTC options
#   · Time-varying jump intensity → better vol behaviour + short-maturity pricing
#   · Realised jump variation corrects short-maturity pricing errors
# - Siu & Elliott (2021): SETAR-GARCH on BTC
#   · Self-Exciting Threshold AR handles long-memory and conditional non-normality
#   · Hybrid models necessary for regime-switching behaviours

def arji_garch_model(returns, threshold=None):
    # - Decompose returns into diffusion + jump components
    # - Estimate jump intensity lambda_t as autoregressive process:
    #   · lambda_t = lambda_0 + rho * lambda_{t-1} + gamma * jump_indicator_{t-1}
    # - Fit GARCH variance conditional on jump-adjusted innovations
    # - Return jump-filtered residuals and conditional variance
    pass

def detect_distribution_shift(in_sample_returns, oos_returns, window=60):
    # - Compute rolling KL-divergence between in-sample and OOS distributions
    # - Flag dates where KL-divergence exceeds 2-sigma threshold
    # - Return list of structural break dates
    pass

def setar_garch_threshold(returns, delay=1):
    # - Estimate threshold value tau from return quantiles
    # - Split returns into two regimes: r_{t-delay} <= tau and > tau
    # - Fit separate AR parameters per regime
    # - Overlay GARCH(1,1) on regime-filtered residuals
    pass
