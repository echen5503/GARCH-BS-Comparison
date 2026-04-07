"""Section 3.1 (paper §2.1): The Black-Scholes-Merton Paradigm"""

# - Asset price follows Geometric Brownian Motion:
#   dS_t = mu*S_t*dt + sigma*S_t*dW_t
#   · sigma is constant; dW_t ~ N(0, dt) → log-normal returns
# - European Call closed-form:
#   C = S0*N(d1) - K*exp(-r*T)*N(d2)
#   · d1 = [ln(S0/K) + (r + 0.5*sigma^2)*T] / (sigma*sqrt(T))
#   · d2 = d1 - sigma*sqrt(T)
# - EWMA Benchmark (this paper's BSM feed):
#   · Use 30-day EWMA of historical vol instead of a global constant
#   · Mimics naive market makers who linearly extrapolate recent variance
#   · Backward-looking: trails shocks, does not anticipate them

import math

def bsm_price(S0, K, r, T, sigma, option_type='call'):
    # - d1 = (ln(S0/K) + (r + 0.5*sigma^2)*T) / (sigma*sqrt(T))
    # - d2 = d1 - sigma*sqrt(T)
    # - If call:  price = S0*N(d1) - K*exp(-r*T)*N(d2)
    # - If put:   price = K*exp(-r*T)*N(-d2) - S0*N(-d1)
    # - Return price
    pass

def ewma_vol(returns, lambda_=0.94, window=30):
    # - Initialise sigma_sq_0 = var(returns[:window])
    # - For t in range(window, len(returns)):
    #   · sigma_sq_t = lambda*sigma_sq_{t-1} + (1-lambda)*returns[t]^2
    # - Annualise: annualised_vol = sqrt(sigma_sq * 252)
    # - Return series of 30-day EWMA annualised volatilities
    pass

def bsm_with_ewma(S0, K, r, T, returns, lambda_=0.94):
    # - Compute ewma_vol from recent 30 days of returns
    # - Feed sigma into bsm_price
    # - Return BSM price using EWMA-updated volatility
    pass
