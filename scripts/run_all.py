import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

from fetch_data      import main as fetch
from compute_metrics import main as compute


if __name__ == "__main__":
    print("=" * 55)
    print(f"  NSE Stock Dashboard — Daily Refresh")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55 + "\n")

    fetch()
    compute()

    print("=" * 55)
    print(f"  All done. {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Refresh Power BI: Home → Refresh")
    print("=" * 55)
