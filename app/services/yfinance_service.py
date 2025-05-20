import yfinance as yf
import pandas as pd

def get_stock_data(symbol, duration):
    # duration: '1Y', '2Y', etc. Map to yfinance period
    period_map = {
        '1Y': '1y',
        '2Y': '2y',
        '3Y': '3y',
        '5Y': '5y',
        'ALL': 'max'
    }
    yf_period = period_map.get(duration.upper(), '1y')
    df = yf.download(symbol, period=yf_period, interval='1d', progress=False)
    if df.empty:
        return pd.DataFrame()
    # Standardize columns to match previous usage
    df = df.rename(columns={
        'Open': 'o',
        'High': 'h',
        'Low': 'l',
        'Close': 'c',
        'Volume': 'v'
    })
    df = df[['o', 'h', 'l', 'c', 'v']]
    return df.reset_index(drop=True)
