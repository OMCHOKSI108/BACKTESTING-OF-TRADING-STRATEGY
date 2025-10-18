import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def strategy_3_bollinger_bands(df, period=20, std_dev=2, initial_balance=100000):
    """
    Strategy 3: Bollinger Bands Mean Reversion Strategy

    Buy Signal: When price touches or goes below lower Bollinger Band
    Sell Signal: When price touches or goes above upper Bollinger Band

    Parameters:
        df: DataFrame with OHLCV data
        period: Period for moving average (default: 20)
        std_dev: Standard deviation multiplier (default: 2)
        initial_balance: Initial portfolio balance

    Returns:
        dict: Strategy results with trades and metrics
    """
    logger.info(
        f"Running Bollinger Bands Strategy (Period: {period}, Std Dev: {std_dev})"
    )

    df = df.copy()

    # Calculate Bollinger Bands
    df["sma"] = df["c"].rolling(window=period).mean()
    df["std"] = df["c"].rolling(window=period).std()
    df["upper_band"] = df["sma"] + (df["std"] * std_dev)
    df["lower_band"] = df["sma"] - (df["std"] * std_dev)

    # Calculate band position (0 = lower band, 100 = upper band)
    df["band_position"] = (
        (df["c"] - df["lower_band"]) / (df["upper_band"] - df["lower_band"])
    ) * 100

    # Initialize variables
    position = None  # None, 'BUY', or 'SELL'
    entry_price = 0
    entry_time = None
    trades = []
    trade_durations = []

    # Iterate through data (skip initial calculation period)
    for i in range(period, len(df)):
        current_time = df.iloc[i]["timestamp"] if "timestamp" in df.columns else i
        current_price = df.iloc[i]["c"]
        upper_band = df.iloc[i]["upper_band"]
        lower_band = df.iloc[i]["lower_band"]
        band_pos = df.iloc[i]["band_position"]

        # Check for buy signal (price near or below lower band)
        if (
            position is None and current_price <= lower_band * 1.001
        ):  # Allow 0.1% tolerance
            position = "BUY"
            entry_price = current_price
            entry_time = current_time
            logger.debug(
                f"BUY signal at {current_time}: Price={current_price:.2f}, Lower Band={lower_band:.2f}"
            )

        # Check for sell signal (price near or above upper band)
        elif (
            position == "BUY" and current_price >= upper_band * 0.999
        ):  # Allow 0.1% tolerance
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

            trade = {
                "entry_time": str(entry_time),
                "entry_price": float(entry_price),
                "exit_time": str(exit_time),
                "exit_price": float(exit_price),
                "pnl": float(pnl),
                "duration": duration,
                "type": "BUY",
                "entry_band_pos": (
                    float(df.iloc[max(0, i - duration)]["band_position"])
                    if duration < i
                    else 0
                ),
                "exit_band_pos": float(band_pos),
            }
            trades.append(trade)
            trade_durations.append(duration)

            position = None
            logger.debug(
                f"SELL signal at {exit_time}: Price={exit_price:.2f}, Upper Band={upper_band:.2f}, P&L: {pnl}"
            )

    # Close any open position at the end
    if position == "BUY":
        exit_price = df.iloc[-1]["c"]
        exit_time = (
            df.iloc[-1]["timestamp"] if "timestamp" in df.columns else len(df) - 1
        )
        exit_band_pos = df.iloc[-1]["band_position"]
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
            "entry_band_pos": float(
                df.iloc[max(0, len(df) - duration - 1)]["band_position"]
            ),
            "exit_band_pos": float(exit_band_pos),
        }
        trades.append(trade)
        trade_durations.append(duration)

        logger.debug(
            f"Closed open position at end: Price={exit_price:.2f}, Band Pos={exit_band_pos:.2f}, P&L: {pnl}"
        )

    # Prepare results
    pnl_values = [trade["pnl"] for trade in trades]

    result = {
        "trades": trades,
        "trade_durations": trade_durations,
        "total_trades": len(trades),
        "winning_trades": len([t for t in trades if t["pnl"] > 0]),
        "losing_trades": len([t for t in trades if t["pnl"] <= 0]),
        "parameters": {
            "period": period,
            "std_dev": std_dev,
            "strategy_type": "Bollinger Bands Mean Reversion",
        },
    }

    logger.info(f"Bollinger Bands strategy completed: {len(trades)} trades")
    return result
