"""Section 4 (paper §3): Methodology and Experimental Design"""

# - Four methodological pillars:
#   · 4_1_data_acquisition.py    — BTC spot prices, rates, Deribit options
#   · 4_2_oos_testing.py         — strict in/out-of-sample split, no look-ahead
#   · 4_3_regime_classification.py — Calm / Normal / Panic via native BTC vol
#   · 4_4_monte_carlo_pricing.py — risk-neutral MC with implied yield + beta damping
