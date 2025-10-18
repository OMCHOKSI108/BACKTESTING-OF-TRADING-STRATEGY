import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def compute_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def compute_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculate MACD indicator"""
    fast_ema = compute_ema(data, fast_period)
    slow_ema = compute_ema(data, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = compute_ema(macd_line, signal_period)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram

def strategy_4_macd_crossover(df, fast_period=12, slow_period=26, signal_period=9, initial_balance=100000):
    """
    Strategy 4: MACD Crossover Strategy

    Buy Signal: When MACD line crosses above signal line
    Sell Signal: When MACD line crosses below signal line

    Parameters:
        df: DataFrame with OHLCV data
        fast_period: Fast EMA period for MACD (default: 12)
        slow_period: Slow EMA period for MACD (default: 26)
        signal_period: Signal line EMA period (default: 9)
        initial_balance: Initial portfolio balance

    Returns:
        dict: Strategy results with trades and metrics
    """
    logger.info(f"Running MACD Strategy (Fast: {fast_period}, Slow: {slow_period}, Signal: {signal_period})")

    df = df.copy()

    # Calculate MACD
    df['macd_line'], df['signal_line'], df['histogram'] = compute_macd(
        df['c'], fast_period, slow_period, signal_period
    )

    # Calculate crossover signals
    df['macd_above_signal'] = df['macd_line'] > df['signal_line']
    df['prev_macd_above_signal'] = df['macd_above_signal'].shift(1)

    # Initialize variables
    position = None  # None, 'BUY', or 'SELL'
    entry_price = 0
    entry_time = None
    trades = []
    trade_durations = []

    # Iterate through data (skip initial calculation period)
    start_idx = max(fast_period, slow_period, signal_period)
    for i in range(start_idx, len(df)):
        current_time = df.iloc[i]['timestamp'] if 'timestamp' in df.columns else i
        current_price = df.iloc[i]['c']
        macd_line = df.iloc[i]['macd_line']
        signal_line = df.iloc[i]['signal_line']
        histogram = df.iloc[i]['histogram']

        # Check for buy signal (MACD crosses above signal)
        if position is None and df.iloc[i]['macd_above_signal'] and not df.iloc[i]['prev_macd_above_signal']:
            position = 'BUY'
            entry_price = current_price
            entry_time = current_time
            logger.debug(f"BUY signal at {current_time}: MACD={macd_line:.4f}, Signal={signal_line:.4f}")

        # Check for sell signal (MACD crosses below signal)
        elif position == 'BUY' and not df.iloc[i]['macd_above_signal'] and df.iloc[i]['prev_macd_above_signal']:
            exit_price = current_price
            exit_time = current_time
            pnl = exit_price - entry_price

            # Calculate trade duration
            if isinstance(entry_time, (int, float)) and isinstance(exit_time, (int, float)):
                duration = exit_time - entry_time
            else:
                duration = 1  # Default duration if timestamps are not numeric

            trade = {
                'entry_time': str(entry_time),
                'entry_price': float(entry_price),
                'exit_time': str(exit_time),
                'exit_price': float(exit_price),
                'pnl': float(pnl),
                'duration': duration,
                'type': 'BUY',
                'entry_macd': float(df.iloc[max(0, i - duration)]['macd_line']) if duration < i else 0,
                'exit_macd': float(macd_line),
                'entry_signal': float(df.iloc[max(0, i - duration)]['signal_line']) if duration < i else 0,
                'exit_signal': float(signal_line)
            }
            trades.append(trade)
            trade_durations.append(duration)

            position = None
            logger.debug(f"SELL signal at {exit_time}: MACD={macd_line:.4f}, Signal={signal_line:.4f}, P&L: {pnl}")

    # Close any open position at the end
    if position == 'BUY':
        exit_price = df.iloc[-1]['c']
        exit_time = df.iloc[-1]['timestamp'] if 'timestamp' in df.columns else len(df)-1
        exit_macd = df.iloc[-1]['macd_line']
        exit_signal = df.iloc[-1]['signal_line']
        pnl = exit_price - entry_price

        if isinstance(entry_time, (int, float)) and isinstance(exit_time, (int, float)):
            duration = exit_time - entry_time
        else:
            duration = 1

        trade = {
            'entry_time': str(entry_time),
            'entry_price': float(entry_price),
            'exit_time': str(exit_time),
            'exit_price': float(exit_price),
            'pnl': float(pnl),
            'duration': duration,
            'type': 'BUY',
            'entry_macd': float(df.iloc[max(0, len(df) - duration - 1)]['macd_line']),
            'exit_macd': float(exit_macd),
            'entry_signal': float(df.iloc[max(0, len(df) - duration - 1)]['signal_line']),
            'exit_signal': float(exit_signal)
        }
        trades.append(trade)
        trade_durations.append(duration)

        logger.debug(f"Closed open position at end: MACD={exit_macd:.4f}, Signal={exit_signal:.4f}, P&L: {pnl}")

    # Prepare results
    pnl_values = [trade['pnl'] for trade in trades]

    result = {
        'trades': trades,
        'trade_durations': trade_durations,
        'total_trades': len(trades),
        'winning_trades': len([t for t in trades if t['pnl'] > 0]),
        'losing_trades': len([t for t in trades if t['pnl'] <= 0]),
        'parameters': {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'strategy_type': 'MACD Crossover'
        }
    }

    logger.info(f"MACD strategy completed: {len(trades)} trades")
    return result