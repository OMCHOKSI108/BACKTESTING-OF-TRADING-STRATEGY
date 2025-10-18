# ==============================================================================
# 0. IMPORT LIBRARIES (after runtime restart)
# ==============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import quantstats as qs

# ==============================================================================
# 1. TRADE GENERATION FUNCTION (EMA Crossover with SL/TP)
# ==============================================================================
def perform_ema_backtest(data, short_window=9, long_window=15, sl_pct=0.01, tp_pct=0.03):
    """
    Performs an iterative backtest on an EMA crossover strategy with fixed SL/TP.
    """
    data['ema_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['ema_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['position_signal'] = np.where(data['ema_short'] > data['ema_long'], 1, -1)
    data['entry_signal'] = data['position_signal'].diff()

    in_position = False
    trades = []
    for i in range(len(data)):
        if not in_position and data['entry_signal'].iloc[i] == 2:
            in_position = True
            entry_price = data['Close'].iloc[i]
            stop_loss = entry_price * (1 - sl_pct)
            take_profit = entry_price * (1 + tp_pct)
            trades.append({'entry_date': data['DateTime'].iloc[i], 'entry_price': entry_price, 'trade_type': 'long', 'stop_loss': stop_loss, 'take_profit': take_profit, 'exit_date': None, 'exit_price': None, 'pnl': 0})
        elif in_position:
            exit_reason = None
            exit_price = 0
            if data['Low'].iloc[i] <= stop_loss:
                exit_price = stop_loss
                exit_reason = "Stop Loss"
            elif data['High'].iloc[i] >= take_profit:
                exit_price = take_profit
                exit_reason = "Take Profit"
            elif data['entry_signal'].iloc[i] == -2:
                exit_price = data['Close'].iloc[i]
                exit_reason = "Opposing Signal"
            if exit_reason:
                trade = trades[-1]
                trade['exit_date'] = data['DateTime'].iloc[i]
                trade['exit_price'] = exit_price
                trade['pnl'] = trade['exit_price'] - trade['entry_price']
                trade['exit_reason'] = exit_reason
                in_position = False
    return pd.DataFrame(trades)

# ==============================================================================
# 2. ROBUST REPORTING AND PLOTTING FUNCTION (using QuantStats)
# ==============================================================================
def generate_full_report(trades_df, original_data, title, initial_capital=10000.0):
    """
    Generates a full tear sheet report with robust handling for flat returns.
    """
    if trades_df.empty or trades_df['exit_date'].isna().all():
        print(f"\n--- {title} ---")
        print("No trades were completed, so no performance report can be generated.")
        return

    trades_df = trades_df.dropna(subset=['exit_date']).set_index('exit_date')
    daily_pnl = trades_df['pnl'].resample('D').sum()
    date_range = pd.date_range(start=original_data['DateTime'].min(), end=original_data['DateTime'].max(), freq='D')
    equity_curve = (initial_capital + daily_pnl.cumsum()).reindex(date_range, method='ffill')
    equity_curve.iloc[0] = initial_capital
    equity_curve = equity_curve.ffill()
    strategy_returns = equity_curve.pct_change(fill_method=None).fillna(0)
    strategy_returns.name = "Strategy"
    benchmark_data = original_data.set_index('DateTime')['Close']
    benchmark_returns = benchmark_data.pct_change(fill_method=None).fillna(0)
    benchmark_returns.name = "Benchmark"
    
    print(f"\n--- {title} ---")
    
    if strategy_returns.std() == 0:
        print("\nStrategy produced a flat return. Generating a simplified report.")
        qs.reports.basic(strategy_returns, benchmark=benchmark_returns)
    else:
        qs.reports.full(strategy_returns, benchmark=benchmark_returns)

# ==============================================================================
# 3. EXECUTION SCRIPT
# ==============================================================================
try:
    column_names = ['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    df_eurusd = pd.read_csv('/content/EURUSD15.csv', sep='\t', header=None, names=column_names)
    df_eurusd['DateTime'] = pd.to_datetime(df_eurusd['DateTime'])
    
    df_xausd = pd.read_csv('/content/XAUUSD15.csv', sep='\t', header=None, names=column_names)
    df_xausd['DateTime'] = pd.to_datetime(df_xausd['DateTime'])
    
    print("Data loaded successfully.")
    print("="*50)

    # --- Run Backtest and Generate Report for EUR/USD ---
    eurusd_trades = perform_ema_backtest(df_eurusd.copy(), sl_pct=0.005, tp_pct=0.015)
    generate_full_report(eurusd_trades, df_eurusd, title="EUR/USD EMA Crossover Performance")

    # --- Run Backtest and Generate Report for XAU/USD ---
    xausd_trades = perform_ema_backtest(df_xausd.copy(), sl_pct=0.01, tp_pct=0.03)
    generate_full_report(xausd_trades, df_xausd, title="XAU/USD EMA Crossover Performance")

except FileNotFoundError:
    print("Error: Make sure 'EURUSD15.csv' and 'XAUUSD15.csv' are in the '/content/' directory.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")