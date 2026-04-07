"""Section 1.3: The Research Gap"""

# - BSM assumes constant volatility (random walk with fixed sigma)
# - Practitioners patch BSM with rolling EWMA volatility:
#   · EWMA is backward-looking — trails market shocks rather than anticipating them
# - Gap: no rigorous out-of-sample comparison of forward-looking GARCH
#   against EWMA-BSM baseline specifically for crypto panic regimes
# - This paper: quantify the empirical and economic divergence out-of-sample

def compute_ewma_volatility(returns, lambda_=0.94, window=30):
    # - Initialise sigma_sq = variance of first `window` returns
    # - For each subsequent return r_t:
    #   · sigma_sq = lambda * sigma_sq + (1 - lambda) * r_t^2
    # - Annualise: sigma = sqrt(sigma_sq * 252)
    # - Return rolling series of EWMA vol estimates
    pass

def highlight_trailing_bias(ewma_vol, realised_vol):
    # - Compute lag: date of EWMA peak vs. date of realised vol peak
    # - Quantify average lag in days across panic episodes
    # - Return summary statistics of trailing bias
    pass
