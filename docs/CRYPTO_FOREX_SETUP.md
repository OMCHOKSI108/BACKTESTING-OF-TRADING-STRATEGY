# Advanced Crypto & Forex Data Configuration
## Professional Currency Layer Integration + Dual API System

## 💱 Currency Layer API Keys (Primary Forex Source)

The system now uses **Currency Layer API** as the primary source for professional forex data with dual API key rotation:

### Configured API Keys:
```
CURRENCY_LAYER_API_KEY1=f76a1f7cc3a0c38b25a0da6603973066  # Even requests
CURRENCY_LAYER_API_KEY2=9f259d42951a0e4a22628af03045cde0  # Odd requests
```

### Features:
- **Dual Key Rotation**: Odd/even request distribution for optimal performance
- **Rate Limiting**: 4-second intervals per key (1000 requests/hour per key)
- **Professional Data**: Real-time and historical forex rates
- **Automatic Fallback**: Falls back to Alpha Vantage if needed
- **Documentation**: https://docs.apilayer.com/currencylayer/docs/api-documentation

## Additional API Keys

### 1. Alpha Vantage (Forex Fallback)
```
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```
- Get free API key from: https://www.alphavantage.co/support/#api-key
- Free tier: 5 API requests per minute, 500 requests per day
- Used as fallback when Currency Layer is unavailable

### 2. Finnhub (Optional - for additional data)
```
FINNHUB_API_KEY=your_finnhub_api_key_here
```
- Get free API key from: https://finnhub.io/register
- Free tier: 60 API calls/minute

### 3. CoinGecko (No API Key Required)
- Public API used for crypto data
- Rate limit: 50 calls/minute (automatically handled)

### 4. Binance (No API Key Required) 
- Public API used for crypto data
- Rate limit: 1200 calls/minute (automatically handled)

## Supported Markets & Symbols

### Cryptocurrency
- **Primary Source**: Binance API (real-time OHLCV data)
- **Fallback Source**: CoinGecko API
- **Supported Symbols**: BTC, ETH, ADA, DOT, LINK, XRP, LTC, BCH, BNB, SOL, MATIC, AVAX, ATOM, UNI, AAVE, MKR, COMP, YFI, SNX, CRV, SUSHI, BAL, 1INCH, ALPHA, and more
- **Timeframes**: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo
- **Data Quality**: Advanced validation with OHLC consistency checks

### Forex
- **Primary Source**: Alpha Vantage API
- **Supported Pairs**: All major and minor forex pairs (EUR/USD, GBP/USD, USD/JPY, etc.)
- **Timeframes**: 1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo
- **Features**: Professional forex data with bid/ask spread handling

## Data Quality Features

### 1. Multi-Source Aggregation
- Automatically tries multiple data sources
- Selects best quality data based on scoring algorithm
- Intelligent fallback mechanisms

### 2. Advanced Data Validation
- OHLC consistency validation
- Statistical outlier detection and removal
- Missing data interpolation
- Duplicate timestamp removal

### 3. Professional Time Series Processing
- Proper resampling for different timeframes
- Financial aggregation rules (OHLC + Volume)
- Timezone handling and normalization

### 4. Caching & Performance
- SQLite-based intelligent caching
- Data quality scoring for cache selection
- Configurable cache expiration

### 5. Error Handling & Logging
- Comprehensive error handling for API failures
- Detailed logging for debugging
- Graceful degradation on data source failures

## Example Usage

### Crypto Data
```python
# Gather Bitcoin daily data for last 30 days
data = advanced_crypto_forex_service.gather_advanced_data(
    symbol="BTC",
    market_type="Crypto", 
    start_date="2024-09-18",
    end_date="2024-10-18",
    timeframe="1d"
)
```

### Forex Data
```python
# Gather EUR/USD hourly data
data = advanced_crypto_forex_service.gather_advanced_data(
    symbol="EURUSD",
    market_type="Forex",
    start_date="2024-10-15", 
    end_date="2024-10-18",
    timeframe="1h"
)
```

## Data Format

All data is returned in standardized format:
- `timestamp`: DateTime index
- `o`: Opening price
- `h`: Highest price  
- `l`: Lowest price
- `c`: Closing price
- `v`: Volume (0 for forex)
- `quality_score`: Data quality metric (0.0-1.0)

## Rate Limiting

The system automatically handles rate limiting for all APIs:
- CoinGecko: 50 requests/minute
- Binance: 1200 requests/minute  
- Alpha Vantage: 5 requests/minute (free tier)
- Intelligent request spacing and retry logic

## Troubleshooting

### Common Issues

1. **"No data available"**
   - Check API key configuration
   - Verify symbol format (BTC not BTC-USD for crypto)
   - Check date range (some APIs have limitations)

2. **"Rate limit exceeded"** 
   - System will automatically retry with delays
   - Consider premium API subscriptions for higher limits

3. **"Poor data quality"**
   - System automatically selects best available source
   - Check logs for specific data quality issues

### Debug Mode
Enable detailed logging by setting:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```