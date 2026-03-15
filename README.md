# NSE Stock Analysis Dashboard

An end-to-end equity analytics pipeline for 5 NSE stocks — automated data ingestion, financial indicator computation, Power BI dashboard, and optional Azure OpenAI daily commentary.

---

## Tech stack
| Layer | Tool |
|---|---|
| Data ingestion | Python, yfinance |
| Analysis | pandas, numpy, ta library |
| Export | openpyxl (Excel) |
| Dashboard | Power BI Desktop |
| AI insights | Azure OpenAI (optional) |

---

## How it works

```
yfinance → raw_prices.csv → compute_metrics.py → stock_analysis.xlsx → Power BI
                                                                    ↓
                                                           ai_insights.py (terminal)
```

Python fetches and analyses the data. Power BI reads the Excel output and displays it visually. Run `scripts/run_all.py` every day after market close to refresh everything.

---

## Setup

```bash
# 1. Clone and enter project
git clone https://github.com/YOUR_USERNAME/stock-dashboard
cd stock-dashboard

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install libraries
pip install -r requirements.txt

# 4. Add Azure credentials (optional — only for ai_insights.py)
# Create a .env file:
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# 5. Run the pipeline
python scripts/run_all.py

# 6. Open Power BI → Get Data → Excel → select data/stock_analysis.xlsx
```

---

## Dashboard pages (Power BI)

**Page 1 — Overview:** KPI cards, normalised price chart (rebased to 100), monthly returns, date slicer

**Page 2 — Technical signals:** Signal scorecard (BUY/HOLD/SELL), Bollinger Bands, RSI with 30/70 lines, MACD histogram

**Page 3 — Risk & portfolio:** Risk vs return scatter, Sharpe ratio ranking, correlation heatmap, rolling volatility, anomaly markers

---

## Daily refresh

```bash
python scripts/run_all.py          # refresh data + Excel
python scripts/ai_insights.py      # optional: AI market commentary
# Then in Power BI: Home → Refresh
```

---

## Key findings
*(Fill in after running with real data)*

- **Finding 1 (performance):** ...
- **Finding 2 (technical signal):** ...
- **Finding 3 (risk):** ...

---

## Resume bullet

> "Built an end-to-end NSE equity analytics dashboard — automated daily data ingestion via yfinance, computed RSI/MACD/Bollinger Band/Sharpe ratio indicators for 5 stocks in Python, and visualised portfolio risk, technical signals, and benchmark-relative performance in Power BI; integrated Azure OpenAI to generate daily market commentary from computed indicators."

---

## Stocks analysed
TCS · Infosys · HDFC Bank · ICICI Bank · Reliance · Nifty 50 (benchmark)
