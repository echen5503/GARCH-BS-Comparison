"""Section 5.3 (paper §4.3): Trading Backtest — The Signal-Driven Straddle"""

# - Strategy: buy 30-day ATM straddle when GARCH forecasts underpriced vol
# - Market IV constructed as: EWMA_vol * (1 + VRP_MARKUP) → simulates MM pricing
# - Signal condition: GARCH_vol_forecast > market_iv + SIGNAL_THRESHOLD
#   · Fires on 27 of 39 available periods
# - Cost: SPREAD_COST per trade (market maker spread)
# - Benchmark: naive always-buy straddle → ~-50% cumulative loss (theta bleed)
# - GARCH strategy result: ~+20% cumulative OOS P&L
#   · Avoids overprice-vol regimes → preserves capital
#   · Captures tail-risk upside during underpriced-vol periods

VRP_MARKUP        = 0.20    # 20% variance risk premium markup
SIGNAL_THRESHOLD  = 0.05    # GARCH must exceed market IV by ≥ 5%
SPREAD_COST       = 0.015   # 1.5% fixed premium per trade

def build_market_iv(ewma_vol, vrp_markup=VRP_MARKUP):
    # - market_iv = ewma_vol * (1 + vrp_markup)
    # - Return synthetic market IV series
    pass

def generate_garch_signal(garch_vol_forecast, market_iv,
                          threshold=SIGNAL_THRESHOLD):
    # - signal = garch_vol_forecast > market_iv + threshold
    # - Return boolean Series (True = buy straddle)
    pass

def price_atm_straddle(S0, r, T, sigma):
    # - call_price = bsm_price(S0, K=S0, r=r, T=T, sigma=sigma, option_type='call')
    # - put_price  = bsm_price(S0, K=S0, r=r, T=T, sigma=sigma, option_type='put')
    # - Return call_price + put_price
    pass

def run_straddle_backtest(prices, garch_vol, ewma_vol, r,
                          spread_cost=SPREAD_COST):
    # - market_iv = build_market_iv(ewma_vol)
    # - signals   = generate_garch_signal(garch_vol, market_iv)
    # - For each 30-day period t:
    #   · If signals[t]:
    #     - entry_cost = price_atm_straddle(S[t], r, T=30/252, sigma=market_iv[t])
    #     - entry_cost *= (1 + spread_cost)
    #     - payoff = |S[t+30] - S[t]|           (straddle payoff at expiry)
    #     - pnl[t] = (payoff - entry_cost) / entry_cost
    #   · Else: pnl[t] = 0
    # - cumulative_pnl = (1 + pnl).cumprod() - 1
    # - Return pnl series, cumulative_pnl, trade_count
    pass

def compare_vs_naive_strategy(garch_pnl, naive_pnl):
    # - Plot cumulative P&L for both strategies
    # - Report: Sharpe ratio, max drawdown, trade count, hit rate
    # - Save figure to PandL_over_time.png
    pass
