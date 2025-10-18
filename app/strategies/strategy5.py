import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def compute_rsi(data, window=14):
    """Calculate RSI indicator"""
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()


def strategy_5_multi_indicator(
    df,
    rsi_period=14,
    ema_short=9,
    ema_long=21,
    rsi_overbought=70,
    rsi_oversold=30,
    initial_balance=100000,
):
    """
    Strategy 5: Multi-Indicator Confirmation Strategy

    Uses RSI + EMA crossover for confirmation
    Buy Signal: RSI < oversold AND short EMA crosses above long EMA
    Sell Signal: RSI > overbought OR short EMA crosses below long EMA

    Parameters:
        df: DataFrame with OHLCV data
        rsi_period: Period for RSI calculation (default: 14)
        ema_short: Short EMA period (default: 9)
        ema_long: Long EMA period (default: 21)
        rsi_overbought: RSI overbought level (default: 70)
        rsi_oversold: RSI oversold level (default: 30)
        initial_balance: Initial portfolio balance

    Returns:
        dict: Strategy results with trades and metrics
    """
    logger.info(
        f"Running Multi-Indicator Strategy (RSI: {rsi_period}, EMA: {ema_short}/{ema_long})"
    )

    df = df.copy()

    # Calculate indicators
    df["rsi"] = compute_rsi(df["c"], window=rsi_period)
    df["ema_short"] = compute_ema(df["c"], ema_short)
    df["ema_long"] = compute_ema(df["c"], ema_long)

    # Calculate EMA crossover signals
    df["ema_short_above_long"] = df["ema_short"] > df["ema_long"]
    df["prev_ema_short_above_long"] = df["ema_short_above_long"].shift(1)

    # Initialize variables
    position = None  # None, 'BUY', or 'SELL'
    entry_price = 0
    entry_time = None
    trades = []
    trade_durations = []

    # Iterate through data (skip initial calculation period)
    start_idx = max(rsi_period, ema_short, ema_long)
    for i in range(start_idx, len(df)):
        current_time = df.iloc[i]["timestamp"] if "timestamp" in df.columns else i
        current_price = df.iloc[i]["c"]
        current_rsi = df.iloc[i]["rsi"]
        ema_short_val = df.iloc[i]["ema_short"]
        ema_long_val = df.iloc[i]["ema_long"]

        # Check for buy signal (RSI oversold + EMA bullish crossover)
        if (
            position is None
            and current_rsi < rsi_oversold
            and df.iloc[i]["ema_short_above_long"]
            and not df.iloc[i]["prev_ema_short_above_long"]
        ):

            position = "BUY"
            entry_price = current_price
            entry_time = current_time
            logger.debug(
                f"BUY signal at {current_time}: RSI={current_rsi:.2f}, EMA crossover"
            )

        # Check for sell signal (RSI overbought OR EMA bearish crossover)
        elif position == "BUY" and (
            current_rsi > rsi_overbought
            or (
                not df.iloc[i]["ema_short_above_long"]
                and df.iloc[i]["prev_ema_short_above_long"]
            )
        ):

            exit_price = current_price
            exit_time = current_time
            pnl = exit_price - entry_price

            # Calculate trade duration
            if isinstance(entry_time, (int, float)) and isinstance(
                exit_time, (int, float)
            ):
                duration = exit_time - entry_time
            else:
                duration = 1  # Default duration if timestamps are not numeric

            # Determine exit reason
            exit_reason = (
                "RSI_overbought" if current_rsi > rsi_overbought else "EMA_crossover"
            )

            trade = {
                "entry_time": str(entry_time),
                "entry_price": float(entry_price),
                "exit_time": str(exit_time),
                "exit_price": float(exit_price),
                "pnl": float(pnl),
                "duration": duration,
                "type": "BUY",
                "entry_rsi": (
                    float(df.iloc[max(0, i - duration)]["rsi"])
                    if duration < i
                    else current_rsi
                ),
                "exit_rsi": float(current_rsi),
                "exit_reason": exit_reason,
            }
            trades.append(trade)
            trade_durations.append(duration)

            position = None
            logger.debug(
                f"SELL signal at {exit_time}: {exit_reason}, RSI={current_rsi:.2f}, P&L: {pnl}"
            )

    # Close any open position at the end
    if position == "BUY":
        exit_price = df.iloc[-1]["c"]
        exit_time = (
            df.iloc[-1]["timestamp"] if "timestamp" in df.columns else len(df) - 1
        )
        exit_rsi = df.iloc[-1]["rsi"]
        pnl = exit_price - entry_price

        if isinstance(entry_time, (int, float)) and isinstance(exit_time, (int, float)):
            duration = exit_time - entry_time
        else:
            duration = 1

        trade = {
            "entry_time": str(entry_time),
            "entry_price": float(entry_price),
            "exit_time": str(exit_time),
            "exit_price": float(exit_price),
            "pnl": float(pnl),
            "duration": duration,
            "type": "BUY",
            "entry_rsi": float(df.iloc[max(0, len(df) - duration - 1)]["rsi"]),
            "exit_rsi": float(exit_rsi),
            "exit_reason": "end_of_data",
        }
        trades.append(trade)
        trade_durations.append(duration)

        logger.debug(f"Closed open position at end: RSI={exit_rsi:.2f}, P&L: {pnl}")

    # Prepare results
    pnl_values = [trade["pnl"] for trade in trades]

    result = {
        "trades": trades,
        "trade_durations": trade_durations,
        "total_trades": len(trades),
        "winning_trades": len([t for t in trades if t["pnl"] > 0]),
        "losing_trades": len([t for t in trades if t["pnl"] <= 0]),
        "parameters": {
            "rsi_period": rsi_period,
            "ema_short": ema_short,
            "ema_long": ema_long,
            "rsi_overbought": rsi_overbought,
            "rsi_oversold": rsi_oversold,
            "strategy_type": "Multi-Indicator (RSI + EMA)",
        },
    }

    logger.info(f"Multi-indicator strategy completed: {len(trades)} trades")
    return result
