# This file is now deprecated. Use yfinance_service.py instead for stock data.

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

def get_finnhub_api_key():
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("[ERROR] FINNHUB_API_KEY not set in environment. Please set it in your .env file.")
    return api_key

def get_stock_data(symbol, duration):
    now = datetime.now()
    delta_map = {"1Y": 365, "2Y": 730, "3Y": 1095, "5Y": 1825, "ALL": 3650}
    days = delta_map.get(duration.upper(), 365)
    start = int((now - timedelta(days=days)).timestamp())
    end = int(now.timestamp())

    api_key = get_finnhub_api_key()
    url = f"https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": symbol,
        "resolution": "D",
        "from": start,
        "to": end,
        "token": api_key,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        r = response.json()
        if r.get("s") != "ok":
            print(f"[ERROR] Finnhub API returned status: {r.get('s', 'unknown')}. Response: {r}")
            # Print the full response for debugging
            print(f"[DEBUG] Full Finnhub response: {r}")
            return pd.DataFrame()
        df = pd.DataFrame({
            "t": pd.to_datetime(r["t"], unit="s"),
            "o": r["o"],
            "h": r["h"],
            "l": r["l"],
            "c": r["c"],
            "v": r["v"]
        })
        df.set_index("t", inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Finnhub API request failed: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return pd.DataFrame()
