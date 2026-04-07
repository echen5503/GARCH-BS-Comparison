"""Section 5.2 (paper §4.2): The Volatility Smile and Pricing Accuracy"""

# - Compare theoretical IV surfaces to actual market IV
# - BS EWMA:
#   · Produces a rigid, flat IV surface
#   · Severely misprices deep OTM puts AND calls
#   · Flat surface overshoots the market smirk near the money
# - t-GARCH(1,1):
#   · Student-t errors reproduce smile curvature
#   · Closely tracks market bids for deep OTM instruments
#   · Limitation: symmetric variance equation → cannot capture volatility smirk
#     (market actively prices downside skew; GARCH forces symmetry)

def compute_model_iv_surface(pricing_fn, strikes, maturities, S0, r):
    # - For each (K, T) pair:
    #   · model_price = pricing_fn(S0, K, r, T)
    #   · iv = implied_vol_newton_raphson(model_price, S0, K, r, T)
    # - Return 2D grid: iv_surface[maturity_idx, strike_idx]
    pass

def compare_iv_surfaces(market_iv, garch_iv, bs_iv, moneyness_grid, maturities):
    # - For each maturity:
    #   · Plot market_iv, garch_iv, bs_iv vs. moneyness
    #   · Compute smile curvature: d^2(IV)/dK^2 for each model
    # - Report: curvature match score GARCH vs. BS
    # - Highlight OTM call overpricing by GARCH (symmetry artifact)
    pass

def measure_smile_vs_smirk(market_iv, strikes, S0):
    # - Compute put/call skew: IV(0.9*S0) - IV(1.1*S0)
    # - Positive skew → smirk (market prices downside more)
    # - Compare skew magnitude vs. model IVs
    # - Return skew metric per maturity
    pass
