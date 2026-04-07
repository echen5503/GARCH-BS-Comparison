# To What Extent Does a Student-t GARCH(1,1) Model Capture Observable Phenomena of Crypto Markets Better Than EWMA Black-Scholes Assumptions?

- Compare t-GARCH(1,1) against EWMA-anchored BSM for BTC derivative pricing
- Strict out-of-sample evaluation (2023–2026) across Calm / Normal / Panic regimes
- Metrics: volatility smile fit, VaR exceedances, straddle backtest P&L

---

## File Hierarchy

```
paper/
├── __init__.py                              # Abstract + file map
├── 1_introduction/
│   ├── 1_1_financial_markets.py             # Crypto market structure
│   ├── 1_2_options_mechanics.py             # Options pricing fundamentals
│   └── 1_3_research_gap.py                  # EWMA backward-looking bias
├── 2_literature_review/
│   ├── 2_1_bsm_paradigm.py                  # BSM, volatility smile, Newton-Raphson IV
│   ├── 2_2_conditional_heteroskedasticity.py # GARCH, CRIX, Duan risk-neutral
│   ├── 2_3_jumps_heavy_tails.py             # ARJI-GARCH, SETAR-GARCH, dist shifts
│   └── 2_4_computational_frontiers.py       # MC, PINNs, LSTM-GARCH, HyperIV
├── 3_theoretical_framework/
│   ├── 3_1_bsm_model.py                     # GBM → closed-form BSM + EWMA feed
│   └── 3_2_tgarch_model.py                  # Conditional variance + Student-t errors
├── 4_methodology/
│   ├── 4_1_data_acquisition.py              # yfinance + Deribit, OTM/ATM filter
│   ├── 4_2_oos_testing.py                   # In-sample fit 2020–2023, freeze params
│   ├── 4_3_regime_classification.py         # 30-day rolling vol percentile buckets
│   └── 4_4_monte_carlo_pricing.py           # Implied yield + beta dampening (VRP)
├── 5_results/
│   ├── 5_1_volatility_forecasting.py        # IGARCH hangover, leading vs. trailing
│   ├── 5_2_volatility_smile.py              # Smile curvature, smirk asymmetry
│   ├── 5_3_trading_backtest.py              # Signal-driven straddle, +20% OOS P&L
│   ├── 5_4_pricing_error_distribution.py    # BS smoothness vs. GARCH symmetry fails
│   └── 5_5_var_exceedances.py               # 95% VaR by regime (MC vs. EWMA-Gaussian)
├── 6_discussion.py                          # Limitations: speed, smirk, IGARCH
├── 7_conclusion.py                          # Summary + future directions
└── 8_references.py                          # Full bibliography + REFERENCES dict
```

---

## 1. Introduction

- **1.1 Financial Markets** — Crypto: continuous, unique macro drivers, non-normal returns
- **1.2 Options Mechanics** — Call/Put, strike K, early exercise, fat-tail pricing need
- **1.3 Research Gap** — EWMA trails shocks; this paper quantifies forward-looking GARCH advantage OOS

---

## 2. Literature Review

- **2.1 BSM Paradigm** — Constant vol, volatility smile, Newton-Raphson implied vol
- **2.2 Conditional Heteroskedasticity** — GARCH(1,1), Duan LRNVR, BTC/CRIX vol index
- **2.3 Jumps & Heavy Tails** — ARJI-GARCH time-varying jumps, SETAR-GARCH regime switching
- **2.4 Computational Frontiers** — Monte Carlo cost, PINNs, LSTM-GARCH, HyperIV smoothing
- **Gap** — No rigorous OOS backtest of t-GARCH straddle vs. EWMA-BSM in panic regimes

---

## 3. Theoretical Framework

- **3.1 BSM Model**
  - `dS_t = μS_t dt + σS_t dW_t`
  - Closed form: `C = S0·N(d1) − K·e^{−rT}·N(d2)`
  - EWMA benchmark: 30-day rolling vol fed into BSM instead of constant σ
- **3.2 t-GARCH(1,1)**
  - `σ_t² = ω + α·ε_{t−1}² + β·σ_{t−1}²`
  - Innovations `ε_t = σ_t·z_t`, `z_t ~ Student-t(ν)`
  - Heavy tails built into variance mechanism via ν degrees of freedom

---

## 4. Methodology

- **4.1 Data** — BTC-USD + ^IRX via yfinance; Deribit options API; drop ITM + illiquid
- **4.2 OOS Protocol** — Fit params on 2020–2023 only; freeze; evaluate 2023–2026
- **4.3 Regime Classification** — 30-day rolling vol: Calm (<p25) / Normal (p25–p90) / Panic (>p90)
- **4.4 Monte Carlo** — 2,000 paths; implied yield replaces risk-free rate; beta dampened to 0.95

---

## 5. Empirical Results

- **5.1 Volatility Forecasting** — α+β≈1 (IGARCH); ν=2.95; GARCH ≈ EWMA over long horizons
- **5.2 Volatility Smile** — GARCH reproduces smile curvature; fails to capture downside smirk
- **5.3 Trading Backtest** — GARCH signal fires 27/39 periods; +20% OOS P&L vs. −50% naive
- **5.4 Pricing Errors** — BS fails at low TTM near-the-money; GARCH fails on OTM calls
- **5.5 VaR Exceedances**

  | Regime | Target | GARCH | BS EWMA |
  |:-------|:------:|:-----:|:-------:|
  | Calm   |  5.0%  |  5.8% |  10.7%  |
  | Normal |  5.0%  |  0.7% |   2.7%  |
  | Panic  |  5.0%  |  0.0% |   0.0%  |

---

## 6. Discussion & Limitations

- GARCH MC too slow for HFT → future: PINNs to solve SDEs (Lu et al., 2021)
- Symmetric variance → cannot capture smirk → fix: GJR-GARCH or EGARCH
- IGARCH hangover from static fit → fix: rolling-window re-fitting

---

## 7. Conclusion

- EWMA-BSM: fast but inadequate for BTC tail risk
- t-GARCH(1,1) wins on: smile fit, calm-regime VaR, straddle signal quality
- GARCH caveats: IGARCH persistence, symmetric smile, volatility hangover in Normal regime
- Next steps: asymmetric extensions + dynamic re-fitting to replace BS EWMA across all regimes

---

## References

See [paper/8_references.py](paper/8_references.py) for full bibliography.
