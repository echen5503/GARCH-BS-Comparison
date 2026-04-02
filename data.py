import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from arch import arch_model
from scipy.stats import norm

# ==========================================
# 1. ROBUST DATA ACQUISITION
# ==========================================
def get_crypto_research_data():
    tickers = ['BTC-USD', '^VIX', '^IRX']
    print(f"Fetching data for {tickers}...")
    
    # auto_adjust=False ensures we keep all columns; 
    # yfinance 0.2.50+ returns MultiIndex by default.
    raw_data = yf.download(tickers, start="2020-01-01", end="2026-03-20", auto_adjust=False)
    
    # Handle MultiIndex and select 'Close' (BTC has no Adj Close)
    # Using 'Price' level to extract tickers
    data = raw_data['Close'].copy()
    data.columns = ['BTC', 'RiskFree', 'VIX']
    data = data.ffill().dropna()
    
    # Calculate Log Returns
    data['Returns'] = np.log(data['BTC'] / data['BTC'].shift(1))
    
    # Define Regimes (Panic vs Calm)
    p25, p90 = data['VIX'].quantile(0.25), data['VIX'].quantile(0.90)
    data['Regime'] = pd.cut(data['VIX'], bins=[0, p25, p90, 500], labels=['Calm', 'Normal', 'Panic'])
    
    return data.dropna(), (p25, p90)

df, thresholds = get_crypto_research_data()

# ==========================================
# 2. GARCH(1,1) FITTING
# ==========================================
# Scale returns by 100 for better optimization convergence
am = arch_model(df['Returns'] * 100, vol='Garch', p=1, q=1, mean='Constant', dist='normal')
res = am.fit(disp='off')

# Extract Parameters (Scaled back for pricing)
omega = res.params['omega'] / 10000 
alpha = res.params['alpha[1]']
beta = res.params['beta[1]']
mu_phys = res.params['mu'] / 100
h_last = (res.conditional_volatility.iloc[-1] / 100)**2

# ==========================================
# 3. PRICING ENGINES (BS vs DUAN GARCH)
# ==========================================

def black_scholes_call(S, K, T, r, sigma):
    """Analytic BS Model: Assumes Constant Variance"""
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)

def duan_garch_call(S, K, T_days, r_daily, h_init, n_sims=10000):
    """
    Duan (1995) Local Risk-Neutral Valuation Relationship (LRNVR)
    Under Q-measure: R_t = r - 0.5*h_t + sqrt(h_t)*z_t
    """
    prices = np.full(n_sims, S, dtype=float)
    h = np.full(n_sims, h_init, dtype=float)
    
    for _ in range(int(T_days)):
        z = np.random.standard_normal(n_sims)
        # S_t = S_{t-1} * exp(r - 0.5*h_t + sqrt(h_t)*z_t)
        prices *= np.exp(r_daily - 0.5 * h + np.sqrt(h) * z)
        # h_t = omega + alpha * h_{t-1} * z_{t-1}^2 + beta * h_{t-1}
        h = omega + alpha * h * (z**2) + beta * h
        
    payoffs = np.maximum(prices - K, 0)
    return np.exp(-r_daily * T_days) * np.mean(payoffs)

# ==========================================
# 4. GENERATING FIGURES
# ==========================================

# Figure 1: BTC Price with Regime Shading
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['BTC'], color='black', alpha=0.3, label='BTC Price')
plt.fill_between(df.index, 0, df['BTC'].max(), where=(df['Regime'] == 'Panic'), color='red', alpha=0.2, label='Panic')
plt.fill_between(df.index, 0, df['BTC'].max(), where=(df['Regime'] == 'Calm'), color='green', alpha=0.2, label='Calm')
plt.title("Figure 1: BTC Market Regimes (VIX Shaded)")
plt.yscale('log')
plt.legend()
plt.savefig("btcprice.png")

# Figure 3 Preview: Volatility Smile Comparison
# (Pricing 10% OTM to 10% ITM options)
strikes = np.linspace(df['BTC'].iloc[-1] * 0.8, df['BTC'].iloc[-1] * 1.2, 10)
bs_prices = [black_scholes_call(df['BTC'].iloc[-1], k, 30/365, df['RiskFree'].iloc[-1]/100, np.sqrt(h_last*365)) for k in strikes]
garch_prices = [duan_garch_call(df['BTC'].iloc[-1], k, 30, (df['RiskFree'].iloc[-1]/100)/365, h_last) for k in strikes]

plt.figure(figsize=(10, 5))
plt.plot(strikes / df['BTC'].iloc[-1], bs_prices, label='Black-Scholes (Constant Vol)', linestyle='--')
plt.plot(strikes / df['BTC'].iloc[-1], garch_prices, label='GARCH (Varying Vol)', marker='o')
plt.title("Figure 3: Option Pricing Comparison (Moneyness vs Price)")
plt.xlabel("Moneyness (K/S)")
plt.ylabel("Option Price ($)")
plt.legend()
plt.savefig("fig.png")

print("\n--- Summary Statistics (Figure 4) ---")
print(df.groupby('Regime')['Returns'].agg(['mean', 'std', 'skew', 'kurt']).rename(columns={'std': 'Volatility'}))