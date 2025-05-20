import pandas as pd
import numpy as np

def compute_rsi(data, window=14):
    delta = data["c"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_vwap(df):
    return (df['c'] * df['v']).cumsum() / df['v'].cumsum()

def calculate_atr(df, period=14):
    high_low = df['h'] - df['l']
    high_close = np.abs(df['h'] - df['c'].shift())
    low_close = np.abs(df['l'] - df['c'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

def calculate_cpr(df):
    df['pivot'] = (df['h'].shift(1) + df['l'].shift(1) + df['c'].shift(1)) / 3
    df['bc'] = (df['h'].shift(1) + df['l'].shift(1)) / 2
    df['tc'] = 2 * df['pivot'] - df['bc']
    return df

def backtest_orb_strategy(df):
    df = df.copy()
    df = calculate_cpr(df)
    df['VWAP'] = calculate_vwap(df)
    df['ATR'] = calculate_atr(df)

    df['range_high'] = df['h'].rolling(window=6).max()
    df['range_low'] = df['l'].rolling(window=6).min()

    position = None
    trades = []
    pnl = []

    for i in range(6, len(df)):
        if position is None:
            if df['c'].iloc[i] > df['range_high'].iloc[i-1] and df['c'].iloc[i] > df['VWAP'].iloc[i]:
                entry = df['c'].iloc[i]
                sl = entry - df['ATR'].iloc[i]
                tgt = entry + (df['range_high'].iloc[i-1] - df['range_low'].iloc[i-1]) * 1.5
                position = ('BUY', entry, sl, tgt)
            elif df['c'].iloc[i] < df['range_low'].iloc[i-1] and df['c'].iloc[i] < df['VWAP'].iloc[i]:
                entry = df['c'].iloc[i]
                sl = entry + df['ATR'].iloc[i]
                tgt = entry - (df['range_high'].iloc[i-1] - df['range_low'].iloc[i-1]) * 1.5
                position = ('SELL', entry, sl, tgt)
        else:
            direction, entry, sl, tgt = position
            current = df['c'].iloc[i]
            if direction == 'BUY':
                if current <= sl or current >= tgt:
                    pnl.append(current - entry)
                    trades.append((float(entry), float(current)))
                    position = None
            elif direction == 'SELL':
                if current >= sl or current <= tgt:
                    pnl.append(entry - current)
                    trades.append((float(entry), float(current)))
                    position = None

    # Prepare last 100 candles for visualization
    candles = None
    if len(df) > 0:
        last = df.tail(100)
        candles = {
            'dates': last.index.strftime('%Y-%m-%d').tolist() if hasattr(last.index, 'strftime') else list(map(str, last.index)),
            'open': last['o'].astype(float).tolist(),
            'high': last['h'].astype(float).tolist(),
            'low': last['l'].astype(float).tolist(),
            'close': last['c'].astype(float).tolist(),
        }

    return {
        "total_trades": len(trades),
        "total_profit": round(sum(pnl), 2),
        "average_profit": round(sum(pnl)/len(pnl), 2) if pnl else 0,
        "trades": trades,
        "candles": candles,
    }


def backtest_strategy(df, strategy):
    df = df.copy()
    df["RSI"] = compute_rsi(df)
    position = False
    buy_price = 0
    trades = []
    pnl = []

    for i in range(1, len(df)):
        if not position and df["RSI"].iloc[i] < strategy["buy"]:
            buy_price = df["c"].iloc[i]
            position = True
        elif position and df["RSI"].iloc[i] > strategy["sell"]:
            sell_price = df["c"].iloc[i]
            profit = sell_price - buy_price
            pnl.append(profit)
            trades.append((buy_price, sell_price))
            position = False

    # Ensure all trade values are native Python floats for JSON serialization
    trades = [(float(buy), float(sell)) for buy, sell in trades]
    return {
        "total_trades": len(trades),
        "total_profit": round(sum(pnl), 2),
        "average_profit": round(sum(pnl)/len(pnl), 2) if pnl else 0,
        "trades": trades,
    }
