"""Section 6 (paper §5): Discussion and Limitations"""

# - t-GARCH(1,1) empirical advantages:
#   · Better smile reproduction
#   · More accurate VaR in calm regimes
#   · Effective vol-underpricing filter for trading strategies
# - Limitations:
#   1. Computational cost:
#      · Monte Carlo is too slow for high-frequency market making
#      · Future: Physics-Informed Neural Networks to solve stochastic PDEs (Lu et al., 2021)
#   2. Structural symmetry:
#      · Symmetric variance equation → cannot capture volatility smirk
#      · Fix: GJR-GARCH or EGARCH to penalise negative shocks differently
#   3. IGARCH hangover from rigid OOS cutoff:
#      · High beta persistence → model "remembers" old macro panics
#      · Fix: rolling-window re-fitting so model can forget outdated shocks
#      · Would improve VaR accuracy in Normal regimes

def quantify_computational_cost(n_paths, n_steps, n_options):
    # - bsm_time = n_options * constant_closed_form_cost
    # - mc_time  = n_options * n_paths * n_steps * per_step_cost
    # - speedup_needed = mc_time / bsm_time
    # - Return speedup_needed (motivates neural PDE solver research)
    pass

def asymmetric_garch_extensions():
    # - GJR-GARCH: sigma_t^2 = omega + (alpha + gamma*I_{eps<0})*eps_{t-1}^2
    #              + beta*sigma_{t-1}^2
    #   · gamma > 0 → negative shocks increase variance more than positive
    # - EGARCH:    log(sigma_t^2) = omega + alpha*(|z_{t-1}| - E|z|)
    #              + gamma*z_{t-1} + beta*log(sigma_{t-1}^2)
    #   · Naturally captures leverage effect (smirk asymmetry)
    # - Fit both extensions on BTC in-sample data
    # - Compare OOS smile reproduction vs. symmetric GARCH
    pass

def rolling_window_refit(returns, window_years=3, step_months=6):
    # - For each OOS date t spaced step_months apart:
    #   · in_sample = returns[t - window_years : t]
    #   · Refit t-GARCH(1,1) on in_sample
    #   · Store updated params (omega, alpha, beta, nu) for date t
    # - Compare rolling-refitted VaR vs. static-param VaR in Normal regime
    pass
