"""Section 7 (paper §6): Conclusion"""

# - EWMA-BSM: industry standard for speed; inadequate for BTC tail-risk reality
# - Strict OOS environment confirms t-GARCH(1,1) superiority in specific conditions:
#   · Captures volatility smile curvature
#   · Superior 30-day VaR in calm regimes (5.8% vs. 10.7% exceedance)
#   · Effective straddle filter: +20% cumulative P&L vs. naive always-buy (-50%)
# - GARCH caveats revealed by data:
#   · Static params → IGARCH behaviour on BTC
#   · Volatility hangover during regime transitions (Normal regime VaR overestimates)
#   · Symmetric model cannot capture downside smirk
# - Final verdict: GARCH provides necessary heavy-tailed framework to survive
#   crypto extremes, but requires:
#   · Asymmetric extensions (GJR-GARCH / EGARCH)
#   · Dynamic rolling re-fitting
#   to fully replace BS EWMA across all volatility regimes

def summarise_findings():
    # - Print table: GARCH vs. BS comparison across all five result dimensions
    #   · Volatility forecast accuracy
    #   · Smile reproduction
    #   · Straddle backtest P&L
    #   · Pricing error distribution
    #   · VaR exceedance rates by regime
    pass

def future_research_directions():
    # - [1] GJR-GARCH / EGARCH for smirk asymmetry
    # - [2] Rolling-window re-fitting to eliminate IGARCH hangover
    # - [3] LSTM-GARCH hybrid for OOS vol forecasting
    # - [4] Physics-Informed Neural Networks to replace MC simulation
    # - [5] Jump-diffusion augmentation (ARJI-GARCH) for macro shock events
    pass
