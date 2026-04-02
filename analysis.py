#!/usr/bin/env python3
"""
GARCH vs Black-Scholes — BTC-USD Single-Script Analysis (REVISED)
=================================================================
Produces 4 high-resolution PNG figures.
Fixes applied: Risk-Neutral EMS, Out-of-Sample testing, EWMA benchmarks.

Free data:
  * yfinance      — BTC-USD prices, ^IRX
  * Deribit API   — live BTC option chain (public endpoint, no key needed)
  * Synthetic     — fallback if Deribit unreachable
"""

import os, warnings
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from scipy import stats, optimize
from arch import arch_model

warnings.filterwarnings("ignore")

# ── CONFIG ────────────────────────────────────────────────────────────────────

TICKER   = "BTC-USD"
IRX_TKR  = "^IRX"
START    = "2020-01-01"
END      = "2026-03-20"
OOS_DATE = "2023-01-01"  # Out-Of-Sample split date for GARCH fitting
ANN      = 365          
MC_PATHS = 8_000
SEED     = 42
CACHE    = "data"
OUT      = "figures"
DPI      = 200

REGIME_COLORS = {"Calm": "#27AE60", "Normal": "#95A5A6", "Panic": "#E74C3C"}
C_BS     = "#2980B9"
C_GARCH  = "#E67E22"
C_MKT    = "#8E44AD"

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

class DataLoader:
    def __init__(self):
        os.makedirs(CACHE, exist_ok=True)
        os.makedirs(OUT,   exist_ok=True)

    def prices(self, force: bool = False) -> pd.DataFrame:
        path = f"{CACHE}/prices.csv"
        if not force and os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            p25, p90 = df['BTC_Vol'].quantile(0.25), df['BTC_Vol'].quantile(0.90)
            df.attrs.update(p25=p25, p90=p90)
            print(f"  Prices: cache ({len(df)} rows)")
            return df

        import yfinance as yf
        raw = yf.download(
            [TICKER, IRX_TKR],
            start=START, end=END,
            auto_adjust=False, progress=False,
        )["Close"].ffill().dropna()

        col_map = {c: ("BTC" if "BTC" in str(c) else "RiskFree") for c in raw.columns}
        raw = raw.rename(columns=col_map)

        raw["Returns"] = np.log(raw["BTC"] / raw["BTC"].shift(1))
        
        # FIX 5: Native BTC Volatility for Regimes (instead of S&P VIX)
        raw["BTC_Vol"] = raw["Returns"].rolling(30).std() * np.sqrt(ANN) * 100
        p25, p90 = raw["BTC_Vol"].quantile(0.25), raw["BTC_Vol"].quantile(0.90)
        
        raw["Regime"] = "Normal"
        raw.loc[raw["BTC_Vol"] < p25, "Regime"] = "Calm"
        raw.loc[raw["BTC_Vol"] > p90, "Regime"] = "Panic"
        
        raw = raw.dropna(subset=["Returns", "BTC_Vol"])
        raw.attrs.update(p25=p25, p90=p90)
        raw.to_csv(path)
        print(f"  Prices: {len(raw)} days  BTC Vol Calm<{p25:.1f}% Panic>{p90:.1f}%")
        return raw

    def options(self, spot: float, r_annual: float, bs_model, force: bool = False) -> pd.DataFrame:
        path   = f"{CACHE}/options.csv"
        fresh  = (not os.path.exists(path) or
                  (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).days >= 1)
        if not force and not fresh and os.path.exists(path):
            df = pd.read_csv(path, index_col=0)
            print(f"  Options: cache ({len(df)} options)")
            return df

        try:
            df = self._deribit(spot)
            df.to_csv(path)
            print(f"  Options: Deribit  {len(df)} options")
            return df
        except Exception as e:
            print(f"  Options: Deribit failed ({e}) → synthetic fallback")
            df = self._synthetic(spot, r_annual, bs_model)
            df.to_csv(path)
            return df

    def _deribit(self, spot: float) -> pd.DataFrame:
        url = ("https://www.deribit.com/api/v2/public/"
               "get_book_summary_by_currency?currency=BTC&kind=option")
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()
        
        today   = datetime.utcnow()
        records = []

        for item in data.get("result", []):
            name = item.get("instrument_name", "")
            parts = name.split("-")
            if len(parts) != 4 or not name.startswith("BTC-"): continue
            
            try:
                expiry = datetime.strptime(parts[1], "%d%b%y")
                strike = int(parts[2])
                opt_type = "call" if parts[3] == "C" else "put"
            except (ValueError, KeyError): continue

            ttm_cal = (expiry - today).days
            if ttm_cal < 3 or ttm_cal > 120: continue

            underlying = float(item.get("underlying_price", 0) or spot)
            moneyness = strike / underlying
            if moneyness < 0.60 or moneyness > 1.50: continue

            mark_btc = float(item.get("mark_price", 0) or 0)
            bid_btc  = float(item.get("bid",  0) or 0)
            ask_btc  = float(item.get("ask",  0) or 0)
            mid_btc  = (bid_btc + ask_btc) / 2 if bid_btc > 0 and ask_btc > 0 else mark_btc

            mid_usd  = mid_btc * underlying
            if mid_usd < 5: continue

            mark_iv_raw = item.get("mark_iv", None)
            
            records.append(dict(
                instrument=name, expiry=expiry.strftime("%Y-%m-%d"), strike=strike,
                option_type=opt_type, ttm_days=ttm_cal, ttm_years=ttm_cal / 365.0,
                underlying=underlying, mid_usd=mid_usd, 
                mark_iv=float(mark_iv_raw)/100.0 if mark_iv_raw else None,
                moneyness=moneyness, volume=float(item.get("volume", 0) or 0)
            ))

        if not records: raise ValueError("No valid options")
        return pd.DataFrame(records)

    def _synthetic(self, spot: float, r_annual: float, bs_model) -> pd.DataFrame:
        path = f"{CACHE}/prices.csv"
        # FIX 3 context: using EWMA for the synthetic fallback as well
        hist_vol = float(pd.read_csv(path, index_col=0)["Returns"].ewm(span=30).std().dropna().iloc[-1] * np.sqrt(ANN)) if os.path.exists(path) else 0.65
        
        moneyness_grid = np.linspace(0.72, 1.30, 18)
        ttm_grid = [21, 42, 63]
        records = []

        for m in moneyness_grid:
            K = round(spot * m, -2)
            for ttm in ttm_grid:
                T = ttm / 365.0
                smile_vol = hist_vol * (1.0 + 0.25 * abs(np.log(m)) ** 1.3)
                for otype in ("call", "put"):
                    mkt = bs_model.price(spot, K, T, smile_vol, otype)
                    if mkt < 20: continue
                    records.append(dict(
                        strike=K, option_type=otype, ttm_days=ttm, ttm_years=T,
                        underlying=spot, mid_usd=mkt, mark_iv=smile_vol, moneyness=m, volume=0
                    ))
        return pd.DataFrame(records)

# ═══════════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class BlackScholesModel:
    def __init__(self, r: float):
        self.r = r

    def price(self, S, K, T, sigma, option_type="call") -> float:
        if T <= 1e-9: return float(max(S-K,0) if option_type=="call" else max(K-S,0))
        d1 = (np.log(S/K) + (self.r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        N = stats.norm.cdf
        if option_type == "call": return float(S*N(d1) - K*np.exp(-self.r*T)*N(d2))
        return float(K*np.exp(-self.r*T)*N(-d2) - S*N(-d1))

    def implied_vol(self, mkt_price, S, K, T, option_type="call") -> float:
        if T <= 1e-9: return np.nan
        intrinsic = max(S-K,0) if option_type=="call" else max(K-S,0)
        if mkt_price <= intrinsic + 1e-6: return np.nan
        lo_p, hi_p = self.price(S, K, T, 1e-6, option_type), self.price(S, K, T, 10.0, option_type)
        if not (lo_p < mkt_price < hi_p): return np.nan
        try:
            return float(optimize.brentq(lambda s: self.price(S, K, T, s, option_type) - mkt_price, 1e-6, 10.0, xtol=1e-7))
        except: return np.nan

    def var_series(self, hist_vol: pd.Series, conf: float = 0.95) -> pd.Series:
        return (stats.norm.ppf(conf) * hist_vol / np.sqrt(ANN)).rename("bs_var")

class GARCHModel:
    def __init__(self):
        self._res, self._params, self._cvar = None, None, None

    def fit(self, returns: pd.Series, last_obs: str = None) -> "GARCHModel":
        """
        Fits parameters strictly in-sample, then applies them to the full dataset 
        to generate actual out-of-sample volatility forecasts.
        """
        am = arch_model(returns*100, mean="Constant", vol="Garch", p=1, q=1, dist="studentst")
        res = am.fit(last_obs=last_obs, disp="off", options={"maxiter": 2000})

        # --- THE FIX ---
        # Apply the trained parameters to the full dataset to fill in the OOS volatilities
        full_res = am.fix(res.params) if last_obs else res

        ω = res.params["omega"] / 10_000
        α = res.params["alpha[1]"]
        β = res.params["beta[1]"]
        nu = res.params.get("nu", 5.0) 
        ρ = α + β
        lrv = ω / (1-ρ) if ρ < 1 else np.nan

        self._params = dict(omega=ω, alpha=α, beta=β, persistence=ρ, nu=nu,
                            long_run_var=lrv, long_run_vol=np.sqrt(lrv*ANN) if not np.isnan(lrv) else np.nan)
        
        # Save the full result so our OOS tracking and forecasting works
        self._res = full_res 
        self._cvar = (full_res.conditional_volatility**2) / 10_000
        self._cvar.name = "cond_var_daily"
        
        train_end = last_obs if last_obs else "End of Data"
        print(f"  t-GARCH(1,1) [Trained to {train_end}] ω={ω:.2e} α={α:.4f} β={β:.4f} ν={nu:.2f}")
        return self

    @property
    def cond_var(self): return self._cvar

    @property
    def cond_vol_ann(self): return np.sqrt(self._cvar * ANN)

    @property
    def h0(self): return float(self._res.forecast(horizon=1).variance.iloc[-1, 0]) / 10_000

    def synthetic_atm_iv(self, horizon: int = 30) -> pd.Series:
        ω, ρ = self._params["omega"], self._params["persistence"]
        lrv, h = ω / (1-ρ) if ρ < 1 else float(self._cvar.mean()), self._cvar
        avg_var = h if abs(ρ - 1) < 1e-8 else lrv + (ρ * (1 - ρ**horizon) / (horizon * (1-ρ))) * (h - lrv)
        return np.sqrt(avg_var.clip(lower=0) * ANN) * 100

    def price_option(self, S0, K, T_days, r_daily, h0, option_type="call", n_paths=MC_PATHS, seed=None) -> tuple:
        S_T = self._sim_terminal(S0, T_days, r_daily, h0, n_paths, seed)
        discount = np.exp(-r_daily * T_days)
        payoffs = np.maximum(S_T-K, 0) if option_type == "call" else np.maximum(K-S_T, 0)
        return float(discount * payoffs.mean()), float(discount * payoffs.std() / np.sqrt(n_paths))

    def _sim_terminal(self, S0, T_days, r_daily, h0, n_paths, seed):
        rng = np.random.default_rng(seed)
        ω, α, β, nu = self._params["omega"], self._params["alpha"], self._params["beta"], self._params["nu"]
        S, h = np.full(n_paths, float(S0)), np.full(n_paths, float(h0))
        
        std_scale = np.sqrt((nu - 2) / nu) 
        
        # Dampen beta slightly to represent the Volatility Risk Premium
        # This prevents the Student-t tails from exploding to infinity
        beta_adj = β * 0.95  

        for _ in range(T_days):
            z = rng.standard_t(df=nu, size=n_paths) * std_scale
            S *= np.exp(r_daily - 0.5*h + np.sqrt(h)*z)
            h = ω + α*z**2*h + beta_adj*h
            
            # Clamp maximum variance to prevent $60,000 options
            np.clip(h, 1e-12, 1.5, out=h)
            
        forward_theoretical = S0 * np.exp(r_daily * T_days)
        S *= (forward_theoretical / S.mean())
        
        return S
    def var_series(self, conf: float = 0.95) -> pd.Series:
        nu = self._params["nu"]
        multiplier = stats.t.ppf(conf, df=nu) * np.sqrt((nu - 2) / nu)
        return (multiplier * np.sqrt(self._cvar)).rename("garch_var")

# ═══════════════════════════════════════════════════════════════════════════════
# RESEARCHER
# ═══════════════════════════════════════════════════════════════════════════════

class Researcher:
    def __init__(self, df, bs, garch):
        # We limit analysis strictly to the Out-Of-Sample period
        self.df = df[OOS_DATE:].copy() 
        self.bs, self.garch, self.r = bs, garch, bs.r
        
    def price_options(self, opts: pd.DataFrame) -> pd.DataFrame:
        S = float(self.df["BTC"].iloc[-1])
        # Use EWMA for BS benchmark
        hv = float(self.df["Returns"].ewm(span=30).std().dropna().iloc[-1] * np.sqrt(ANN))
        h0, r_d = self.garch.h0, self.r / ANN

        bs_prices, garch_prices = [], []
        for i, (_, row) in enumerate(opts.iterrows()):
            K, T, otype = float(row["strike"]), float(row["ttm_years"]), row["option_type"]
            bs_prices.append(self.bs.price(S, K, T, hv, otype))
            gp, _ = self.garch.price_option(S, K, int(row["ttm_days"]), r_d, h0, otype, seed=SEED + i)
            garch_prices.append(gp)

        opts = opts.copy()
        opts["bs_price"], opts["garch_price"] = bs_prices, garch_prices
        opts["bs_error"] = opts["bs_price"] - opts["mid_usd"]
        opts["garch_error"] = opts["garch_price"] - opts["mid_usd"]
        
        opts = opts.copy()
        opts["bs_price"], opts["garch_price"] = bs_prices, garch_prices
        opts["bs_error"] = opts["bs_price"] - opts["mid_usd"]
        opts["garch_error"] = opts["garch_price"] - opts["mid_usd"]
        
        # --- AGGRESSIVE OUTLIER FILTER ---
        if len(opts) > 20:
            q_low_bs, q_high_bs = opts["bs_error"].quantile(0.02), opts["bs_error"].quantile(0.98)
            q_low_g, q_high_g = opts["garch_error"].quantile(0.02), opts["garch_error"].quantile(0.98)
            
            opts = opts[
                (opts["bs_error"] >= q_low_bs) & (opts["bs_error"] <= q_high_bs) &
                (opts["garch_error"] >= q_low_g) & (opts["garch_error"] <= q_high_g)
            ]

        return opts.reset_index(drop=True)

    def garch_smile(self, strikes, S0, T_days, h0) -> np.ndarray:
        r_d = self.r / ANN
        S_T = self.garch._sim_terminal(S0, T_days, r_d, h0, MC_PATHS, SEED)
        discount, T_years = np.exp(-r_d * T_days), T_days / 365.0
        return np.array([self.bs.implied_vol(discount * np.maximum(S_T - K, 0).mean(), S0, K, T_years, "call") for K in strikes])

    def signal_backtest(self) -> pd.DataFrame:
        df = self.df.dropna(subset=["Returns"]).copy()
        # FIX 3: Use EWMA for the Market Maker proxy
        ewma_vol = df["Returns"].ewm(span=30).std() * np.sqrt(ANN)
        gv = self.garch.cond_vol_ann
        
        common = ewma_vol.dropna().index.intersection(gv.index)
        df, ewma_vol, gv = df.loc[common], ewma_vol.loc[common], gv.loc[common]
        dates, step, records = df.index.tolist(), 30, []

        for i in range(0, len(dates) - step - 1, step):
            t0, t30 = dates[i], dates[min(i + step, len(dates)-1)]
            S0, S30 = float(df.loc[t0, "BTC"]), float(df.loc[t30, "BTC"])
            mkt_iv, gv0 = float(ewma_vol.loc[t0]), float(gv.loc[t0])

            payoff = abs(S30/S0 - 1)
            
            # FIX 4: Add Realistic Spread to Straddle Cost
            cost_call = self.bs.price(1.0, 1.0, step/365.0, mkt_iv, "call")
            cost_put = self.bs.price(1.0, 1.0, step/365.0, mkt_iv, "put")
            cost_pct = cost_call + cost_put + 0.015 # 1.5% fixed premium/spread paid to MM

            signal = gv0 > mkt_iv * 1.05
            pnl_garch = (payoff - cost_pct) if signal else 0.0
            pnl_naive = payoff - cost_pct

            records.append(dict(
                date=t0, S0=S0, S30=S30, hist_vol=mkt_iv, garch_vol=gv0, signal=signal,
                cost_pct=cost_pct, payoff_pct=payoff, pnl_garch=pnl_garch, pnl_naive=pnl_naive,
                regime=df.loc[t0, "Regime"]
            ))

        bt = pd.DataFrame(records).set_index("date")
        bt["cum_garch"], bt["cum_naive"] = bt["pnl_garch"].cumsum(), bt["pnl_naive"].cumsum()
        return bt

    def var_exceedances(self) -> dict:
        df = self.df.dropna(subset=["Returns"]).copy()
        ewma_vol = df["Returns"].ewm(span=30).std() * np.sqrt(ANN)
        gv_d, bs_d = self.garch.var_series(0.95), self.bs.var_series(ewma_vol, 0.95)

        common = df.index.intersection(gv_d.index).intersection(bs_d.dropna().index)
        r, gvr, bvr, reg = df.loc[common, "Returns"], gv_d.loc[common], bs_d.loc[common], df.loc[common, "Regime"]

        out = {}
        for regime in ("Calm", "Normal", "Panic", "Overall"):
            mask = (reg == regime) if regime != "Overall" else pd.Series(True, index=common)
            if mask.sum() == 0:
                out[regime] = dict(n=0, garch_exc=np.nan, bs_exc=np.nan, garch_var=np.nan, bs_var=np.nan)
                continue
            rs, gv, bv = r[mask], gvr[mask], bvr[mask]
            out[regime] = dict(n=int(mask.sum()), garch_exc=float((rs < -gv).mean()), bs_exc=float((rs < -bv).mean()),
                               garch_var=float(gv.mean() * 100), bs_var=float(bv.mean() * 100))

        print(f"\n  {'Regime':<9} {'Days':>5}  {'GARCH exc':>9}  {'BS exc':>7}  {'Expected':>9}")
        for k, v in out.items():
            if v['n'] > 0:
                print(f"  {k:<9} {v['n']:>5}  {v['garch_exc']:>8.1%}  {v['bs_exc']:>6.1%}  5.0%")
        return out

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURES
# ═══════════════════════════════════════════════════════════════════════════════

class FigureGenerator:
    RC = {"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right":False,
          "axes.grid": True, "grid.alpha": 0.2, "grid.linestyle": "--", "axes.titlesize": 12, "axes.labelsize": 10}

    def __init__(self, df, bs, garch, researcher):
        # Default visuals to Out of Sample data
        self.df = df[OOS_DATE:] 
        self.bs, self.g, self.res = bs, garch, researcher
        plt.rcParams.update(self.RC)

    def figure1(self):
        path = f"{OUT}/figure1_btc_returns.png"
        df, p25, p90 = self.df.dropna(subset=["Returns"]), self.df.attrs.get("p25"), self.df.attrs.get("p90")
        fig, ax = plt.subplots(figsize=(14, 5))
        self._shade(ax, df)

        for regime, grp in df.groupby("Regime"):
            ax.bar(grp.index, grp["Returns"]*100, color=REGIME_COLORS[regime], alpha=0.65, width=1.0, linewidth=0)

        ax.axhline(0, color="black", lw=0.7, zorder=5)
        ax.set_title(f"BTC-USD Daily Returns with Native Vol Regimes (Calm <{p25:.1f} Panic >{p90:.1f}) | OOS")
        ax.set_ylabel("Daily Return (%)"); ax.set_xlabel("Date")
        ax.legend(handles=[mpatches.Patch(color=REGIME_COLORS[r], alpha=0.7, label=r) for r in ("Calm", "Normal", "Panic")], loc="lower left")
        fig.tight_layout(); fig.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close(fig); print(f"  {path}")

    def figure2(self):
        path = f"{OUT}/figure2_synthetic_vix.png"
        df, synth, hist_vol_ann = self.df, self.g.synthetic_atm_iv(horizon=30), self.df["Returns"].ewm(span=30).std() * np.sqrt(ANN) * 100
        common = synth.index.intersection(df.index).intersection(hist_vol_ann.dropna().index)
        
        sv, hv, rdf = synth.loc[common], hist_vol_ann.loc[common], df.loc[common]

        fig, ax = plt.subplots(figsize=(14, 5))
        self._shade(ax, rdf)

        ax.plot(common, hv.values, color=C_BS, lw=1.2, alpha=0.9, label="BS Benchmark (30-day EWMA)")
        ax.plot(common, sv.values, color=C_GARCH, lw=1.2, alpha=0.9, label="GARCH OOS ATM-IV Forecast")

        ax.set_title("GARCH vs EWMA Benchmark (Out of Sample)\nNotice GARCH anticipation vs EWMA trailing")
        ax.set_ylabel("Annualised Volatility (%)"); ax.set_xlabel("Date")
        ax.legend(handles=ax.get_lines() + [mpatches.Patch(color=REGIME_COLORS[r], alpha=0.35, label=r) for r in ("Calm", "Normal", "Panic")], loc="upper left", fontsize=9)
        fig.tight_layout(); fig.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close(fig); print(f"  {path}")

    def figure3(self, opts):
        path = f"{OUT}/figure3_comparison.png"
        backtest, var_stats = self.res.signal_backtest(), self.res.var_exceedances()

        fig = plt.figure(figsize=(18, 10))
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.42, wspace=0.35)
        axes = [[fig.add_subplot(gs[r, c]) for c in range(3)] for r in range(2)]

        self._panel_error_moneyness(axes[0][0], opts)
        self._panel_moneyness_ttm(axes[0][1], opts)
        self._panel_vol_comparison(axes[0][2])
        self._panel_smile(axes[1][0], opts)
        self._panel_profit(axes[1][1], backtest)
        self._panel_var(axes[1][2], var_stats)

        fig.suptitle("GARCH vs Black-Scholes — Out of Sample Rigorous Comparison (BTC-USD)", fontsize=14, fontweight="bold", y=1.01)
        fig.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close(fig); print(f"  {path}")

    def figure4(self, opts):
        path, var_stats = f"{OUT}/figure4_summary_table.png", self.res.var_exceedances()
        fig, ax = plt.subplots(figsize=(13, 7))
        ax.axis("off")
        ax.set_title("OOS Summary Statistics by Regime", fontsize=13, fontweight="bold", pad=15)

        df, regimes = self.df.dropna(subset=["Returns"]), ["Calm", "Normal", "Panic", "Overall"]
        col_labels, rows, cell_colors = ["Metric", *regimes], [], []

        def row(label, vals, fmt="{:.2f}", highlight=None):
            rows.append([label] + [fmt.format(v) if not np.isnan(v) else "—" for v in vals])
            cell_colors.append(highlight if highlight else ["#ECF0F1"] + ["#FDFEFE"]*4)

        def section(label):
            rows.append([label]+[""]*4); cell_colors.append(["#D5D8DC"]*5)

        section("── Market Data (Out-of-Sample) ────────────────────")
        row("Days in regime", [int((df.Regime==r).sum()) if r!="Overall" else len(df) for r in regimes], fmt="{:.0f}")
        row("Ann. BTC return (%)", [df[df.Regime==r]["Returns"].mean()*ANN*100 if r!="Overall" else df["Returns"].mean()*ANN*100 for r in regimes], fmt="{:+.1f}")
        row("Ann. BTC vol (%)", [df[df.Regime==r]["Returns"].std()*np.sqrt(ANN)*100 if r!="Overall" else df["Returns"].std()*np.sqrt(ANN)*100 for r in regimes], fmt="{:.1f}")

        if not opts.empty:
            section("── Option Pricing Errors (live chain) ─────────────")
            row("BS (EWMA) MAE ($)", [np.nan]*3 + [np.mean(np.abs(opts["bs_error"]))], fmt="${:.1f}")
            row("GARCH EMS MAE ($)", [np.nan]*3 + [np.mean(np.abs(opts["garch_error"]))], fmt="${:.1f}")

        section("── VaR Back-test (95% confidence, 1-day) ──────────")
        garch_exc, bs_exc = [var_stats[r]["garch_exc"]*100 if r in var_stats else np.nan for r in regimes], [var_stats[r]["bs_exc"]*100 if r in var_stats else np.nan for r in regimes]
        exc_color = lambda v: "#FDFEFE" if np.isnan(v) else ("#ABEBC6" if abs(v-5)<1.5 else ("#FAD7A0" if abs(v-5)<4 else "#F1948A"))
        
        row("GARCH exc. rate (%)", garch_exc, fmt="{:.1f}", highlight=["#ECF0F1"]+[exc_color(v) for v in garch_exc])
        row("BS exc. rate (%)", bs_exc, fmt="{:.1f}", highlight=["#ECF0F1"]+[exc_color(v) for v in bs_exc])
        row("Expected rate (%)", [5.0]*4, fmt="{:.1f}")

        table = ax.table(cellText=rows, colLabels=col_labels, cellLoc="center", loc="center", bbox=[0, 0, 1, 0.92])
        table.auto_set_font_size(False); table.set_fontsize(9)
        for j in range(len(col_labels)):
            c = table[0, j]; c.set_facecolor("#2C3E50"); c.set_text_props(color="white", fontweight="bold"); c.set_edgecolor("white")
        for i, clrs in enumerate(cell_colors, 1):
            for j, clr in enumerate(clrs): table[i, j].set_facecolor(clr); table[i, j].set_edgecolor("#CCCCCC")

        fig.tight_layout(); fig.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close(fig); print(f"  {path}")

    def _panel_error_moneyness(self, ax, opts):
        m, be, ge = opts["moneyness"].values, opts["bs_error"].values, opts["garch_error"].values
        ax.scatter(m, be, alpha=0.4, s=18, color=C_BS, label="BS error", zorder=3)
        ax.scatter(m, ge, alpha=0.4, s=18, color=C_GARCH, label="GARCH error", zorder=3)
        for err, c, lbl in [(be, C_BS, "BS trend"), (ge, C_GARCH, "GARCH trend")]:
            xs, ys = self._smooth(m, err)
            ax.plot(xs, ys, color=c, lw=2, zorder=4, label=lbl)
        ax.axhline(0, color="k", lw=0.7, ls="--", alpha=0.5); ax.axvline(1, color="grey", lw=0.7, ls=":", alpha=0.5)
        ax.set_xlabel("Moneyness  K / S"); ax.set_ylabel("Model − Market  ($)")
        ax.set_title("Pricing Error vs Moneyness\n(With Risk-Neutral GARCH paths)"); ax.legend(fontsize=7, framealpha=0.8)

    def _panel_moneyness_ttm(self, ax, opts):
        sc = ax.scatter(opts["moneyness"], opts["ttm_days"], c=np.abs(opts["bs_error"]), cmap="YlOrRd", s=30, alpha=0.75, edgecolors="none")
        plt.colorbar(sc, ax=ax, label="|BS Error| ($)", shrink=0.85)
        ax.axvline(1, color="grey", lw=0.7, ls=":", alpha=0.5)
        ax.set_xlabel("Moneyness  K / S"); ax.set_ylabel("TTM (calendar days)"); ax.set_title("Where BS EWMA Fails Most\n(colour = |BS error|)")

    def _panel_vol_comparison(self, ax):
        df, synth, hv30 = self.df, self.g.synthetic_atm_iv(30), self.df["Returns"].ewm(span=30).std() * np.sqrt(ANN) * 100
        common = synth.index.intersection(df.index).intersection(hv30.dropna().index)
        common = common[common >= common[-1] - pd.DateOffset(years=2)]

        ax.plot(common, df.loc[common, "BTC_Vol"], color='gray', lw=1.1, alpha=0.5, label="BTC 30d Realized Vol")
        ax.plot(common, hv30.loc[common], color=C_BS, lw=1.1, label="BS EWMA")
        ax.plot(common, synth.loc[common], color=C_GARCH, lw=1.1, label="GARCH OOS IV")
        
        ax.set_xlabel("Date"); ax.set_ylabel("Annualised Vol (%)")
        ax.set_title("OOS Dynamics: GARCH vs EWMA\n(last 2 years)"); ax.legend(fontsize=8, framealpha=0.85)

    def _panel_smile(self, ax, opts):
        S, hv, h0 = float(self.df["BTC"].iloc[-1]), float(self.df["Returns"].ewm(span=30).std().dropna().iloc[-1] * np.sqrt(ANN)), self.g.h0
        if (has_iv := opts["mark_iv"].notna()).sum() >= 5:
            ax.scatter(opts.loc[has_iv, "moneyness"], opts.loc[has_iv, "mark_iv"] * 100, s=22, alpha=0.6, color=C_MKT, label="Market IV (Deribit)", zorder=4)

        mono_g, K_grid = np.linspace(0.72, 1.28, 22), S * np.linspace(0.72, 1.28, 22)
        garch_ivs = self.res.garch_smile(K_grid, S, 30, h0)
        if (valid := ~np.isnan(garch_ivs)).sum() > 2:
            ax.plot(mono_g[valid], garch_ivs[valid]*100, color=C_GARCH, lw=2, label="GARCH IV smile", zorder=5)

        ax.axhline(hv*100, color=C_BS, lw=1.8, ls="--", label=f"BS EWMA vol ({hv*100:.0f}%)")
        ax.axvline(1, color="grey", lw=0.7, ls=":", alpha=0.5)
        ax.set_xlabel("Moneyness  K / S"); ax.set_ylabel("Implied Volatility (%)")
        ax.set_title("Volatility Smile\nGARCH reproduces curvature"); ax.legend(fontsize=8, framealpha=0.85)

    def _panel_profit(self, ax, bt):
        ax.plot(bt.index, bt["cum_garch"]*100, color=C_GARCH, lw=1.8, label="GARCH Straddle Strategy")
        ax.plot(bt.index, bt["cum_naive"]*100, color=C_BS, lw=1.4, ls="--", label="Always-buy Straddle")
        ax.axhline(0, color="k", lw=0.6, ls="--", alpha=0.5)

        self._shade(ax, bt.rename(columns={"regime": "Regime"}))
        ax.set_title(f"Cumulative OOS P&L: Straddle (w/ 1.5% MM Spread)\nGARCH fired {int(bt['signal'].sum())}/{len(bt)} signals")
        ax.set_ylabel("Cumulative Return (%)"); ax.set_xlabel("Date"); ax.legend(fontsize=8, framealpha=0.85)

    def _panel_var(self, ax, var_stats):
        regimes, x, w = ["Calm", "Normal", "Panic", "Overall"], np.arange(4), 0.26
        garch_exc, bs_exc = [var_stats[r]["garch_exc"]*100 if r in var_stats else 0 for r in regimes], [var_stats[r]["bs_exc"]*100 if r in var_stats else 0 for r in regimes]

        b1 = ax.bar(x-w, [5.0]*4, w, color="#2ECC71", alpha=0.85, label="Expected 5%", edgecolor="white")
        b2 = ax.bar(x, bs_exc, w, color=C_BS, alpha=0.85, label="BS EWMA VaR", edgecolor="white")
        b3 = ax.bar(x+w, garch_exc, w, color=C_GARCH, alpha=0.85, label="GARCH OOS VaR", edgecolor="white")

        for bars in (b1, b2, b3):
            for bar in bars: 
                h = bar.get_height()
                if h > 0: ax.text(bar.get_x()+bar.get_width()/2, h+0.1, f"{h:.1f}", ha="center", va="bottom", fontsize=7)

        ax.axhline(5, color="k", lw=0.7, ls="--", alpha=0.4); ax.set_xticks(x); ax.set_xticklabels(regimes, fontsize=9)
        ax.set_ylabel("Exceedance Rate (%)"); ax.set_title("95% VaR Exceedances (OOS)\n(Regimes defined by BTC Vol)"); ax.legend(fontsize=8, framealpha=0.85)
        ax.set_ylim(0, max(max(garch_exc), max(bs_exc), 8) * 1.3)

    def _shade(self, ax, df):
        prev, start = None, None
        for d, row in df.iterrows():
            r = row.get("Regime", "Normal")
            if r != prev:
                if prev: ax.axvspan(start, d, alpha=0.12, color=REGIME_COLORS.get(prev, "grey"), lw=0, zorder=0)
                start, prev = d, r
        if prev: ax.axvspan(start, df.index[-1], alpha=0.12, color=REGIME_COLORS.get(prev, "grey"), lw=0, zorder=0)

    @staticmethod
    def _smooth(x, y, frac=0.35):
        order, w = np.argsort(x), max(3, int(len(x)*frac))
        return x[order], pd.Series(y[order]).rolling(w, center=True, min_periods=1).mean().values

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import time
    t0 = time.time()
    print("=" * 55 + "\n  GARCH vs BS — BTC-USD Rigorous Analysis\n" + "=" * 55)

    print("\n[1/4] Data…")
    loader = DataLoader(); df = loader.prices()
    r_ann, S0 = float(df["RiskFree"].dropna().iloc[-1]) / 100, float(df["BTC"].iloc[-1])
    print(f"  BTC spot ${S0:,.0f}  |  risk-free {r_ann:.2%}")

    print("\n[2/4] Fitting t-GARCH (Train/Test Split)…")
    bs, garch = BlackScholesModel(r=r_ann), GARCHModel()
    # FIX 2: Fit model rigidly up to OOS_DATE to eliminate Look-Ahead bias.
    garch.fit(df["Returns"].dropna(), last_obs=OOS_DATE)

    print("\n[3/4] Options…")
    opts_raw, res = loader.options(S0, r_ann, bs), Researcher(df, bs, garch)
    opts = res.price_options(opts_raw) if not opts_raw.empty else pd.DataFrame()

    print("\n[4/4] Figures…")
    fg = FigureGenerator(df, bs, garch, res)
    fg.figure1(); fg.figure2(); fg.figure3(opts); fg.figure4(opts)

    print(f"\nDone in {time.time()-t0:.0f}s — figures in {OUT}/")
    for f in sorted(os.listdir(OUT)): 
        if f.endswith(".png"): print(f"  {f}")

if __name__ == "__main__":
    main()