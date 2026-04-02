import yfinance as yf
import pandas as pd
import numpy as np
import json
from arch import arch_model

def run_producer():
    # 1. Acquisition
    tickers = ['BTC-USD', '^VIX', '^IRX']
    raw_data = yf.download(tickers, start="2020-01-01", end="2026-03-20", auto_adjust=False)
    
    df = raw_data['Close'].copy()
    df.columns = ['BTC', 'RiskFree', 'VIX']
    df = df.ffill().dropna()
    df['Returns'] = np.log(df['BTC'] / df['BTC'].shift(1))
    
    p25, p90 = df['VIX'].quantile(0.25), df['VIX'].quantile(0.90)
    df['Regime'] = pd.cut(df['VIX'], bins=[0, p25, p90, 500], labels=['Calm', 'Normal', 'Panic'])

    # 2. GARCH Fitting
    am = arch_model(df['Returns'].dropna() * 100, vol='Garch', p=1, q=1, mean='Constant', dist='normal')
    res = am.fit(disp='off')

    # 3. Save Parameters for the Hook
    params = {
        "omega": res.params['omega'] / 10000,
        "alpha": res.params['alpha[1]'],
        "beta": res.params['beta[1]'],
        "mu": res.params['mu'] / 100,
        "vix_p25": p25,
        "vix_p90": p90
    }
    
    with open('garch_params.json', 'w') as f:
        json.dump(params, f)

    # 4. Save DataFrame
    df.to_csv("crypto_research_data.csv")
    print("Producer Complete: Saved 'crypto_research_data.csv' and 'garch_params.json'")

if __name__ == "__main__":
    run_producer()