"""
To What Extent Does a Student-t GARCH(1,1) Model Capture Observable Phenomena
of Crypto Markets Better Than EWMA Black-Scholes Assumptions?
"""

# ABSTRACT
# - BSM framework assumes constant volatility and log-normal returns
# - Fails to capture volatility clustering and heavy tails in crypto markets
# - Compare: t-GARCH(1,1) vs BSM anchored by 30-day EWMA volatility
# - Dataset: BTC spot data + live Deribit options chains
# - Regimes: Calm / Normal / Panic (classified by native BTC 30-day rolling vol)
# - Out-of-sample window: 2023-2026
# - Results: t-GARCH outperforms EWMA-BSM on smile, VaR, and straddle P&L

# FILE HIERARCHY
# paper/
# ├── 1_introduction/
# │   ├── 1_1_financial_markets.py
# │   ├── 1_2_options_mechanics.py
# │   └── 1_3_research_gap.py
# ├── 2_literature_review/
# │   ├── 2_1_bsm_paradigm.py
# │   ├── 2_2_conditional_heteroskedasticity.py
# │   ├── 2_3_jumps_heavy_tails.py
# │   └── 2_4_computational_frontiers.py
# ├── 3_theoretical_framework/
# │   ├── 3_1_bsm_model.py
# │   └── 3_2_tgarch_model.py
# ├── 4_methodology/
# │   ├── 4_1_data_acquisition.py
# │   ├── 4_2_oos_testing.py
# │   ├── 4_3_regime_classification.py
# │   └── 4_4_monte_carlo_pricing.py
# ├── 5_results/
# │   ├── 5_1_volatility_forecasting.py
# │   ├── 5_2_volatility_smile.py
# │   ├── 5_3_trading_backtest.py
# │   ├── 5_4_pricing_error_distribution.py
# │   └── 5_5_var_exceedances.py
# ├── 6_discussion.py
# ├── 7_conclusion.py
# └── 8_references.py
