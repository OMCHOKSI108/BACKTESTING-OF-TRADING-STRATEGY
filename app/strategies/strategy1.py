import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def strategy_1_sma_crossover(df, fast_period=9, slow_period=21, initial_balance=100000):
    """
    Strategy 1: Simple Moving Average Crossover Strategy

    Buy Signal: When fast SMA crosses above slow SMA
    Sell Signal: When fast SMA crosses below slow SMA

    Parameters:
        df: DataFrame with OHLCV data
        fast_period: Period for fast moving average (default: 9)
        slow_period: Period for slow moving average (default: 21)
        initial_balance: Initial portfolio balance

    Returns:
        dict: Strategy results with trades and metrics
    """
    logger.info(f"Running SMA Crossover Strategy (Fast: {fast_period}, Slow: {slow_period})")

    df = df.copy()

    # Calculate moving averages
    df['fast_sma'] = df['c'].rolling(window=fast_period).mean()
    df['slow_sma'] = df['c'].rolling(window=slow_period).mean()

    # Calculate crossover signals
    df['fast_above_slow'] = df['fast_sma'] > df['slow_sma']
    df['prev_fast_above_slow'] = df['fast_above_slow'].shift(1)

    # Initialize variables
    position = None  # None, 'BUY', or 'SELL'
    entry_price = 0
    entry_time = None
    trades = []
    trade_durations = []

    # Iterate through data
    for i in range(max(fast_period, slow_period), len(df)):
        current_time = df.iloc[i]['timestamp'] if 'timestamp' in df.columns else i
        current_price = df.iloc[i]['c']

        # Check for buy signal (fast crosses above slow)
        if position is None and df.iloc[i]['fast_above_slow'] and not df.iloc[i]['prev_fast_above_slow']:
            position = 'BUY'
            entry_price = current_price
            entry_time = current_time
            logger.debug(f"BUY signal at {current_time}: {current_price}")

        # Check for sell signal (fast crosses below slow)
        elif position == 'BUY' and not df.iloc[i]['fast_above_slow'] and df.iloc[i]['prev_fast_above_slow']:
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
                'type': 'BUY'
            }
            trades.append(trade)
            trade_durations.append(duration)

            position = None
            logger.debug(f"SELL signal at {exit_time}: {exit_price}, P&L: {pnl}")

    # Close any open position at the end
    if position == 'BUY':
        exit_price = df.iloc[-1]['c']
        exit_time = df.iloc[-1]['timestamp'] if 'timestamp' in df.columns else len(df)-1
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
            'type': 'BUY'
        }
        trades.append(trade)
        trade_durations.append(duration)

        logger.debug(f"Closed open position at end: {exit_price}, P&L: {pnl}")

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
            'strategy_type': 'SMA Crossover'
        }
    }

    logger.info(f"SMA Crossover strategy completed: {len(trades)} trades")
    return result