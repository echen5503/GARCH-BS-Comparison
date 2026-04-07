"""Section 1.2: The Mechanics of Options"""

# - Options: contracts granting the right (not obligation) to buy (Call) or sell (Put)
#   at strike K
# - Option value is highly sensitive to the market's expectation of future variance
# - American options carry an early-exercise premium:
#   · American calls on non-dividend assets → rarely exercise early
#   · American puts → may exercise early if asset crashes (exercise boundary exists)
# - Crypto's massive intraday dislocations → true cost requires fat-tail models
# - Key properties requiring non-Gaussian models:
#   · Excess kurtosis (fat tails)
#   · Volatility clustering

def price_european_option(S, K, r, T, sigma, option_type):
    # - Compute d1 = [ln(S/K) + (r + 0.5*sigma^2)*T] / (sigma * sqrt(T))
    # - Compute d2 = d1 - sigma * sqrt(T)
    # - If Call: return S*N(d1) - K*exp(-r*T)*N(d2)
    # - If Put:  return K*exp(-r*T)*N(-d2) - S*N(-d1)
    pass

def check_early_exercise_american_put(S, K, r, T, sigma):
    # - Compute intrinsic value = max(K - S, 0)
    # - Compute European put value via BSM
    # - If intrinsic > European value → early exercise is optimal
    pass
