import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import time
import threading
import concurrent.futures
from functools import lru_cache
import hashlib
import sqlite3
from queue import Queue
import asyncio
import aiohttp
from typing import List, Dict, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedDataService:
    def __init__(self, max_workers=10, cache_size=1000):
        self.raw_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
        self.processed_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
        self.cache_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache.db')
        
        os.makedirs(self.raw_data_path, exist_ok=True)
        os.makedirs(self.processed_data_path, exist_ok=True)
        
        # Performance optimizations
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.processing_queue = Queue()
        self.cache_size = cache_size
        self.rate_limiter = {}  # For API rate limiting
        
        # Initialize SQLite cache
        self._init_cache_db()
        
        logger.info(f"Enhanced DataService initialized with {max_workers} workers")

    def _init_cache_db(self):
        """Initialize SQLite database for caching"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS data_cache (
                        cache_key TEXT PRIMARY KEY,
                        symbol TEXT,
                        timeframe TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        data_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_symbol_timeframe 
                    ON data_cache(symbol, timeframe)
                ''')
                conn.commit()
                logger.info("Cache database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")

    def _generate_cache_key(self, symbol: str, start_date: str, end_date: str, timeframe: str) -> str:
        """Generate unique cache key for data requests"""
        key_string = f"{symbol}_{start_date}_{end_date}_{timeframe}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Retrieve cached data if available and not expired"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.execute('''
                    SELECT data_json FROM data_cache 
                    WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
                ''', (cache_key,))
                result = cursor.fetchone()
                
                if result:
                    import json
                    data_dict = json.loads(result[0])
                    df = pd.DataFrame(data_dict)
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                    logger.info(f"Retrieved cached data for key: {cache_key}")
                    return df
        except Exception as e:
            logger.error(f"Error retrieving cached data: {e}")
        return None

    def _cache_data(self, cache_key: str, symbol: str, timeframe: str, 
                   start_date: str, end_date: str, df: pd.DataFrame, expire_hours: int = 24):
        """Cache data with expiration"""
        try:
            # Convert DataFrame to JSON
            df_copy = df.copy()
            if df_copy.index.name == 'timestamp' or 'timestamp' in str(df_copy.index):
                df_copy.reset_index(inplace=True)
                df_copy['timestamp'] = df_copy['timestamp'].astype(str)
            
            data_json = df_copy.to_json(orient='records')
            expires_at = (datetime.now() + timedelta(hours=expire_hours)).isoformat()
            
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO data_cache 
                    (cache_key, symbol, timeframe, start_date, end_date, data_json, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (cache_key, symbol, timeframe, start_date, end_date, data_json, expires_at))
                conn.commit()
                logger.info(f"Cached data for {symbol} (expires in {expire_hours} hours)")
        except Exception as e:
            logger.error(f"Error caching data: {e}")

    def _rate_limit_check(self, api_name: str, requests_per_minute: int = 60) -> bool:
        """Check if we're within rate limits for API calls"""
        current_time = time.time()
        
        if api_name not in self.rate_limiter:
            self.rate_limiter[api_name] = []
        
        # Remove requests older than 1 minute
        self.rate_limiter[api_name] = [
            req_time for req_time in self.rate_limiter[api_name]
            if current_time - req_time < 60
        ]
        
        # Check if we can make another request
        if len(self.rate_limiter[api_name]) < requests_per_minute:
            self.rate_limiter[api_name].append(current_time)
            return True
        
        return False

    def get_api_key(self, key_name):
        """Get API key from environment variables"""
        api_key = os.getenv(key_name)
        if not api_key:
            logger.warning(f"{key_name} not set in environment variables")
        return api_key

    def fetch_yahoo_data(self, symbol, start_date, end_date, timeframe='1d'):
        """Enhanced fetch data from Yahoo Finance with caching and rate limiting"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(symbol, start_date, end_date, timeframe)
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached data for {symbol}")
                return cached_data

            # Rate limiting check
            if not self._rate_limit_check('yahoo', requests_per_minute=200):
                logger.warning(f"Rate limit exceeded for Yahoo Finance, queuing request for {symbol}")
                time.sleep(0.5)

            logger.info(f"Fetching Yahoo Finance data for {symbol} from {start_date} to {end_date}")

            # Map timeframe to yfinance interval
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m', '45m': '45m',
                '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1wk', '1mo': '1mo'
            }
            interval = interval_map.get(timeframe, '1d')

            # Let yfinance handle session management (required for newer versions)
            df = yf.download(
                symbol, 
                start=start_date, 
                end=end_date, 
                interval=interval, 
                progress=False,
                timeout=30,
                auto_adjust=True  # Explicitly set to avoid FutureWarning
            )

            if df.empty:
                logger.warning(f"No data returned from Yahoo Finance for {symbol}")
                return pd.DataFrame()

            # Flatten multi-level column headers if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Standardize columns
            df = df.rename(columns={
                'Open': 'o', 'High': 'h', 'Low': 'l', 'Close': 'c', 'Volume': 'v'
            })

            # Ensure we have all required columns
            required_cols = ['o', 'h', 'l', 'c', 'v']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in Yahoo data for {symbol}")
                return pd.DataFrame()

            df = df[required_cols].copy()
            df['timestamp'] = df.index
            df.reset_index(drop=True, inplace=True)

            # Cache the result
            self._cache_data(cache_key, symbol, timeframe, start_date, end_date, df)

            logger.info(f"Successfully fetched {len(df)} candles from Yahoo Finance for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_multiple_symbols_concurrent(self, symbols: List[str], start_date: str, 
                                        end_date: str, timeframe: str = '1d') -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols concurrently"""
        logger.info(f"Fetching data for {len(symbols)} symbols concurrently")
        
        results = {}
        
        def fetch_single_symbol(symbol):
            try:
                data = self.fetch_yahoo_data(symbol, start_date, end_date, timeframe)
                return symbol, data
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                return symbol, pd.DataFrame()
        
        # Use ThreadPoolExecutor for concurrent fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(fetch_single_symbol, symbol): symbol 
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol, data = future.result()
                results[symbol] = data
                logger.info(f"Completed fetching data for {symbol} ({len(data)} records)")
        
        logger.info(f"Successfully fetched data for {len(results)} symbols")
        return results

    def fetch_finnhub_data(self, symbol, start_date, end_date, timeframe='1d'):
        """Fetch data from Finnhub API"""
        try:
            api_key = self.get_api_key("FINNHUB_API_KEY")
            if not api_key:
                logger.warning("Finnhub API key not available, skipping Finnhub data fetch")
                return pd.DataFrame()

            logger.info(f"Fetching Finnhub data for {symbol} from {start_date} to {end_date}")

            # Convert dates to timestamps
            start_ts = int(pd.to_datetime(start_date).timestamp())
            end_ts = int(pd.to_datetime(end_date).timestamp())

            # Map timeframe to Finnhub resolution
            resolution_map = {
                '1m': '1', '5m': '5', '15m': '15', '30m': '30', '45m': '45',
                '1h': '60', '4h': '240', '1d': 'D', '1w': 'W', '1mo': 'M'
            }
            resolution = resolution_map.get(timeframe, 'D')

            url = "https://finnhub.io/api/v1/stock/candle"
            params = {
                "symbol": symbol,
                "resolution": resolution,
                "from": start_ts,
                "to": end_ts,
                "token": api_key,
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("s") != "ok":
                logger.warning(f"Finnhub API returned status: {data.get('s', 'unknown')}")
                return pd.DataFrame()

            df = pd.DataFrame({
                "timestamp": pd.to_datetime(data["t"], unit="s"),
                "o": data["o"],
                "h": data["h"],
                "l": data["l"],
                "c": data["c"],
                "v": data["v"]
            })

            logger.info(f"Successfully fetched {len(df)} candles from Finnhub for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching Finnhub data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_alphavantage_data(self, symbol, start_date, end_date, timeframe='1d'):
        """Fetch data from Alpha Vantage API"""
        try:
            api_key = self.get_api_key("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                logger.warning("Alpha Vantage API key not available, skipping Alpha Vantage data fetch")
                return pd.DataFrame()

            logger.info(f"Fetching Alpha Vantage data for {symbol} from {start_date} to {end_date}")

            # Alpha Vantage free tier limitations
            if timeframe in ['1m', '5m', '15m', '30m']:
                logger.warning("Alpha Vantage intraday data requires premium subscription")
                return pd.DataFrame()

            function = "TIME_SERIES_DAILY"
            url = "https://www.alphavantage.co/query"
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": api_key,
                "outputsize": "full"
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "Time Series (Daily)" not in data:
                logger.warning(f"Alpha Vantage API error: {data}")
                return pd.DataFrame()

            time_series = data["Time Series (Daily)"]
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # Filter by date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]

            # Rename columns
            df = df.rename(columns={
                '1. open': 'o', '2. high': 'h', '3. low': 'l',
                '4. close': 'c', '5. volume': 'v'
            })

            # Convert to numeric
            for col in ['o', 'h', 'l', 'c', 'v']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['timestamp'] = df.index
            df.reset_index(drop=True, inplace=True)

            logger.info(f"Successfully fetched {len(df)} candles from Alpha Vantage for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_market_data(self, symbol, market_type, start_date, end_date, timeframe='1d'):
        """
        Main method to fetch market data from multiple sources based on market type
        Returns combined and cleaned data
        """
        logger.info(f"Fetching data for {symbol} ({market_type}) from {start_date} to {end_date}")

        all_data = []

        # Try Yahoo Finance first (most reliable)
        yahoo_data = self.fetch_yahoo_data(symbol, start_date, end_date, timeframe)
        if not yahoo_data.empty:
            all_data.append(yahoo_data)

        # Try Finnhub for additional data (especially good for forex)
        if market_type == "Forex":
            finnhub_data = self.fetch_finnhub_data(symbol, start_date, end_date, timeframe)
            if not finnhub_data.empty:
                all_data.append(finnhub_data)

        # Try Alpha Vantage as backup
        av_data = self.fetch_alphavantage_data(symbol, start_date, end_date, timeframe)
        if not av_data.empty:
            all_data.append(av_data)

        # Combine data from all sources (prioritize Yahoo Finance)
        if not all_data:
            logger.error(f"No data could be fetched for {symbol}")
            return pd.DataFrame()

        if len(all_data) == 1:
            combined_df = all_data[0].copy()
            logger.info(f"Using single data source: shape={combined_df.shape}, columns={list(combined_df.columns)}")
        else:
            logger.info(f"Combining data from {len(all_data)} sources")
            for i, df in enumerate(all_data):
                logger.info(f"DataFrame {i}: shape={df.shape}, columns={list(df.columns)}")
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Combined DataFrame shape: {combined_df.shape}, columns: {list(combined_df.columns)}")

        # Ensure timestamp is datetime
        if 'timestamp' in combined_df.columns:
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
            combined_df = combined_df.dropna(subset=['timestamp'])
            logger.info(f"After timestamp conversion: {len(combined_df)} rows")
        else:
            logger.error(f"Timestamp column missing in combined data for {symbol}")
            logger.error(f"Available columns: {list(combined_df.columns)}")
            return pd.DataFrame()

        # Only do deduplication and sorting if we have multiple sources
        if len(all_data) > 1:
            combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='first')
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

        # Clean data
        combined_df = self.clean_data(combined_df)

        logger.info(f"Final data has {len(combined_df)} candles for {symbol}")
        return combined_df

    def clean_data(self, df):
        """Clean and validate the data"""
        if df.empty:
            return df

        initial_rows = len(df)
        logger.debug(f"Starting data cleaning with {initial_rows} rows")

        # Remove rows with NaN values in critical columns
        df = df.dropna(subset=['o', 'h', 'l', 'c'], how='any')
        logger.debug(f"After removing NaN in OHLC: {len(df)} rows")

        # Ensure numeric types
        numeric_cols = ['o', 'h', 'l', 'c', 'v']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Remove any remaining NaN values in OHLC
        df = df.dropna(subset=['o', 'h', 'l', 'c'])
        logger.debug(f"After numeric conversion: {len(df)} rows")

        # Basic OHLC validation (more lenient)
        # High should be >= Low
        df = df[df['h'] >= df['l']]
        
        # High should be >= Open and Close (with small tolerance for precision)
        tolerance = 0.01
        df = df[(df['h'] >= df['o'] - tolerance) & (df['h'] >= df['c'] - tolerance)]
        
        # Low should be <= Open and Close (with small tolerance)
        df = df[(df['l'] <= df['o'] + tolerance) & (df['l'] <= df['c'] + tolerance)]
        
        # Remove rows with zero or negative prices
        df = df[(df['o'] > 0) & (df['h'] > 0) & (df['l'] > 0) & (df['c'] > 0)]

        logger.debug(f"After OHLC validation: {len(df)} rows")
        
        final_rows = len(df)
        if final_rows < initial_rows:
            logger.info(f"Data cleaning removed {initial_rows - final_rows} invalid rows")

        return df.reset_index(drop=True)

    def save_raw_data(self, df, symbol, timeframe):
        """Save raw data to CSV"""
        if df.empty:
            return False

        filename = f"{symbol}_{timeframe}_{int(time.time())}.csv"
        filepath = os.path.join(self.raw_data_path, filename)

        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Saved raw data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving raw data: {str(e)}")
            return False

    def save_processed_data(self, df, symbol, timeframe):
        """Save processed/cleaned data to CSV"""
        if df.empty:
            return False

        filename = f"{symbol}_{timeframe}.csv"
        filepath = os.path.join(self.processed_data_path, filename)

        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Saved processed data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving processed data: {str(e)}")
            return False

    def load_processed_data(self, symbol, timeframe):
        """Load processed data from CSV"""
        filename = f"{symbol}_{timeframe}.csv"
        filepath = os.path.join(self.processed_data_path, filename)

        if not os.path.exists(filepath):
            return pd.DataFrame()

        try:
            df = pd.read_csv(filepath)
            # Convert timestamp back to datetime if it exists
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.dropna(subset=['timestamp'])
            logger.info(f"Loaded processed data from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading processed data: {str(e)}")
            return pd.DataFrame()

    def gather_data(self, symbol, market_type, start_date, end_date, timeframe='1d'):
        """
        Main method to gather data according to user input
        Saves raw and processed data automatically
        """
        logger.info(f"Gathering data for {symbol} ({market_type}) - {timeframe}")

        # Try to load existing processed data first
        existing_data = self.load_processed_data(symbol, timeframe)
        if not existing_data.empty:
            logger.info(f"Using existing processed data for {symbol}")
            return existing_data

        # Fetch new data
        df = self.get_market_data(symbol, market_type, start_date, end_date, timeframe)

        if df.empty:
            logger.error(f"Failed to gather data for {symbol}")
            return pd.DataFrame()

        # Save raw data
        self.save_raw_data(df, symbol, timeframe)

        # Save processed data
        self.save_processed_data(df, symbol, timeframe)

        return df

    def batch_process_symbols(self, symbol_requests: List[Dict]) -> Dict[str, Dict]:
        """
        High-performance batch processing for multiple symbol requests
        Each request should have: {symbol, market_type, start_date, end_date, timeframe}
        """
        logger.info(f"Starting batch processing for {len(symbol_requests)} symbol requests")
        
        results = {}
        
        def process_symbol_request(request):
            symbol = request['symbol']
            try:
                data = self.gather_data(
                    symbol=request['symbol'],
                    market_type=request['market_type'],
                    start_date=request['start_date'],
                    end_date=request['end_date'],
                    timeframe=request.get('timeframe', '1d')
                )
                
                return symbol, {
                    'success': True,
                    'data': data,
                    'records': len(data),
                    'message': f"Successfully processed {len(data)} records"
                }
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                return symbol, {
                    'success': False,
                    'data': pd.DataFrame(),
                    'records': 0,
                    'error': str(e)
                }
        
        # Process requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_request = {
                executor.submit(process_symbol_request, request): request['symbol'] 
                for request in symbol_requests
            }
            
            for future in concurrent.futures.as_completed(future_to_request):
                symbol, result = future.result()
                results[symbol] = result
                
                status = "✅" if result['success'] else "❌"
                logger.info(f"{status} {symbol}: {result.get('message', result.get('error', 'Unknown'))}")
        
        success_count = sum(1 for r in results.values() if r['success'])
        logger.info(f"Batch processing completed: {success_count}/{len(symbol_requests)} successful")
        
        return results

    def optimize_cache(self, max_age_hours: int = 168):  # 1 week default
        """Clean up expired cache entries to optimize performance"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                # Delete expired entries
                deleted = conn.execute('''
                    DELETE FROM data_cache 
                    WHERE expires_at < CURRENT_TIMESTAMP OR created_at < datetime('now', '-{} hours')
                '''.format(max_age_hours)).rowcount
                
                # Vacuum database to reclaim space
                conn.execute('VACUUM')
                conn.commit()
                
                logger.info(f"Cache optimized: removed {deleted} expired entries")
                return deleted
        except Exception as e:
            logger.error(f"Error optimizing cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict:
        """Get cache statistics for monitoring"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_entries,
                        COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_entries,
                        COUNT(CASE WHEN expires_at <= CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
                        COUNT(DISTINCT symbol) as unique_symbols
                    FROM data_cache
                ''')
                stats = dict(zip(['total_entries', 'active_entries', 'expired_entries', 'unique_symbols'], 
                               cursor.fetchone()))
                
                # Get cache size
                cache_size_mb = os.path.getsize(self.cache_db_path) / (1024 * 1024) if os.path.exists(self.cache_db_path) else 0
                stats['cache_size_mb'] = round(cache_size_mb, 2)
                
                return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    def clear_cache(self):
        """Clear all cached data"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute('DELETE FROM data_cache')
                conn.commit()
            
            # Reset statistics
            self.cache_hits = 0
            self.cache_misses = 0
            
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_performance_statistics(self):
        """Get performance statistics of the data service"""
        cache_stats = self.get_cache_statistics()
        
        return {
            'max_workers': self.max_workers,
            'rate_limit_per_minute': getattr(self, 'rate_limit_per_minute', 60),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': round(self.cache_hits / max(self.cache_hits + self.cache_misses, 1), 3),
            'total_requests': self.cache_hits + self.cache_misses,
            'cache_entries': cache_stats.get('total_entries', 0),
            'active_entries': cache_stats.get('active_entries', 0),
            'unique_symbols': cache_stats.get('unique_symbols', 0),
            'cache_size_mb': cache_stats.get('cache_size_mb', 0)
        }

    def _get_current_timestamp(self):
        """Get current timestamp string"""
        return datetime.now().isoformat()

    def get_multiple_stocks_data(self, symbols: List[str], timeframe: str = '1d', 
                                period: str = '1mo') -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols with enhanced concurrent processing"""
        if not symbols:
            return {}

        # Convert period to start_date and end_date
        end_date = datetime.now()
        
        if period == '1mo':
            start_date = end_date - timedelta(days=30)
        elif period == '3mo':
            start_date = end_date - timedelta(days=90)
        elif period == '6mo':
            start_date = end_date - timedelta(days=180)
        elif period == '1y':
            start_date = end_date - timedelta(days=365)
        elif period == '2y':
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 1 month

        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        logger.info(f"Fetching {len(symbols)} symbols concurrently for period {period}")
        
        results = {}
        
        def fetch_single_symbol(symbol):
            try:
                # Use the existing fetch method
                data = self.fetch_data('US Stocks', symbol, start_date_str, end_date_str, timeframe)
                return symbol, data
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                return symbol, pd.DataFrame()

        # Execute concurrent fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(fetch_single_symbol, symbol) for symbol in symbols]
            
            for future in concurrent.futures.as_completed(futures):
                symbol, data = future.result()
                results[symbol] = data
                
                if not data.empty:
                    logger.info(f"✅ Fetched {len(data)} candles for {symbol}")
                else:
                    logger.warning(f"❌ No data retrieved for {symbol}")

        return results

    def __del__(self):
        """Cleanup when service is destroyed"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
            logger.info("DataService executor shutdown completed")

# Maintain backward compatibility
DataService = EnhancedDataService