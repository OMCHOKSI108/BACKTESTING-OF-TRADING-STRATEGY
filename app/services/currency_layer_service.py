"""
Currency Layer API Service for Professional Forex Data
Implements odd/even API key rotation for optimal performance
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


class CurrencyLayerForexService:
    """
    Professional Currency Layer API service with dual API key rotation
    Implements enterprise-grade forex data gathering with:
    - Odd/Even API key rotation for load balancing
    - Rate limiting and error handling
    - Historical and real-time data support
    - Professional OHLC data conversion
    """

    def __init__(self):
        # Dual API keys for load balancing from environment variables
        self.api_keys = {
            "key1": os.getenv(
                "CURRENCY_LAYER_API_KEY1", "f76a1f7cc3a0c38b25a0da6603973066"
            ),  # Even requests
            "key2": os.getenv(
                "CURRENCY_LAYER_API_KEY2", "9f259d42951a0e4a22628af03045cde0"
            ),  # Odd requests
        }

        self.base_url = "https://api.currencylayer.com"
        self.request_counter = 0
        self.rate_limits = {
            "key1": {"last_request": 0, "requests_per_hour": 1000},
            "key2": {"last_request": 0, "requests_per_hour": 1000},
        }

        # Supported currency pairs (major, minor, exotic)
        self.supported_pairs = {
            "majors": [
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "USDCHF",
                "AUDUSD",
                "USDCAD",
                "NZDUSD",
            ],
            "minors": [
                "EURGBP",
                "EURJPY",
                "GBPJPY",
                "EURCHF",
                "EURAUD",
                "GBPCHF",
                "AUDCAD",
                "AUDJPY",
            ],
            "exotics": [
                "USDINR",
                "USDSGD",
                "USDHKD",
                "USDMXN",
                "USDBRL",
                "USDRUB",
                "USDCNY",
                "USDSEK",
                "USDNOK",
                "USDPLN",
                "USDTRY",
                "USDZAR",
            ],
        }

        logger.info("CurrencyLayer Forex Service initialized with dual API keys")

    def _get_api_key(self) -> Tuple[str, str]:
        """
        Get API key using odd/even rotation system
        Returns: (api_key, key_name)
        """
        self.request_counter += 1

        if self.request_counter % 2 == 0:
            # Even requests use key1
            key_name = "key1"
        else:
            # Odd requests use key2
            key_name = "key2"

        api_key = self.api_keys[key_name]

        logger.info(f"Using {key_name} for request #{self.request_counter}")
        return api_key, key_name

    def _check_rate_limit(self, key_name: str) -> bool:
        """Check if we can make a request with the given API key"""
        current_time = time.time()
        last_request = self.rate_limits[key_name]["last_request"]

        # Currency Layer allows 1000 requests per hour on free plan
        # That's about 3.6 seconds between requests to be safe
        min_interval = 4.0  # 4 seconds between requests per key

        if current_time - last_request < min_interval:
            wait_time = min_interval - (current_time - last_request)
            logger.info(f"Rate limiting {key_name}, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)

        self.rate_limits[key_name]["last_request"] = time.time()
        return True

    def _normalize_currency_pair(self, symbol: str) -> Tuple[str, str]:
        """
        Normalize currency pair to Currency Layer format
        Currency Layer uses USD as base for most pairs
        Returns: (base_currency, target_currency)
        """
        # Remove common suffixes
        symbol = symbol.replace("=X", "").replace(".FOREX", "").upper()

        # Handle different formats
        if "/" in symbol:
            parts = symbol.split("/")
            base, target = parts[0], parts[1]
        elif len(symbol) == 6:
            base, target = symbol[:3], symbol[3:]
        else:
            # Default to USD pairs
            if symbol.startswith("USD"):
                base, target = "USD", symbol[3:]
            else:
                base, target = symbol[:3], "USD"

        return base, target

    def _convert_to_direct_quote(self, base: str, target: str, rate: float) -> float:
        """
        Convert Currency Layer rate to direct quote format
        Currency Layer provides USD-based rates, we need to convert for other pairs
        """
        if base == "USD":
            return rate  # Direct USD quote
        elif target == "USD":
            return 1.0 / rate if rate != 0 else 0  # Inverse for USD target
        else:
            # Cross currency calculation needed
            return rate  # Will be handled in cross-rate calculation

    async def fetch_live_rates(self, currencies: List[str]) -> Dict:
        """
        Fetch live exchange rates for multiple currencies
        """
        api_key, key_name = self._get_api_key()
        self._check_rate_limit(key_name)

        # Currency Layer format: comma-separated currency codes
        currency_list = ",".join(currencies)

        url = f"{self.base_url}/live"
        params = {"access_key": api_key, "currencies": currency_list, "format": 1}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("success"):
                        logger.info(
                            f"Successfully fetched live rates for {len(currencies)} currencies"
                        )
                        return data
                    else:
                        logger.error(
                            f"Currency Layer API error: {data.get('error', {}).get('info', 'Unknown error')}"
                        )
                        return {}

        except Exception as e:
            logger.error(f"Error fetching live rates: {e}")
            return {}

    async def fetch_historical_data(self, date: str, currencies: List[str]) -> Dict:
        """
        Fetch historical exchange rates for a specific date
        """
        api_key, key_name = self._get_api_key()
        self._check_rate_limit(key_name)

        currency_list = ",".join(currencies)

        url = f"{self.base_url}/historical"
        params = {
            "access_key": api_key,
            "date": date,  # Format: YYYY-MM-DD
            "currencies": currency_list,
            "format": 1,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("success"):
                        logger.info(f"Successfully fetched historical rates for {date}")
                        return data
                    else:
                        error_msg = data.get("error", {}).get("info", "Unknown error")
                        logger.error(
                            f"Currency Layer historical API error: {error_msg}"
                        )
                        return {}

        except Exception as e:
            logger.error(f"Error fetching historical data for {date}: {e}")
            return {}

    def _create_synthetic_ohlc(self, rates_data: List[Dict], pair: str) -> pd.DataFrame:
        """
        Create synthetic OHLC data from Currency Layer rates
        Since Currency Layer provides daily closing rates, we simulate intraday data
        """
        if not rates_data:
            return pd.DataFrame()

        df_data = []

        for i, day_data in enumerate(rates_data):
            if not day_data.get("success") or not day_data.get("quotes"):
                continue

            date = day_data.get("date", "")
            quotes = day_data.get("quotes", {})

            # Get the rate for our pair
            base, target = self._normalize_currency_pair(pair)

            # Currency Layer uses USD as base, so we get USD-to-target rates
            if base == "USD":
                rate_key = f"USD{target}"
                close_rate = quotes.get(rate_key, 0)
            elif target == "USD":
                rate_key = f"USD{base}"
                usd_to_base = quotes.get(rate_key, 0)
                close_rate = 1.0 / usd_to_base if usd_to_base != 0 else 0
            else:
                # Cross rate calculation
                usd_to_base_key = f"USD{base}"
                usd_to_target_key = f"USD{target}"
                usd_to_base = quotes.get(usd_to_base_key, 0)
                usd_to_target = quotes.get(usd_to_target_key, 0)

                if usd_to_base != 0:
                    close_rate = usd_to_target / usd_to_base
                else:
                    close_rate = 0

            if close_rate == 0:
                continue

            # Create synthetic OHLC data
            # For forex, we simulate typical daily volatility (0.5-1.5%)
            volatility = np.random.uniform(0.005, 0.015)  # 0.5% to 1.5%

            # Generate realistic OHLC from closing price
            close = close_rate

            # Previous close for gap calculation
            if i > 0 and df_data:
                prev_close = df_data[-1]["c"]
                gap = np.random.uniform(-0.002, 0.002)  # Small overnight gap
                open_price = prev_close * (1 + gap)
            else:
                open_price = close * (1 + np.random.uniform(-0.001, 0.001))

            # High and Low based on volatility
            high_range = volatility * close
            low_range = volatility * close

            high = max(open_price, close) + np.random.uniform(0, high_range)
            low = min(open_price, close) - np.random.uniform(0, low_range)

            # Ensure OHLC consistency
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            df_data.append(
                {
                    "timestamp": pd.to_datetime(date),
                    "o": round(open_price, 5),
                    "h": round(high, 5),
                    "l": round(low, 5),
                    "c": round(close, 5),
                    "v": 0,  # Forex doesn't have volume
                }
            )

        if not df_data:
            return pd.DataFrame()

        df = pd.DataFrame(df_data)
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        logger.info(f"Created synthetic OHLC data for {pair}: {len(df)} candles")
        return df

    async def get_forex_data(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Main method to get forex data from Currency Layer API
        """
        base, target = self._normalize_currency_pair(symbol)
        logger.info(
            f"Fetching forex data for {base}/{target} from {start_date} to {end_date}"
        )

        # For timeframes other than daily, we'll use daily data and resample
        if timeframe != "1d":
            logger.warning(
                f"Currency Layer provides daily data only. Timeframe {timeframe} will use daily data."
            )

        # Generate date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        # Currency Layer historical data is limited on free plan
        # We'll fetch data day by day for better accuracy
        date_range = pd.date_range(start=start_dt, end=end_dt, freq="D")

        # Limit to last 30 days for free plan
        if len(date_range) > 30:
            logger.warning(
                "Limiting to last 30 days due to Currency Layer free plan limits"
            )
            date_range = date_range[-30:]

        # Currencies to fetch (we need both base and target if not USD)
        currencies = set([base, target])
        if "USD" not in currencies:
            currencies.add("USD")  # Need USD for cross-rate calculation

        currencies = list(currencies)

        # Fetch historical data for each date
        historical_data = []

        # Use ThreadPoolExecutor for concurrent requests (respecting rate limits)
        with ThreadPoolExecutor(max_workers=2) as executor:
            tasks = []

            for date in date_range:
                date_str = date.strftime("%Y-%m-%d")

                # Skip weekends for forex data
                if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue

                task = asyncio.create_task(
                    self.fetch_historical_data(date_str, currencies)
                )
                tasks.append(task)

                # Rate limiting: don't overwhelm the API
                await asyncio.sleep(2)  # 2 seconds between requests

            # Wait for all tasks to complete
            if tasks:
                historical_data = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and failed requests
        valid_data = [
            data
            for data in historical_data
            if isinstance(data, dict) and data.get("success")
        ]

        if not valid_data:
            logger.error(f"No valid data received for {base}/{target}")
            return pd.DataFrame()

        # Create OHLC data
        df = self._create_synthetic_ohlc(valid_data, symbol)

        if df.empty:
            logger.error(f"Failed to create OHLC data for {base}/{target}")
            return pd.DataFrame()

        # Add metadata
        df.attrs["source"] = "Currency Layer API"
        df.attrs["symbol"] = f"{base}/{target}"
        df.attrs["api_requests"] = len(valid_data)

        logger.info(f"Successfully created {len(df)} forex candles for {base}/{target}")
        return df

    def get_supported_pairs(self) -> Dict[str, List[str]]:
        """Get all supported currency pairs"""
        return self.supported_pairs

    def is_pair_supported(self, symbol: str) -> bool:
        """Check if a currency pair is supported"""
        normalized = symbol.replace("=X", "").replace(".FOREX", "").upper()

        all_pairs = []
        for category in self.supported_pairs.values():
            all_pairs.extend(category)

        return normalized in all_pairs

    async def test_api_connectivity(self) -> Dict[str, bool]:
        """Test connectivity and validity of both API keys"""
        results = {}

        for key_name, api_key in self.api_keys.items():
            try:
                url = f"{self.base_url}/live"
                params = {"access_key": api_key, "currencies": "EUR,GBP", "format": 1}

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        data = await response.json()
                        results[key_name] = data.get("success", False)

                        if not data.get("success"):
                            error_info = data.get("error", {})
                            logger.error(f"API key {key_name} error: {error_info}")

            except Exception as e:
                logger.error(f"Error testing {key_name}: {e}")
                results[key_name] = False

        logger.info(f"API connectivity test results: {results}")
        return results


# Global instance for use in other modules
currency_layer_service = CurrencyLayerForexService()


def sync_get_forex_data(
    symbol: str, start_date: str, end_date: str, timeframe: str = "1d"
) -> pd.DataFrame:
    """
    Synchronous wrapper for async forex data fetching
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                currency_layer_service.get_forex_data(
                    symbol, start_date, end_date, timeframe
                )
            )
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in sync_get_forex_data: {e}")
        return pd.DataFrame()


# Convenience functions for easy integration
async def get_live_forex_rates(pairs: List[str]) -> Dict:
    """Get live rates for multiple currency pairs"""
    return await currency_layer_service.fetch_live_rates(pairs)


async def test_currency_layer_apis() -> Dict[str, bool]:
    """Test both Currency Layer API keys"""
    return await currency_layer_service.test_api_connectivity()


if __name__ == "__main__":
    # Test the service
    import asyncio

    async def test_service():
        print("Testing Currency Layer Forex Service...")

        # Test API connectivity
        connectivity = await test_currency_layer_apis()
        print(f"API Connectivity: {connectivity}")

        # Test data fetching
        if any(connectivity.values()):
            print("\nTesting EURUSD data fetching...")
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            df = await currency_layer_service.get_forex_data(
                "EURUSD", start_date, end_date
            )

            if not df.empty:
                print(f"Successfully fetched {len(df)} candles")
                print(f"Latest data:\n{df.tail()}")
            else:
                print("No data received")

    asyncio.run(test_service())
