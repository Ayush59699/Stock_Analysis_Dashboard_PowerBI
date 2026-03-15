import os
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend    import MACD
from ta.volatility import BollingerBands
from fetch_data import main as fetch

# Config
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
RAW_FILE   = os.path.join(DATA_DIR, "raw_prices.csv")
EXCEL_FILE = os.path.join(DATA_DIR, "stock_analysis.xlsx")
RISK_FREE  = 0.06          # 6% India risk-free rate proxy
STOCKS     = ["TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "RELIANCE.NS"]
NIFTY      = "^NSEI"

# Load data
def load_raw():
    if not os.path.exists(RAW_FILE):
        print("[metrics] raw_prices.csv not found — fetching now...")
        fetch()
    df = pd.read_csv(RAW_FILE, parse_dates=["date"])
    df.sort_values(["ticker", "date"], inplace=True)
    return df


# Sheet 1: prices
def build_prices(df):
    return df.copy()


# Sheet 2: returns
def build_returns(df):
    nifty_df = df[df["ticker"] == NIFTY][["date", "close"]].copy()
    nifty_df.rename(columns={"close": "nifty_close"}, inplace=True)
    nifty_df["nifty_return"] = nifty_df["nifty_close"].pct_change()

    frames = []
    for ticker in STOCKS:
        t = df[df["ticker"] == ticker].copy()
        t["daily_return"]      = t["close"].pct_change()
        t["cumulative_return"] = (1 + t["daily_return"]).cumprod() - 1
        t = t.merge(nifty_df[["date", "nifty_return"]], on="date", how="left")
        t["alpha"] = t["daily_return"] - t["nifty_return"]
        frames.append(t[["date", "ticker", "daily_return", "cumulative_return", "nifty_return", "alpha"]])

    return pd.concat(frames, ignore_index=True)


# Sheet 3: technicals
def build_technicals(df):
    frames = []
    for ticker in STOCKS:
        t = df[df["ticker"] == ticker].copy().reset_index(drop=True)
        close = t["close"]

        # RSI
        t["rsi_14"] = RSIIndicator(close=close, window=14).rsi()

        # MACD
        macd_obj        = MACD(close=close)
        t["macd"]       = macd_obj.macd()
        t["macd_signal"]= macd_obj.macd_signal()
        t["macd_hist"]  = macd_obj.macd_diff()

        # Bollinger Bands
        bb              = BollingerBands(close=close, window=20, window_dev=2)
        t["bb_upper"]   = bb.bollinger_hband()
        t["bb_mid"]     = bb.bollinger_mavg()
        t["bb_lower"]   = bb.bollinger_lband()

        # Moving averages
        t["ma_50"]  = close.rolling(50).mean()
        t["ma_200"] = close.rolling(200).mean()

        frames.append(t[["date", "ticker", "rsi_14", "macd", "macd_signal",
                          "macd_hist", "bb_upper", "bb_mid", "bb_lower",
                          "ma_50", "ma_200"]])
    return pd.concat(frames, ignore_index=True)


# Sheet 4: risk
def build_risk(df):
    frames = []
    for ticker in STOCKS:
        t = df[df["ticker"] == ticker].copy().reset_index(drop=True)
        t["daily_return"] = t["close"].pct_change()

        # Rolling 30-day volatility (annualised)
        t["rolling_volatility_30d"] = t["daily_return"].rolling(30).std() * np.sqrt(252)

        # Annualised volatility (full period)
        ann_vol = t["daily_return"].std() * np.sqrt(252)
        t["annualised_volatility"] = ann_vol

        # Max drawdown
        roll_max         = t["close"].cummax()
        drawdown         = (t["close"] - roll_max) / roll_max
        t["max_drawdown"]= drawdown.cummin()

        frames.append(t[["date", "ticker", "rolling_volatility_30d",
                          "annualised_volatility", "max_drawdown"]])
    return pd.concat(frames, ignore_index=True)


# Sheet 5: summary
def build_summary(df):
    rows = []
    for ticker in STOCKS:
        t = df[df["ticker"] == ticker].copy().reset_index(drop=True)
        close         = t["close"]
        daily_ret     = close.pct_change().dropna()

        current_price  = round(close.iloc[-1], 2)
        return_1y      = round((close.iloc[-1] / close.iloc[-252] - 1) * 100, 2) if len(close) >= 252 else None
        ann_vol        = round(daily_ret.std() * np.sqrt(252) * 100, 2)
        ann_return     = round(daily_ret.mean() * 252 * 100, 2)
        sharpe         = round((ann_return / 100 - RISK_FREE) / (ann_vol / 100), 2) if ann_vol else None
        roll_max       = close.cummax()
        max_dd         = round(((close - roll_max) / roll_max).min() * 100, 2)

        # Technical signals (latest values)
        rsi      = RSIIndicator(close=close, window=14).rsi().iloc[-1]
        macd_obj = MACD(close=close)
        macd_val = macd_obj.macd().iloc[-1]
        sig_val  = macd_obj.macd_signal().iloc[-1]
        ma50     = close.rolling(50).mean().iloc[-1]

        macd_signal_str = "Bullish" if macd_val > sig_val else "Bearish"

        # BUY / HOLD / SELL scorecard
        if rsi < 40 and macd_val > sig_val and close.iloc[-1] > ma50:
            scorecard = "BUY"
        elif rsi > 65 and macd_val < sig_val and close.iloc[-1] < ma50:
            scorecard = "SELL"
        else:
            scorecard = "HOLD"

        rows.append({
            "ticker":               ticker,
            "current_price":        current_price,
            "return_1y_pct":        return_1y,
            "annualised_volatility_pct": ann_vol,
            "sharpe_ratio":         sharpe,
            "max_drawdown_pct":     max_dd,
            "current_rsi":          round(rsi, 1),
            "macd_signal":          macd_signal_str,
            "signal_scorecard":     scorecard,
        })

    return pd.DataFrame(rows)


# Sheet 6: correlation
def build_correlation(df):
    pivot = df[df["ticker"].isin(STOCKS)].pivot(index="date", columns="ticker", values="close")
    returns = pivot.pct_change().dropna()
    return returns.corr().round(3)


# Sheet 7: anomalies
def build_anomalies(df):
    frames = []
    for ticker in STOCKS:
        t = df[df["ticker"] == ticker].copy()
        t["daily_return"] = t["close"].pct_change()
        std = t["daily_return"].std()
        anomalies = t[t["daily_return"].abs() > 2 * std].copy()
        anomalies["anomaly_type"] = anomalies["daily_return"].apply(
            lambda x: "Large gain" if x > 0 else "Large drop"
        )
        anomalies["daily_return_pct"] = (anomalies["daily_return"] * 100).round(2)
        frames.append(anomalies[["date", "ticker", "close", "daily_return_pct", "anomaly_type"]])
    return pd.concat(frames, ignore_index=True).sort_values(["date"])


# Export to Excel
def export_excel(sheets: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=(sheet_name == "correlation"))
            print(f"  ✓ Sheet '{sheet_name}' — {len(df)} rows")
    print(f"\n[metrics] Saved → {EXCEL_FILE}\n")


# Main
def main():
    print("[metrics] Loading raw data...")
    df = load_raw()
    print(f"[metrics] {len(df)} rows loaded. Computing metrics...\n")

    sheets = {
        "prices":      build_prices(df),
        "returns":     build_returns(df),
        "technicals":  build_technicals(df),
        "risk":        build_risk(df),
        "summary":     build_summary(df),
        "correlation": build_correlation(df),
        "anomalies":   build_anomalies(df),
    }

    print("[metrics] Exporting to Excel:")
    export_excel(sheets)
    print("[metrics] Done. ✓")
    print(f"[metrics] Open Power BI → Get Data → Excel → select:\n         {EXCEL_FILE}\n")
    return sheets


if __name__ == "__main__":
    main()
