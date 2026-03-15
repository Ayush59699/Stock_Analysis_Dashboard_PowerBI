import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

REQUIRED = ["AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_API_VERSION"]

missing = [k for k in REQUIRED if not os.getenv(k)]
if missing:
    print(f"[ai] Missing .env keys: {', '.join(missing)}")
    print("[ai] Create a .env file with your Azure AI Foundry credentials.")
    sys.exit(1)


DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
EXCEL_FILE = os.path.join(DATA_DIR, "stock_analysis.xlsx")


def format_metrics(summary_df: pd.DataFrame) -> str:
    lines = []
    for _, row in summary_df.iterrows():
        ticker = row["ticker"].replace(".NS", "").replace("^", "")
        lines.append(
            f"{ticker:12s} | Price: ₹{row['current_price']:>8.1f} | "
            f"1Y Return: {row['return_1y_pct']:>6.1f}% | "
            f"RSI: {row['current_rsi']:>5.1f} | "
            f"MACD: {row['macd_signal']:8s} | "
            f"Sharpe: {row['sharpe_ratio']:>5.2f} | "
            f"Volatility: {row['annualised_volatility_pct']:>5.1f}% | "
            f"Signal: {row['signal_scorecard']}"
        )
    return "\n".join(lines)


def get_daily_summary(metrics_text: str) -> str:
    client = AzureOpenAI(
        api_key        = os.getenv("AZURE_OPENAI_KEY"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version    = os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    prompt = f"""Today's NSE equity metrics: {metrics_text}
                Write a concise daily market commentary covering:
                1. Overall market mood
                2. Standout performer and why
                3. Any warning signals (overbought/oversold/bearish)
                4. One actionable observation

                Rules: Use specific numbers. Max 150 words. No generic disclaimers."""


    response = client.chat.completions.create(
        model      = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages   = [
            {"role": "system", "content": "You are a senior equity analyst. Answer based only on the data provided."},
            {"role": "user",   "content": prompt},
        ],
        max_tokens  = 400,
        temperature = 0.3,
    )
    return response.choices[0].message.content.strip()


def main():
    if not os.path.exists(EXCEL_FILE):
        print(f"[ai] stock_analysis.xlsx not found. Run scripts/run_all.py first.")
        sys.exit(1)

    print("[ai] Reading metrics from Excel...")
    summary = pd.read_excel(EXCEL_FILE, sheet_name="summary")

    metrics_text = format_metrics(summary)

    print("[ai] Calling Azure OpenAI...\n")
    try:
        commentary = get_daily_summary(metrics_text)
    except Exception as e:
        print(f"[ai] API call failed: {e}")
        sys.exit(1)

    print("=" * 60)
    print(f"  Daily Market Commentary — {datetime.now().strftime('%d %b %Y')}")
    print("=" * 60)
    print(commentary)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
