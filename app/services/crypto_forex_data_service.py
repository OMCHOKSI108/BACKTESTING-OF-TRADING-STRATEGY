"""
Advanced Crypto & Forex Data Service
Senior Data Scientist & Developer Implementation

This module implements sophisticated data gathering techniques for cryptocurrency
and forex markets using multiple APIs, data validation, normalization, and
enterprise-grade caching strategies.

Key Features:
- Multi-source data aggregation (CoinGecko, Binance, Currency Layer, Alpha Vantage)
- Advanced data quality validation and cleaning
- Time-series data normalization and resampling
- Intelligent fallback mechanisms
- Professional financial data formatting
- Real-time and historical data support
- Dual API key rotation for optimal performance
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
import sqlite3
import hashlib
from functools import lru_cache
import warnings
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings("ignore")

# Import Currency Layer service
from .currency_layer_service import currency_layer_service

logger = logging.getLogger(__name__)


class AdvancedCryptoForexDataService:
    def __init__(self):
        self.cache_db_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "crypto_forex_cache.db"
        )
        self.raw_data_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "raw"
        )
        self.processed_data_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed"
        )

        # API configurations
        self.api_configs = {
            "coingecko": {
                "base_url": "https://api.coingecko.com/api/v3",
                "rate_limit": 50,  # requests per minute
                "timeout": 30,
            },
            "binance": {
                "base_url": "https://api.binance.com/api/v3",
                "rate_limit": 1200,  # requests per minute
                "timeout": 10,
            },
            "alpha_vantage": {
                "base_url": "https://www.alphavantage.co",
                "rate_limit": 5,  # requests per minute for free tier
                "timeout": 30,
            },
            "fxcm": {
                "base_url": "https://api.fxcm.com",
                "rate_limit": 100,
                "timeout": 20,
            },
        }

        # Initialize cache database
        self._init_cache_db()

        # Time interval mappings for different APIs
        self.timeframe_mappings = {
            "coingecko": {
                "1m": "1",
                "5m": "5",
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "4h": "240",
                "1d": "daily",
                "1w": "weekly",
                "1mo": "monthly",
            },
            "binance": {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "4h": "4h",
                "1d": "1d",
                "1w": "1w",
                "1mo": "1M",
            },
            "alpha_vantage": {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "60min",
                "1d": "Daily",
                "1w": "Weekly",
                "1mo": "Monthly",
            },
        }

        logger.info("Advanced Crypto & Forex Data Service initialized")

    def _init_cache_db(self):
        """Initialize advanced caching database with crypto/forex specific schema"""
        try:
            os.makedirs(os.path.dirname(self.cache_db_path), exist_ok=True)

            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS crypto_forex_cache (
                        cache_key TEXT PRIMARY KEY,
                        symbol TEXT,
                        market_type TEXT,
                        data_source TEXT,
                        timeframe TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        data_json TEXT,
                        data_quality_score REAL,
                        created_at TEXT,
                        expires_at TEXT
                    )
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_symbol_timeframe 
                    ON crypto_forex_cache(symbol, timeframe, market_type)
                """
                )

                conn.commit()
                logger.info("Crypto/Forex cache database initialized")

        except Exception as e:
            logger.error(f"Error initializing cache database: {e}")

    def _generate_cache_key(
        self,
        symbol: str,
        market_type: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        source: str,
    ) -> str:
        """Generate unique cache key for data requests"""
        key_string = (
            f"{symbol}_{market_type}_{start_date}_{end_date}_{timeframe}_{source}"
        )
        return hashlib.md5(key_string.encode()).hexdigest()

    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score based on completeness and consistency"""
        if df.empty:
            return 0.0

        score = 1.0

        # Check for missing values
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        score -= missing_ratio * 0.3

        # Check for zero or negative prices
        price_cols = ["o", "h", "l", "c"]
        for col in price_cols:
            if col in df.columns:
                invalid_prices = (df[col] <= 0).sum()
                score -= (invalid_prices / len(df)) * 0.2

        # Check OHLC consistency
        if all(col in df.columns for col in price_cols):
            # High should be >= Open, Low, Close
            consistency_issues = (
                (df["h"] < df["o"])
                | (df["h"] < df["l"])
                | (df["h"] < df["c"])
                | (df["l"] > df["o"])
                | (df["l"] > df["c"])
            ).sum()
            score -= (consistency_issues / len(df)) * 0.3

        # Check for data gaps (missing time periods)
        if "timestamp" in df.columns:
            df_sorted = df.sort_values("timestamp")
            time_diffs = pd.to_datetime(df_sorted["timestamp"]).diff()
            expected_interval = (
                time_diffs.mode()[0]
                if len(time_diffs.mode()) > 0
                else pd.Timedelta("1D")
            )
            large_gaps = (time_diffs > expected_interval * 2).sum()
            score -= (large_gaps / len(df)) * 0.2

        return max(0.0, min(1.0, score))

    async def _fetch_coingecko_data(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        """Fetch cryptocurrency data from CoinGecko API"""
        try:
            # Convert symbol to CoinGecko format (remove common suffixes)
            coin_id = (
                symbol.lower().replace("usd", "").replace("usdt", "").replace("-", "")
            )

            # Map common crypto symbols to CoinGecko IDs
            symbol_mapping = {
                "btc": "bitcoin",
                "eth": "ethereum",
                "ada": "cardano",
                "dot": "polkadot",
                "link": "chainlink",
                "xrp": "ripple",
                "ltc": "litecoin",
                "bch": "bitcoin-cash",
                "bnb": "binancecoin",
                "sol": "solana",
                "matic": "matic-network",
                "avax": "avalanche-2",
                "atom": "cosmos",
            }

            coin_id = symbol_mapping.get(coin_id, coin_id)

            # Convert dates to timestamps
            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

            url = f"{self.api_configs['coingecko']['base_url']}/coins/{coin_id}/market_chart/range"

            params = {
                "vs_currency": "usd",
                "from": start_timestamp,
                "to": end_timestamp,
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extract OHLCV data
                        prices = data.get("prices", [])
                        volumes = data.get("total_volumes", [])

                        if not prices:
                            return pd.DataFrame()

                        # Create DataFrame
                        df_data = []
                        for i, (timestamp, price) in enumerate(prices):
                            row = {
                                "timestamp": pd.to_datetime(timestamp, unit="ms"),
                                "o": price,  # CoinGecko doesn't provide OHLC, use price as approximation
                                "h": price * 1.001,  # Small approximation for high
                                "l": price * 0.999,  # Small approximation for low
                                "c": price,
                                "v": volumes[i][1] if i < len(volumes) else 0,
                            }
                            df_data.append(row)

                        df = pd.DataFrame(df_data)

                        # Resample to requested timeframe if needed
                        df = self._resample_data(df, timeframe)

                        logger.info(
                            f"Fetched {len(df)} records from CoinGecko for {symbol}"
                        )
                        return df
                    else:
                        logger.warning(
                            f"CoinGecko API returned status {response.status}"
                        )
                        return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching CoinGecko data for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_binance_data(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        """Fetch cryptocurrency data from Binance API"""
        try:
            # Convert symbol to Binance format
            binance_symbol = symbol.upper()
            if not binance_symbol.endswith("USDT") and not binance_symbol.endswith(
                "BTC"
            ):
                binance_symbol += "USDT"

            # Map timeframe
            interval = self.timeframe_mappings["binance"].get(timeframe, "1d")

            # Convert dates to milliseconds
            start_time = int(
                datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000
            )
            end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)

            url = f"{self.api_configs['binance']['base_url']}/klines"

            params = {
                "symbol": binance_symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1000,
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if not data:
                            return pd.DataFrame()

                        # Convert to DataFrame
                        df = pd.DataFrame(
                            data,
                            columns=[
                                "timestamp",
                                "o",
                                "h",
                                "l",
                                "c",
                                "v",
                                "close_time",
                                "quote_asset_volume",
                                "number_of_trades",
                                "taker_buy_base_asset_volume",
                                "taker_buy_quote_asset_volume",
                                "ignore",
                            ],
                        )

                        # Convert data types
                        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                        for col in ["o", "h", "l", "c", "v"]:
                            df[col] = pd.to_numeric(df[col], errors="coerce")

                        # Keep only required columns
                        df = df[["timestamp", "o", "h", "l", "c", "v"]].copy()

                        logger.info(
                            f"Fetched {len(df)} records from Binance for {binance_symbol}"
                        )
                        return df
                    else:
                        logger.warning(f"Binance API returned status {response.status}")
                        return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching Binance data for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_alpha_vantage_forex(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        """Fetch forex data from Alpha Vantage API"""
        try:
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                logger.warning("Alpha Vantage API key not available")
                return pd.DataFrame()

            # Parse forex pair (e.g., EURUSD -> EUR, USD)
            if len(symbol) == 6:
                from_currency = symbol[:3]
                to_currency = symbol[3:]
            else:
                # Handle symbols like EURUSD=X
                clean_symbol = symbol.replace("=X", "")
                if len(clean_symbol) == 6:
                    from_currency = clean_symbol[:3]
                    to_currency = clean_symbol[3:]
                else:
                    logger.warning(f"Invalid forex symbol format: {symbol}")
                    return pd.DataFrame()

            # Determine function based on timeframe
            if timeframe in ["1m", "5m", "15m", "30m", "1h"]:
                function = "FX_INTRADAY"
                interval = self.timeframe_mappings["alpha_vantage"].get(
                    timeframe, "1min"
                )
                params = {
                    "function": function,
                    "from_symbol": from_currency,
                    "to_symbol": to_currency,
                    "interval": interval,
                    "apikey": api_key,
                    "outputsize": "full",
                }
            else:
                function = "FX_DAILY"
                params = {
                    "function": function,
                    "from_symbol": from_currency,
                    "to_symbol": to_currency,
                    "apikey": api_key,
                    "outputsize": "full",
                }

            url = f"{self.api_configs['alpha_vantage']['base_url']}/query"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extract time series data
                        if function == "FX_INTRADAY":
                            time_series_key = f"Time Series FX ({interval})"
                        else:
                            time_series_key = "Time Series FX (Daily)"

                        if time_series_key not in data:
                            logger.warning(
                                f"No time series data found in Alpha Vantage response for {symbol}"
                            )
                            return pd.DataFrame()

                        time_series = data[time_series_key]

                        # Convert to DataFrame
                        df_data = []
                        for timestamp, values in time_series.items():
                            try:
                                row = {
                                    "timestamp": pd.to_datetime(timestamp),
                                    "o": float(values["1. open"]),
                                    "h": float(values["2. high"]),
                                    "l": float(values["3. low"]),
                                    "c": float(values["4. close"]),
                                    "v": 0,  # Forex doesn't have volume
                                }
                                df_data.append(row)
                            except (KeyError, ValueError) as e:
                                logger.debug(f"Skipping invalid data point: {e}")
                                continue

                        if not df_data:
                            return pd.DataFrame()

                        df = pd.DataFrame(df_data)
                        df = df.sort_values("timestamp").reset_index(drop=True)

                        # Filter by date range
                        start_dt = pd.to_datetime(start_date)
                        end_dt = pd.to_datetime(end_date)
                        df = df[
                            (df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)
                        ]

                        logger.info(
                            f"Fetched {len(df)} records from Alpha Vantage for {symbol}"
                        )
                        return df
                    else:
                        logger.warning(
                            f"Alpha Vantage API returned status {response.status}"
                        )
                        return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage forex data for {symbol}: {e}")
            return pd.DataFrame()

    def _resample_data(self, df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """Resample data to target timeframe using financial aggregation rules"""
        if df.empty or "timestamp" not in df.columns:
            return df

        # Map timeframes to pandas frequency strings
        freq_mapping = {
            "1m": "1T",
            "5m": "5T",
            "15m": "15T",
            "30m": "30T",
            "1h": "1H",
            "4h": "4H",
            "1d": "1D",
            "1w": "1W",
            "1mo": "1M",
        }

        freq = freq_mapping.get(target_timeframe)
        if not freq:
            return df

        try:
            df = df.set_index("timestamp")

            # Financial aggregation rules
            agg_rules = {
                "o": "first",  # Open: first value in period
                "h": "max",  # High: maximum value in period
                "l": "min",  # Low: minimum value in period
                "c": "last",  # Close: last value in period
                "v": "sum",  # Volume: sum of all values in period
            }

            # Only aggregate columns that exist
            agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}

            resampled = df.resample(freq).agg(agg_rules)
            resampled = resampled.dropna()
            resampled.reset_index(inplace=True)

            logger.debug(
                f"Resampled data from {len(df)} to {len(resampled)} records for {target_timeframe}"
            )
            return resampled

        except Exception as e:
            logger.error(f"Error resampling data: {e}")
            return df.reset_index(drop=True) if "timestamp" in df.index.names else df

    def _normalize_symbol(self, symbol: str, market_type: str) -> str:
        """Normalize symbol format for different markets"""
        symbol = symbol.upper().strip()

        if market_type == "Crypto":
            # Normalize crypto symbols: strip common quote currencies (USD, USDT)
            s = symbol
            # Prefer removing USDT first (commonly used), then USD
            if s.endswith("USDT"):
                s = s[:-4]
            elif s.endswith("USD"):
                s = s[:-3]
            # Remove separators
            s = s.replace("-", "").replace("_", "")
            symbol = s

        elif market_type == "Forex":
            # Normalize forex pairs
            symbol = symbol.replace("=X", "").replace("/", "").replace("-", "")
            if len(symbol) != 6:
                logger.warning(f"Unusual forex symbol format: {symbol}")

        return symbol

    async def fetch_crypto_data(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        """Fetch cryptocurrency data using multiple sources with fallback"""
        normalized_symbol = self._normalize_symbol(symbol, "Crypto")

        # Try multiple sources in order of preference
        sources = [
            ("binance", self._fetch_binance_data),
            ("coingecko", self._fetch_coingecko_data),
        ]

        best_data = pd.DataFrame()
        best_score = 0.0

        for source_name, fetch_func in sources:
            try:
                logger.info(
                    f"Fetching crypto data for {normalized_symbol} from {source_name}"
                )
                data = await fetch_func(
                    normalized_symbol, start_date, end_date, timeframe
                )

                if not data.empty:
                    quality_score = self._calculate_data_quality_score(data)
                    logger.info(
                        f"{source_name} data quality score: {quality_score:.2f}"
                    )

                    if quality_score > best_score:
                        best_data = data.copy()
                        best_score = quality_score

            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                continue

        if not best_data.empty:
            logger.info(
                f"Selected best crypto data source with quality score: {best_score:.2f}"
            )
        else:
            logger.warning(f"No crypto data could be fetched for {symbol}")

        return best_data

    async def fetch_forex_data(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        """
        Fetch forex data using Yahoo Finance (primary) with Currency Layer fallback
        Yahoo Finance provides extensive historical data with intraday support
        """
        normalized_symbol = self._normalize_symbol(symbol, "Forex")

        logger.info(
            f"Starting forex data fetch for {normalized_symbol} with timeframe {timeframe}"
        )

        try:
            # Primary: Yahoo Finance for extensive historical data
            logger.info(f"Attempting Yahoo Finance (primary) for {normalized_symbol}")

            data = await self._fetch_yahoo_forex(
                normalized_symbol, start_date, end_date, timeframe
            )

            logger.info(
                f"Yahoo Finance returned {len(data)} rows for {normalized_symbol}"
            )
            logger.info(f"Yahoo Finance data empty: {data.empty}")

            if not data.empty:
                logger.info(f"Yahoo Finance data columns: {list(data.columns)}")
                logger.info(f"Yahoo Finance data shape: {data.shape}")
                logger.info(f"Yahoo Finance first few rows:\n{data.head(3)}")

            if not data.empty and len(data) > 10:  # Ensure we have meaningful data
                quality_score = self._calculate_data_quality_score(data)
                logger.info(
                    f"Yahoo Finance forex data quality score: {quality_score:.2f}"
                )

                # Add source metadata
                data.attrs["source"] = "Yahoo Finance API"
                data.attrs["timeframe"] = timeframe

                logger.info(f"✅ Using Yahoo Finance data: {len(data)} candles")
                return data
            else:
                logger.warning(
                    f"Yahoo Finance returned insufficient data ({len(data)} rows), trying Currency Layer fallback"
                )  # Fallback 1: Currency Layer API with dual key rotation
            logger.info(f"Falling back to Currency Layer for {normalized_symbol}")
            data = await currency_layer_service.get_forex_data(
                normalized_symbol, start_date, end_date, timeframe
            )

            if not data.empty:
                quality_score = self._calculate_data_quality_score(data)
                logger.info(
                    f"Currency Layer forex data quality score: {quality_score:.2f}"
                )

                # Add source metadata
                data.attrs["source"] = "Currency Layer API"
                data.attrs["api_keys_used"] = "Dual rotation system"

                return data
            else:
                logger.warning(
                    f"Currency Layer returned empty data for {symbol}, trying Alpha Vantage fallback"
                )

            # Fallback 2: Alpha Vantage
            logger.info(f"Falling back to Alpha Vantage for {normalized_symbol}")
            data = await self._fetch_alpha_vantage_forex(
                normalized_symbol, start_date, end_date, timeframe
            )

            if not data.empty:
                quality_score = self._calculate_data_quality_score(data)
                logger.info(
                    f"Alpha Vantage forex data quality score: {quality_score:.2f}"
                )

                # Add source metadata
                data.attrs["source"] = "Alpha Vantage API (fallback)"

                return data
            else:
                logger.warning(
                    f"No forex data could be fetched for {symbol} from any source"
                )

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching forex data for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_yahoo_forex(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        """
        Fetch forex data from Yahoo Finance with support for intraday timeframes
        Yahoo Finance provides extensive historical data for forex pairs
        """
        try:
            # Normalize symbol for Yahoo Finance (EURUSD -> EURUSD=X)
            if not symbol.endswith("=X"):
                yahoo_symbol = f"{symbol}=X"
            else:
                yahoo_symbol = symbol

            # Convert dates to datetime
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)

            # Map timeframe to Yahoo Finance interval
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "4h": "1h",  # Yahoo doesn't have 4h, use 1h
                "1d": "1d",
                "1w": "1wk",
                "1mo": "1mo",
            }

            interval = interval_map.get(timeframe, "1d")

            # For intraday data, Yahoo Finance has limitations on date ranges
            # Split into chunks if needed for long periods with short intervals
            if timeframe in ["1m", "5m", "15m", "30m"] and (end_dt - start_dt).days > 7:
                # For intraday data, limit to 7 days per request to avoid Yahoo limits
                logger.info(f"Fetching intraday data in chunks for {yahoo_symbol}")
                all_data = []

                current_start = start_dt
                chunk_days = 7

                while current_start < end_dt:
                    current_end = min(
                        current_start + pd.Timedelta(days=chunk_days), end_dt
                    )

                    chunk_data = await self._fetch_yahoo_chunk(
                        yahoo_symbol, current_start, current_end, interval
                    )

                    if not chunk_data.empty:
                        all_data.append(chunk_data)

                    current_start = current_end
                    await asyncio.sleep(1)  # Rate limiting

                if all_data:
                    combined_data = pd.concat(all_data, ignore_index=False)
                    combined_data = combined_data[
                        ~combined_data.index.duplicated(keep="first")
                    ]
                    combined_data = combined_data.sort_index()
                    return combined_data

                return pd.DataFrame()

            else:
                # Single request for daily or short intraday periods
                return await self._fetch_yahoo_chunk(
                    yahoo_symbol, start_dt, end_dt, interval
                )

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance forex data for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_yahoo_chunk(
        self,
        symbol: str,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        interval: str,
    ) -> pd.DataFrame:
        """
        Fetch a chunk of Yahoo Finance data
        """
        try:
            # Use ThreadPoolExecutor for yfinance (synchronous)
            def fetch_data():
                import yfinance as yf

                # Yahoo Finance expects Unix timestamps
                start_unix = int(start_date.timestamp())
                end_unix = int(end_date.timestamp())

                df = yf.download(
                    symbol,
                    start=start_unix,
                    end=end_unix,
                    interval=interval,
                    progress=False,
                    prepost=False,  # Exclude pre/post market for forex
                    threads=False,  # Avoid threading issues
                )

                return df

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                df = await loop.run_in_executor(executor, fetch_data)

            if df.empty or len(df) == 0:
                logger.warning(f"No data received from Yahoo Finance for {symbol}")
                return pd.DataFrame()

            # Standardize column names - handle MultiIndex columns from Yahoo Finance
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten MultiIndex columns (e.g., ('Open', 'EURUSD=X') -> 'Open')
                df.columns = df.columns.get_level_values(0)

            # Rename to standardized format
            df = df.rename(
                columns={
                    "Open": "o",
                    "High": "h",
                    "Low": "l",
                    "Close": "c",
                    "Volume": "v",
                }
            )

            # Ensure we have all required columns
            required_cols = ["o", "h", "l", "c"]
            if not all(col in df.columns for col in required_cols):
                logger.warning(
                    f"Missing required columns in Yahoo data for {symbol}. Available: {list(df.columns)}"
                )
                return pd.DataFrame()

            # Keep only OHLCV columns
            df = df[required_cols + (["v"] if "v" in df.columns else [])]

            # Remove any rows with NaN values
            df = df.dropna()

            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            logger.info(
                f"Successfully fetched {len(df)} candles from Yahoo Finance for {symbol}"
            )
            return df

        except Exception as e:
            logger.error(f"Error fetching Yahoo chunk for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_currency_layer_forex(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        """
        Wrapper method for Currency Layer forex data fetching
        This method can be used for direct Currency Layer API calls if needed
        """
        try:
            logger.info(f"Direct Currency Layer fetch for {symbol}")
            return await currency_layer_service.get_forex_data(
                symbol, start_date, end_date, timeframe
            )
        except Exception as e:
            logger.error(f"Error in Currency Layer direct fetch: {e}")
            return pd.DataFrame()

    def validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced data validation and cleaning for financial time series"""
        if df.empty:
            return df

        initial_count = len(df)
        logger.info(f"Starting data validation with {initial_count} records")

        # Remove duplicates based on timestamp
        if "timestamp" in df.columns:
            df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
            logger.info(f"Removed {initial_count - len(df)} duplicate timestamps")

        # Validate OHLCV data types
        price_cols = ["o", "h", "l", "c"]
        for col in price_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "v" in df.columns:
            df["v"] = pd.to_numeric(df["v"], errors="coerce").fillna(0)

        # Remove rows with invalid prices
        before_price_filter = len(df)
        for col in price_cols:
            if col in df.columns:
                df = df[df[col] > 0]

        logger.info(f"Removed {before_price_filter - len(df)} rows with invalid prices")

        # OHLC consistency validation
        if all(col in df.columns for col in price_cols):
            before_consistency = len(df)

            # High should be >= Open, Low, Close
            df = df[(df["h"] >= df["o"]) & (df["h"] >= df["l"]) & (df["h"] >= df["c"])]
            # Low should be <= Open, High, Close
            df = df[(df["l"] <= df["o"]) & (df["l"] <= df["h"]) & (df["l"] <= df["c"])]

            logger.info(
                f"Removed {before_consistency - len(df)} rows with inconsistent OHLC"
            )

        # Outlier detection using statistical methods
        if "c" in df.columns and len(df) > 10:
            # Remove extreme outliers (beyond 3 standard deviations)
            close_mean = df["c"].mean()
            close_std = df["c"].std()

            lower_bound = close_mean - 3 * close_std
            upper_bound = close_mean + 3 * close_std

            before_outlier = len(df)
            df = df[(df["c"] >= lower_bound) & (df["c"] <= upper_bound)]
            logger.info(f"Removed {before_outlier - len(df)} statistical outliers")

        # Sort by timestamp
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)

        final_count = len(df)
        logger.info(
            f"Data validation completed: {final_count} records remaining ({((final_count/initial_count)*100):.1f}% retention)"
        )

        return df

    async def gather_advanced_data(
        self,
        symbol: str,
        market_type: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        """
        Main method for gathering crypto/forex data with advanced techniques

        Returns professionally formatted DataFrame with:
        - timestamp: datetime index
        - o, h, l, c: OHLC prices (standardized format)
        - v: volume (0 for forex)
        - quality_score: data quality metric
        """
        logger.info(
            f"Advanced data gathering: {symbol} ({market_type}) {timeframe} from {start_date} to {end_date}"
        )

        try:
            cache_key = self._generate_cache_key(
                symbol, market_type, start_date, end_date, timeframe, "multi"
            )

            # --- START: CONCRETE FIX ---
            # For forex, we always want to fetch fresh data from Yahoo Finance.
            # Therefore, we will intentionally skip the cache check for it.
            if market_type.lower() == "forex":
                logger.info(
                    "Forex market type detected. Skipping advanced cache to fetch fresh data from Yahoo Finance."
                )
            else:
                # For crypto, use the existing cache logic.
                cached_data = self._get_cached_data(cache_key)
                if cached_data is not None and not cached_data.empty:
                    logger.info(
                        f"Using cached data for {symbol} from advanced service cache."
                    )
                    return cached_data
            # --- END: CONCRETE FIX ---

            # The rest of the function logic continues below...
            # It will now only be reached for crypto if there is a cache miss,
            # and will ALWAYS be reached for forex.

            if market_type.lower() == "forex":
                try:
                    # Fetch fresh data from Yahoo Finance
                    fresh_data = await self._fetch_yahoo_forex(
                        symbol, start_date, end_date, timeframe
                    )
                    if not fresh_data.empty:
                        # Validate and clean data
                        cleaned_data = self.validate_and_clean_data(fresh_data)

                        if not cleaned_data.empty:
                            # Calculate quality score
                            quality_score = self._calculate_data_quality_score(
                                cleaned_data
                            )
                            cleaned_data["quality_score"] = quality_score

                            # Save the new, correct data to the cache for future use if needed
                            self._cache_data(
                                cache_key,
                                symbol,
                                market_type,
                                start_date,
                                end_date,
                                timeframe,
                                cleaned_data,
                                quality_score,
                                "multi",
                            )

                            logger.info(
                                f"Successfully gathered {len(cleaned_data)} fresh forex records for {symbol}"
                            )
                            return cleaned_data
                        else:
                            logger.warning(
                                f"No data remaining after cleaning for {symbol}"
                            )
                            return pd.DataFrame()
                    else:
                        logger.warning(
                            f"No fresh data obtained from Yahoo Finance for {symbol}"
                        )
                        return pd.DataFrame()
                except Exception as e:
                    logger.error(
                        f"Error fetching forex data from Yahoo Finance for {symbol}: {e}"
                    )
                    return pd.DataFrame()

            # Fetch data based on market type (crypto)
            if market_type.lower() == "crypto":
                raw_data = await self.fetch_crypto_data(
                    symbol, start_date, end_date, timeframe
                )
            else:
                logger.error(f"Unsupported market type: {market_type}")
                return pd.DataFrame()

            if raw_data.empty:
                logger.warning(f"No raw data obtained for {symbol}")
                return pd.DataFrame()

            # Validate and clean data
            cleaned_data = self.validate_and_clean_data(raw_data)

            if cleaned_data.empty:
                logger.warning(f"No data remaining after cleaning for {symbol}")
                return pd.DataFrame()

            # Calculate quality score
            quality_score = self._calculate_data_quality_score(cleaned_data)
            cleaned_data["quality_score"] = quality_score

            # Cache the result
            self._cache_data(
                cache_key,
                symbol,
                market_type,
                start_date,
                end_date,
                timeframe,
                cleaned_data,
                quality_score,
                "multi",
            )

            logger.info(
                f"Successfully gathered {len(cleaned_data)} records for {symbol} "
                f"(quality score: {quality_score:.2f})"
            )

            return cleaned_data

        except Exception as e:
            logger.error(f"Error in advanced data gathering for {symbol}: {e}")
            return pd.DataFrame()

    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Retrieve data from cache if not expired"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT data_json, expires_at FROM crypto_forex_cache 
                    WHERE cache_key = ? AND datetime(expires_at) > datetime('now')
                """,
                    (cache_key,),
                )

                result = cursor.fetchone()
                if result:
                    data_json, expires_at = result
                    df = pd.read_json(data_json, orient="records")
                    if "timestamp" in df.columns:
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                    return df

        except Exception as e:
            logger.error(f"Error retrieving cached data: {e}")

        return None

    def _cache_data(
        self,
        cache_key: str,
        symbol: str,
        market_type: str,
        start_date: str,
        end_date: str,
        timeframe: str,
        df: pd.DataFrame,
        quality_score: float,
        source: str,
        expire_hours: int = 24,
    ):
        """Cache data with metadata"""
        try:
            # Convert DataFrame to JSON
            df_copy = df.copy()
            if "timestamp" in df_copy.columns:
                df_copy["timestamp"] = df_copy["timestamp"].astype(str)

            data_json = df_copy.to_json(orient="records")
            expires_at = (datetime.now() + timedelta(hours=expire_hours)).isoformat()
            created_at = datetime.now().isoformat()

            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO crypto_forex_cache 
                    (cache_key, symbol, market_type, data_source, timeframe, 
                     start_date, end_date, data_json, data_quality_score, 
                     created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        cache_key,
                        symbol,
                        market_type,
                        source,
                        timeframe,
                        start_date,
                        end_date,
                        data_json,
                        quality_score,
                        created_at,
                        expires_at,
                    ),
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error caching data: {e}")

    def get_supported_crypto_symbols(self) -> List[str]:
        """Get list of supported cryptocurrency symbols"""
        return [
            "BTC",
            "ETH",
            "ADA",
            "DOT",
            "LINK",
            "XRP",
            "LTC",
            "BCH",
            "BNB",
            "SOL",
            "MATIC",
            "AVAX",
            "ATOM",
            "UNI",
            "AAVE",
            "MKR",
            "COMP",
            "YFI",
            "SNX",
            "CRV",
            "SUSHI",
            "BAL",
            "1INCH",
            "ALPHA",
        ]

    def get_supported_forex_pairs(self) -> List[str]:
        """Get list of supported forex pairs"""
        return [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "USDCHF",
            "AUDUSD",
            "USDCAD",
            "NZDUSD",
            "EURGBP",
            "EURJPY",
            "GBPJPY",
            "EURCHF",
            "EURAUD",
            "EURCAD",
            "AUDCAD",
            "GBPCHF",
            "AUDCHF",
            "CADJPY",
            "CHFJPY",
            "AUDNZD",
            "NZDCAD",
            "NZDJPY",
            "GBPAUD",
            "GBPCAD",
            "GBPNZD",
        ]


# Create instance for external use
advanced_crypto_forex_service = AdvancedCryptoForexDataService()
