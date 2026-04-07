"""Section 4.1 (paper §3.1): Data Acquisition and Cleaning"""

# - Two primary data pipelines:
#   1. Spot Prices & Rates:
#      · BTC-USD daily prices via yfinance
#      · Risk-free rate via ^IRX ticker (yfinance)
#   2. Options Chain:
#      · Live options data from Deribit API
#      · Filter: drop illiquid options (volume = 0, wide spreads)
#      · Filter: drop ITM options — retain only OTM and near-ATM
#      · Rationale: ITM options are illiquid and distort IV surface

def fetch_btc_prices(start='2020-01-01', end='2026-03-31'):
    # - yf.download('BTC-USD', start=start, end=end)
    # - Compute log returns: log(S_t / S_{t-1})
    # - Drop NaN rows
    # - Return DataFrame with columns: [Close, Log_Return]
    pass

def fetch_risk_free_rate(start='2020-01-01', end='2026-03-31'):
    # - yf.download('^IRX', start=start, end=end)
    # - Convert annualised percent to decimal: rate / 100
    # - Forward-fill missing dates (weekends/holidays)
    # - Return Series aligned to BTC price dates
    pass

def fetch_deribit_options(expiry_dates, currency='BTC'):
    # - For each expiry in expiry_dates:
    #   · GET /api/v2/public/get_instruments?currency=BTC&kind=option
    #   · GET /api/v2/public/get_order_book for each instrument
    # - Collect: strike, expiry, bid, ask, last, open_interest, mark_iv
    # - Return DataFrame with raw options chain
    pass

def clean_options_chain(options_df, S_current):
    # - Drop rows where open_interest == 0
    # - Drop rows where (ask - bid) / mid_price > 0.5  (illiquid spread)
    # - Classify moneyness: ITM / ATM / OTM
    #   · Call ITM:  K < S_current
    #   · Put  ITM:  K > S_current
    # - Drop all ITM options
    # - Return cleaned OTM/ATM options DataFrame
    pass
