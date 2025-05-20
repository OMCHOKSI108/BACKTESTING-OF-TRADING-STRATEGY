import yfinance as yf
from datetime import datetime, timedelta

print("--- Testing Yahoo Finance Candle Data for RELIANCE.NS (last 30 days) ---")
symbol = "RELIANCE.NS"
to_date = datetime.now()
from_date = to_date - timedelta(days=30)
df = yf.download(symbol, start=from_date.strftime('%Y-%m-%d'), end=to_date.strftime('%Y-%m-%d'), interval='1d', progress=False)
if not df.empty:
    print(f"Number of candles: {len(df)}")
    print(f"First close price: {df['Close'].iloc[0]}")
    print(df.head())
else:
    print("No candle data returned from Yahoo Finance for RELIANCE.NS.")