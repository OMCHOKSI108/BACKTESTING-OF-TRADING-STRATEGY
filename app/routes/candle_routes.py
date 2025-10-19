from flask import Blueprint, render_template, request, jsonify
from app.services.data_service import DataService
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

candle_bp = Blueprint("candle", __name__)
logger = logging.getLogger(__name__)

# Initialize the data service
data_service = DataService()

# Initialize the data service
data_service = DataService()


@candle_bp.route("/candle-view", methods=["GET"])
def candle_view():
    """Professional candlestick chart view with support for all timeframes"""

    # Get parameters from URL with enhanced defaults
    symbol = request.args.get("symbol", "EURUSD")
    timeframe = request.args.get("timeframe", "1d")
    market_type = request.args.get("market_type", "Forex")
    days = int(request.args.get("days", 100))

    # Validate timeframe - support all timeframes
    supported_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1mo']
    if timeframe not in supported_timeframes:
        timeframe = '1d'  # Default fallback

    # Calculate date range based on timeframe for optimal data loading
    end_date = datetime.now()

    # Adjust days based on timeframe for better performance
    timeframe_days_map = {
        '1m': min(days, 7),    # Max 7 days for 1m
        '5m': min(days, 14),   # Max 14 days for 5m
        '15m': min(days, 30),  # Max 30 days for 15m
        '30m': min(days, 60),  # Max 60 days for 30m
        '1h': min(days, 90),   # Max 90 days for 1h
        '4h': min(days, 180),  # Max 180 days for 4h
        '1d': min(days, 365),  # Max 365 days for 1d
        '1w': min(days, 730),  # Max 2 years for 1w
        '1mo': min(days, 1825) # Max 5 years for 1mo
    }

    actual_days = timeframe_days_map.get(timeframe, days)
    start_date = end_date - timedelta(days=actual_days)

    try:
        # Gather data using the data service
        df = data_service.gather_data(
            symbol=symbol,
            market_type=market_type,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            timeframe=timeframe,
        )

        if df.empty:
            # Create empty chart data for blank/white candlestick display
            empty_chart_data = {
                "dates": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": []
            }

            return render_template(
                "candle_view.html",
                error=f"No data found for {symbol} in {timeframe} timeframe. Chart will display as blank.",
                symbol=symbol,
                timeframe=timeframe,
                market_type=market_type,
                chart_data=empty_chart_data,
                latest_candle=None,
                price_change=0,
                data_count=0,
                data_quality=0,
                is_empty_chart=True
            )

        # Prepare chart data (limit to last N candles for performance)
        max_candles = 500  # Limit for performance
        last_candles = df.tail(max_candles) if len(df) > max_candles else df

        # Convert to chart format with enhanced data validation
        chart_data = {
            "dates": last_candles.index.strftime("%Y-%m-%d %H:%M:%S").tolist(),
            "open": [float(x) if pd.notna(x) else 0.0 for x in last_candles["o"]],
            "high": [float(x) if pd.notna(x) else 0.0 for x in last_candles["h"]],
            "low": [float(x) if pd.notna(x) else 0.0 for x in last_candles["l"]],
            "close": [float(x) if pd.notna(x) else 0.0 for x in last_candles["c"]],
            "volume": (
                [float(x) if pd.notna(x) else 0.0 for x in last_candles["v"]]
                if "v" in last_candles.columns
                else []
            ),
        }

        # Get latest candle data with validation
        latest_candle = last_candles.iloc[-1] if len(last_candles) > 0 else None
        previous_candle = (
            last_candles.iloc[-2] if len(last_candles) > 1 else latest_candle
        )

        # Calculate price change percentage with validation
        price_change = 0.0
        if latest_candle is not None and previous_candle is not None:
            try:
                if pd.notna(previous_candle["c"]) and previous_candle["c"] != 0:
                    price_change = (
                        ((latest_candle["c"] - previous_candle["c"]) / previous_candle["c"] * 100)
                        if pd.notna(latest_candle["c"]) else 0
                    )
            except (KeyError, TypeError, ZeroDivisionError):
                price_change = 0.0

        # Data quality score
        data_quality = calculate_data_quality(last_candles)

        return render_template(
            "candle_view.html",
            symbol=symbol,
            timeframe=timeframe,
            market_type=market_type,
            chart_data=chart_data,
            latest_candle=latest_candle,
            price_change=round(price_change, 2),
            data_count=len(last_candles),
            data_quality=round(data_quality * 100, 1),
            supported_timeframes=supported_timeframes,
            is_empty_chart=False
        )

    except Exception as e:
        logger.error(f"Error in candle_view for {symbol}: {str(e)}")

        # Return blank chart on error
        empty_chart_data = {
            "dates": [],
            "open": [],
            "high": [],
            "low": [],
            "close": [],
            "volume": []
        }

        return render_template(
            "candle_view.html",
            error=f"Error loading chart data: {str(e)}. Displaying blank chart.",
            symbol=symbol,
            timeframe=timeframe,
            market_type=market_type,
            chart_data=empty_chart_data,
            latest_candle=None,
            price_change=0,
            data_count=0,
            data_quality=0,
            supported_timeframes=supported_timeframes,
            is_empty_chart=True
        )


@candle_bp.route("/api/candle-data", methods=["POST"])
def get_candle_data():
    """API endpoint for real-time candle data updates"""

    data = request.get_json()
    symbol = data.get("symbol")
    timeframe = data.get("timeframe", "1d")
    market_type = data.get("market_type", "Forex")
    count = data.get("count", 100)

    try:
        # Calculate date range based on count and timeframe
        end_date = datetime.now()

        # Adjust days based on timeframe
        if timeframe in ["1m", "5m", "15m", "30m"]:
            days = min(count // 100, 30)  # API limitations for intraday
        elif timeframe in ["1h", "4h"]:
            days = min(count // 24, 90)
        else:
            days = count

        start_date = end_date - timedelta(days=days)

        result = data_service.gather_data(
            symbol=symbol,
            market_type=market_type,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            timeframe=timeframe,
        )

        if result.empty:
            return jsonify({"success": False, "message": f"No data found for {symbol}"})

        df = result
        last_candles = df.tail(count) if len(df) > count else df

        # Convert to chart format
        chart_data = {
            "dates": last_candles.index.strftime("%Y-%m-%d %H:%M:%S").tolist(),
            "open": last_candles["o"].astype(float).tolist(),
            "high": last_candles["h"].astype(float).tolist(),
            "low": last_candles["l"].astype(float).tolist(),
            "close": last_candles["c"].astype(float).tolist(),
            "volume": (
                last_candles["v"].astype(float).tolist()
                if "v" in last_candles.columns
                else []
            ),
        }

        # Calculate additional data
        latest_candle = last_candles.iloc[-1]
        previous_candle = (
            last_candles.iloc[-2] if len(last_candles) > 1 else latest_candle
        )
        price_change = (
            ((latest_candle["c"] - previous_candle["c"]) / previous_candle["c"] * 100)
            if previous_candle["c"] != 0
            else 0
        )

        return jsonify(
            {
                "success": True,
                "chart_data": chart_data,
                "latest_candle": {
                    "o": float(latest_candle["o"]),
                    "h": float(latest_candle["h"]),
                    "l": float(latest_candle["l"]),
                    "c": float(latest_candle["c"]),
                    "v": float(latest_candle["v"]) if "v" in latest_candle else 0,
                },
                "price_change": round(price_change, 2),
                "data_count": len(last_candles),
                "data_quality": round(calculate_data_quality(last_candles) * 100, 1),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@candle_bp.route("/api/technical-indicators", methods=["POST"])
def get_technical_indicators():
    """Calculate and return technical indicators for overlay on chart"""

    data = request.get_json()
    symbol = data.get("symbol")
    timeframe = data.get("timeframe", "1d")
    market_type = data.get("market_type", "Forex")
    indicator = data.get("indicator")  # 'ma', 'bollinger', 'rsi', etc.

    try:
        # Get data (similar to above)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=200)  # More data for indicators

        result = data_service.gather_data(
            symbol=symbol,
            market_type=market_type,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            timeframe=timeframe,
        )

        if result.empty:
            return jsonify({"success": False, "message": f"No data found for {symbol}"})

        df = result

        # Calculate indicators based on request
        indicators_data = {}

        if indicator == "ma" or indicator == "all":
            # Moving Average (20-period)
            ma20 = df["c"].rolling(window=20).mean()
            indicators_data["ma20"] = {
                "dates": df.index.strftime("%Y-%m-%d %H:%M:%S").tolist(),
                "values": ma20.fillna(0).tolist(),
            }

        if indicator == "bollinger" or indicator == "all":
            # Bollinger Bands
            ma20 = df["c"].rolling(window=20).mean()
            std20 = df["c"].rolling(window=20).std()
            upper_band = ma20 + (std20 * 2)
            lower_band = ma20 - (std20 * 2)

            indicators_data["bollinger"] = {
                "dates": df.index.strftime("%Y-%m-%d %H:%M:%S").tolist(),
                "upper": upper_band.fillna(0).tolist(),
                "middle": ma20.fillna(0).tolist(),
                "lower": lower_band.fillna(0).tolist(),
            }

        if indicator == "support_resistance" or indicator == "all":
            # Simple support/resistance levels
            recent_data = df.tail(50)
            support_level = recent_data["l"].min()
            resistance_level = recent_data["h"].max()

            indicators_data["support_resistance"] = {
                "support": float(support_level),
                "resistance": float(resistance_level),
            }

        return jsonify({"success": True, "indicators": indicators_data})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error calculating indicators: {str(e)}"}
        )


def calculate_data_quality(df):
    """Calculate data quality score"""
    if df.empty:
        return 0.0

    # Check for missing values
    missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))

    # Check for zero/invalid prices
    invalid_prices = (
        (df["o"] <= 0) | (df["h"] <= 0) | (df["l"] <= 0) | (df["c"] <= 0)
    ).sum()
    invalid_ratio = invalid_prices / len(df)

    # Check OHLC consistency
    ohlc_valid = (
        (df["h"] >= df[["o", "l", "c"]].max(axis=1))
        & (df["l"] <= df[["o", "h", "c"]].min(axis=1))
    ).sum()
    ohlc_ratio = ohlc_valid / len(df)

    # Calculate overall quality
    quality_score = (
        (1 - missing_ratio) * 0.3 + (1 - invalid_ratio) * 0.3 + ohlc_ratio * 0.4
    )

    return max(0.0, min(1.0, quality_score))
