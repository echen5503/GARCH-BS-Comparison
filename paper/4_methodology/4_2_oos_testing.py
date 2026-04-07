"""Section 4.2 (paper §3.2): Out-of-Sample (OOS) Testing Protocol"""

# - In-Sample period:  2020-01-01 → 2023-01-01
#   · Fit t-GARCH(1,1) parameters (omega, alpha, beta, nu) here only
#   · Use arch Python framework (Sheppard et al., 2021)
# - Out-of-Sample period: 2023-01-01 → 2026-03-31
#   · ALL empirical comparisons conducted entirely on OOS data
#   · No re-fitting — static parameters from in-sample
#   · Eliminates look-ahead bias
# - Key rule: GARCH parameters are frozen after in-sample fit

IN_SAMPLE_END   = '2023-01-01'
OOS_START       = '2023-01-01'
OOS_END         = '2026-03-31'

def split_in_out_of_sample(prices_df):
    # - in_sample  = prices_df[prices_df.index <  IN_SAMPLE_END]
    # - oos        = prices_df[prices_df.index >= OOS_START]
    # - Assert no overlap between splits
    # - Return in_sample, oos
    pass

def fit_garch_in_sample(in_sample_returns):
    # - Call fit_tgarch(in_sample_returns)  [see 3_2_tgarch_model.py]
    # - Store params: omega, alpha, beta, nu
    # - Log warning if alpha + beta >= 1 (IGARCH behaviour)
    # - Return frozen parameter dict — do NOT refit on OOS data
    pass

def apply_frozen_garch_oos(frozen_params, oos_returns):
    # - Initialise sigma_sq from last in-sample conditional variance
    # - For each OOS date t:
    #   · Compute epsilon_t from frozen params + oos_returns[t]
    #   · Update sigma_sq_t = omega + alpha*epsilon_t^2 + beta*sigma_sq_{t-1}
    # - Return OOS conditional variance series (no re-estimation)
    pass
