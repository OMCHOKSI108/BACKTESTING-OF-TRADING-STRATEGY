# Trading Strategy Backtester# Trading Strategy Backtester



A comprehensive web application for backtesting trading strategies across multiple markets including Forex, Indian Stocks, and US Stocks. Features advanced analytics, PDF report generation, and a modern Streamlit interface.A comprehensive web application for backtesting trading strategies across multiple markets including Forex, Indian Stocks, and US Stocks. Features advanced analytics, PDF report generation, and a modern Streamlit interface.



## Table of Contents## Table of Contents



- [Features](#features)- [Features](#features)

- [Architecture](#architecture)- [Architecture](#architecture)

- [Technical Insights](#technical-insights)- [Technical Insights](#technical-insights)

- [Quick Start](#quick-start)- [Quick Start](#quick-start)

- [Usage Workflow](#usage-workflow)- [Usage Workflow](#usage-workflow)

- [API Endpoints](#api-endpoints)- [API Endpoints](#api-endpoints)

- [Performance Metrics](#performance-metrics)- [Performance Metrics](#performance-metrics)

- [Configuration](#configuration)- [Configuration](#configuration)

- [Development](#development)- [Development](#development)

- [Sample Results](#sample-results)- [Sample Results](#sample-results)

- [Contributing](#contributing)- [Contributing](#contributing)



## Features## Features



- Multi-market support: Forex, Indian Stocks (NSE), and US Stocks- Multi-market support: Forex, Indian Stocks (NSE), and US Stocks

- Multiple timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo- Multiple timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo

- Five professional trading strategies with customizable parameters- Five professional trading strategies with customizable parameters

- Comprehensive performance metrics including Sharpe Ratio, Sortino Ratio, and Max Drawdown- Comprehensive performance metrics including Sharpe Ratio, Sortino Ratio, and Max Drawdown

- Multiple data sources: Yahoo Finance, Finnhub, Alpha Vantage- Multiple data sources: Yahoo Finance, Finnhub, Alpha Vantage

- Interactive charts and equity curve visualization- Interactive charts and equity curve visualization

- Professional PDF report generation- Professional PDF report generation

- Modern Streamlit dashboard with real-time progress- Modern Streamlit dashboard with real-time progress

- Modular Flask backend with RESTful API architecture- Modular Flask backend with RESTful API architecture

- SQLite caching for improved performance- SQLite caching for improved performance

- Docker containerization support- Docker containerization support



## Architecture## Architecture



``````

trading-backtester/trading-backtester/

├── app/├── app/

│   ├── strategies/          # Trading strategy implementations│   ├── strategies/          # Trading strategy implementations

│   │   ├── strategy1.py     # SMA Crossover Strategy│   │   ├── strategy1.py     # SMA Crossover Strategy

│   │   ├── strategy2.py     # RSI Mean Reversion Strategy│   │   ├── strategy2.py     # RSI Mean Reversion Strategy

│   │   ├── strategy3.py     # Bollinger Bands Strategy│   │   ├── strategy3.py     # Bollinger Bands Strategy

│   │   ├── strategy4.py     # MACD Crossover Strategy│   │   ├── strategy4.py     # MACD Crossover Strategy

│   │   └── strategy5.py     # Multi-Indicator Strategy│   │   └── strategy5.py     # Multi-Indicator Strategy

│   ││   │

│   ├── services/            # Core business logic│   ├── services/            # Core business logic

│   │   ├── data_service.py  # Multi-API data fetching with caching│   │   ├── data_service.py  # Multi-API data fetching with caching

│   │   ├── backtest_service.py # Strategy execution and metrics calculation│   │   ├── backtest_service.py # Strategy execution and metrics calculation

│   │   ├── report_service.py # PDF report generation│   │   ├── report_service.py # PDF report generation

│   │   └── crypto_forex_data_service.py # Advanced forex data handling│   │   └── crypto_forex_data_service.py # Advanced forex data handling

│   ││   │

│   ├── routes/              # API endpoints│   ├── routes/              # API endpoints

│   │   ├── data_routes.py   # Data gathering and management APIs│   │   ├── data_routes.py   # Data gathering and management APIs

│   │   ├── strategy_routes.py # Strategy execution APIs│   │   ├── strategy_routes.py # Strategy execution APIs

│   │   ├── report_routes.py # Report generation APIs│   │   ├── report_routes.py # Report generation APIs

│   │   └── performance_routes.py # System monitoring APIs│   │   └── performance_routes.py # System monitoring APIs

│   ││   │

│   ├── static/charts/       # Generated chart images│   ├── static/charts/       # Generated chart images

│   ├── templates/           # HTML templates (legacy)│   ├── templates/           # HTML templates (legacy)

│   ├── data/                # Data storage│   ├── data/                # Data storage

│   │   ├── raw/            # Raw API response data│   │   ├── raw/            # Raw API response data

│   │   ├── processed/      # Cleaned and standardized data│   │   ├── processed/      # Cleaned and standardized data

│   │   └── trade_history/  # Detailed trade execution logs│   │   └── trade_history/  # Detailed trade execution logs

│   └── reports/            # Generated PDF reports│   └── reports/            # Generated PDF reports

││

├── streamlit_app.py         # Modern Streamlit frontend├── streamlit_app.py         # Modern Streamlit frontend

├── app.py                   # Flask application entry point├── app.py                   # Flask application entry point

├── requirements.txt         # Python dependencies├── requirements.txt         # Python dependencies

├── Dockerfile              # Container configuration├── Dockerfile              # Container configuration

├── docker-compose.yml      # Multi-service orchestration├── docker-compose.yml      # Multi-service orchestration

└── README.md└── README.md

``````



## Technical Insights## Technical Insights



### Data Pipeline Architecture### Data Pipeline Architecture



The system implements a sophisticated multi-layer data pipeline:The system implements a sophisticated multi-layer data pipeline:



1. **Data Acquisition Layer**1. **Data Acquisition Layer**

   - Yahoo Finance: Primary source with automatic fallback   - Yahoo Finance: Primary source with automatic fallback

   - Finnhub API: Alternative forex and global market data   - Finnhub API: Alternative forex and global market data

   - Alpha Vantage: Supplementary data validation   - Alpha Vantage: Supplementary data validation

   - Currency Layer: Real-time forex rates   - Currency Layer: Real-time forex rates



2. **Data Processing Layer**2. **Data Processing Layer**

   - Standardization: All data normalized to OHLCV format   - Standardization: All data normalized to OHLCV format

   - MultiIndex Handling: Complex column structures flattened   - MultiIndex Handling: Complex column structures flattened

   - Caching Strategy: SQLite-based with TTL and market-specific bypass   - Caching Strategy: SQLite-based with TTL and market-specific bypass

   - Error Recovery: Automatic retry with exponential backoff   - Error Recovery: Automatic retry with exponential backoff



3. **Strategy Execution Engine**3. **Strategy Execution Engine**

   - Concurrent Processing: Multi-threaded backtesting   - Concurrent Processing: Multi-threaded backtesting

   - Memory Optimization: Pandas DataFrame operations   - Memory Optimization: Pandas DataFrame operations

   - Position Tracking: Real-time portfolio state management   - Position Tracking: Real-time portfolio state management

   - Risk Management: Configurable stop-loss and position sizing   - Risk Management: Configurable stop-loss and position sizing



### Performance Optimizations### Performance Optimizations



- **Caching Layer**: Multi-level caching prevents redundant API calls- **Caching Layer**: Multi-level caching prevents redundant API calls

- **Async Operations**: Concurrent data fetching improves response times- **Async Operations**: Concurrent data fetching improves response times

- **Memory Management**: DataFrame chunking for large datasets- **Memory Management**: DataFrame chunking for large datasets

- **Database Indexing**: Optimized SQLite queries for historical data- **Database Indexing**: Optimized SQLite queries for historical data



### API Design Patterns### API Design Patterns



- **Blueprint Architecture**: Modular Flask routing with URL prefixes- **Blueprint Architecture**: Modular Flask routing with URL prefixes

- **Service Layer Pattern**: Separation of business logic from API endpoints- **Service Layer Pattern**: Separation of business logic from API endpoints

- **Error Handling**: Comprehensive exception handling with proper HTTP status codes- **Error Handling**: Comprehensive exception handling with proper HTTP status codes

- **Response Standardization**: Consistent JSON response formats across all endpoints- **Response Standardization**: Consistent JSON response formats across all endpoints



## Quick Start## Quick Start



### Option 1: Docker (Recommended)### Option 1: Docker (Recommended)



```bash```bash

# Clone repository# Clone repository

git clone https://github.com/OMCHOKSI108/BACKTESTING-OF-TRADING-STRATEGY.gitgit clone https://github.com/OMCHOKSI108/BACKTESTING-OF-TRADING-STRATEGY.git

cd BACKTESTING-OF-TRADING-STRATEGYcd BACKTESTING-OF-TRADING-STRATEGY



# Start all services# Start all services

docker-compose up --builddocker-compose up --build



# Access the application# Access the application

# Frontend: http://localhost:8501# Frontend: http://localhost:8501

# Backend API: http://localhost:3000# Backend API: http://localhost:3000

``````



### Option 2: Local Development### Option 2: Local Development



```bash```bash

# Install dependencies# Install dependencies

pip install -r requirements.txtpip install -r requirements.txt



# Set up environment variables (optional)# Set up environment variables (optional)

cp .env.example .envcp .env.example .env

# Edit .env with your API keys# Edit .env with your API keys



# Run Flask backend# Run Flask backend

python app.py flaskpython app.py flask



# Run Streamlit frontend (in another terminal)# Run Streamlit frontend (in another terminal)

python app.py streamlitpython app.py streamlit



# Access the application# Access the application

# Frontend: http://localhost:8501# Frontend: http://localhost:8501

# Backend API: http://localhost:3000# Backend API: http://localhost:3000

``````



### Option 3: Direct Execution### Option 3: Direct Execution



```bash```bash

# Run both services simultaneously# Run both services simultaneously

python app.py bothpython app.py both



# Or run individual components# Or run individual components

python streamlit_app.py  # Frontend onlypython streamlit_app.py  # Frontend only

python -c "from app import create_app; app = create_app(); app.run(port=3000)"  # Backend onlypython -c "from app import create_app; app = create_app(); app.run(port=3000)"  # Backend only

``````



## Usage Workflow## Usage Workflow



1. **Data Configuration**1. **Data Configuration**

   - Select market type (Forex, Indian Stocks, US Stocks)   - Select market type (Forex, Indian Stocks, US Stocks)

   - Enter trading symbol (e.g., EURUSD, RELIANCE.NS, AAPL)   - Enter trading symbol (e.g., EURUSD, RELIANCE.NS, AAPL)

   - Choose timeframe and date range   - Choose timeframe and date range

   - Set initial portfolio balance   - Set initial portfolio balance



2. **Data Gathering**2. **Data Gathering**

   - Click "Gather Data" to fetch historical market data   - Click "Gather Data" to fetch historical market data

   - Data automatically saved to `/app/data/raw/` and `/app/data/processed/`   - Data automatically saved to `/app/data/raw/` and `/app/data/processed/`

   - Progress indicators show real-time fetching status   - Progress indicators show real-time fetching status



3. **Strategy Execution**3. **Strategy Execution**

   - Select individual strategies or run comparison analysis   - Select individual strategies or run comparison analysis

   - View live metrics including P&L, win rate, and drawdown   - View live metrics including P&L, win rate, and drawdown

   - Interactive charts display equity curves and trade signals   - Interactive charts display equity curves and trade signals



4. **Report Generation**4. **Report Generation**

   - Generate comprehensive PDF reports   - Generate comprehensive PDF reports

   - Include performance metrics, charts, and trade history   - Include performance metrics, charts, and trade history

   - Download reports for further analysis   - Download reports for further analysis



## API Endpoints## API Endpoints



### Data Management### Data Management

- `POST /api/data/gather` - Fetch and process market data- `POST /api/data/gather` - Fetch and process market data

- `GET /api/data/status` - Check data availability for symbol- `GET /api/data/status` - Check data availability for symbol

- `GET /api/data/preview` - Preview stored data with pagination- `GET /api/data/preview` - Preview stored data with pagination



### Strategy Execution### Strategy Execution

- `POST /api/strategy/run/{id}` - Execute specific strategy (1-5)- `POST /api/strategy/run/{id}` - Execute specific strategy (1-5)

- `POST /api/strategy/compare` - Compare multiple strategies simultaneously- `POST /api/strategy/compare` - Compare multiple strategies simultaneously

- `GET /api/strategy/list` - List available strategies and descriptions- `GET /api/strategy/list` - List available strategies and descriptions



### Report Generation### Report Generation

- `POST /api/report/generate` - Create PDF report for strategy results- `POST /api/report/generate` - Create PDF report for strategy results

- `POST /api/report/compare` - Generate comparison report for multiple strategies- `POST /api/report/compare` - Generate comparison report for multiple strategies

- `GET /api/report/download/{filename}` - Download generated PDF reports- `GET /api/report/download/{filename}` - Download generated PDF reports



### System Monitoring### System Monitoring

- `GET /api/performance/health` - System health check and status- `GET /api/performance/health` - System health check and status

- `GET /api/data/info` - Data service information and capabilities- `GET /api/data/info` - Data service information and capabilities

- `GET /api/strategy/info` - Strategy service information- `GET /api/strategy/info` - Strategy service information



## Performance Metrics## Performance Metrics



The system calculates comprehensive trading performance metrics:The system calculates comprehensive trading performance metrics:



- **Net Profit/Loss** - Total portfolio return in currency units- **Net Profit/Loss** - Total portfolio return in currency units

- **Gross Profit/Loss** - Sum of all winning/losing trades- **Gross Profit/Loss** - Sum of all winning/losing trades

- **Win Rate** - Percentage of profitable trades (0-100%)- **Win Rate** - Percentage of profitable trades (0-100%)

- **Profit Factor** - Gross profit divided by gross loss (>1 indicates profitability)- **Profit Factor** - Gross profit divided by gross loss (>1 indicates profitability)

- **Sharpe Ratio** - Risk-adjusted return measure (higher is better)- **Sharpe Ratio** - Risk-adjusted return measure (higher is better)

- **Sortino Ratio** - Downside risk-adjusted return (higher is better)- **Sortino Ratio** - Downside risk-adjusted return (higher is better)

- **Max Drawdown** - Largest peak-to-valley portfolio decline- **Max Drawdown** - Largest peak-to-valley portfolio decline

- **Average Trade P&L** - Mean profit/loss per trade- **Average Trade P&L** - Mean profit/loss per trade

- **Total Trades** - Number of executed trades- **Total Trades** - Number of executed trades

- **Equity Curve** - Portfolio value progression over time- **Equity Curve** - Portfolio value progression over time

- **Trade History** - Detailed log of all trade executions- **Trade History** - Detailed log of all trade executions



## Configuration## Configuration



### API Keys Setup### API Keys Setup



#### Finnhub API (Free tier available)#### Finnhub API (Free tier available)

```bash```bash

# Get API key from https://finnhub.io# Get API key from https://finnhub.io

echo "FINNHUB_API_KEY=your_finnhub_key" >> .envecho "FINNHUB_API_KEY=your_finnhub_key" >> .env

``````



#### Alpha Vantage API (Free tier available)#### Alpha Vantage API (Free tier available)

```bash```bash

# Get API key from https://www.alphavantage.co# Get API key from https://www.alphavantage.co

echo "ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key" >> .envecho "ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key" >> .env

``````



#### Yahoo Finance#### Yahoo Finance

- No API key required (free public access)- No API key required (free public access)



### Environment Variables### Environment Variables



```bash```bash

# Flask Configuration# Flask Configuration

FLASK_ENV=development  # or productionFLASK_ENV=development  # or production

SECRET_KEY=your_secret_keySECRET_KEY=your_secret_key



# API Keys# API Keys

FINNHUB_API_KEY=your_keyFINNHUB_API_KEY=your_key

ALPHA_VANTAGE_API_KEY=your_keyALPHA_VANTAGE_API_KEY=your_key



# Docker Configuration# Docker Configuration

DOCKER_ENV=false  # Set to true when running in containersDOCKER_ENV=false  # Set to true when running in containers

``````



## Development## Development



### Adding New Strategies### Adding New Strategies



1. Create new strategy file in `app/strategies/`1. Create new strategy file in `app/strategies/`

```python```python

def strategy_6_custom_strategy(df, initial_balance=100000):def strategy_6_custom_strategy(df, initial_balance=100000):

    """    """

    Custom strategy implementation    Custom strategy implementation

    Must return standardized results dictionary    Must return standardized results dictionary

    """    """

    # Strategy logic here    # Strategy logic here

    return {    return {

        "total_trades": trade_count,        "total_trades": trade_count,

        "net_profit_loss": net_pnl,        "net_profit_loss": net_pnl,

        "win_rate": win_rate,        "win_rate": win_rate,

        "trades": trade_list,        "trades": trade_list,

        "candles": processed_data        "candles": processed_data

    }    }

``````



2. Update strategy routes in `app/routes/strategy_routes.py`2. Update strategy routes in `app/routes/strategy_routes.py`

3. Add strategy mapping and update frontend interface3. Add strategy mapping and update frontend interface



### Extending Data Sources### Extending Data Sources



1. Add new data provider in `app/services/data_service.py`1. Add new data provider in `app/services/data_service.py`

2. Implement fetch method following existing patterns2. Implement fetch method following existing patterns

3. Update market type mappings and error handling3. Update market type mappings and error handling



### Custom Metrics### Custom Metrics



Modify `app/services/backtest_service.py` to add new performance calculations:Modify `app/services/backtest_service.py` to add new performance calculations:



```python```python

def calculate_custom_metric(self, trades, equity_curve):def calculate_custom_metric(self, trades, equity_curve):

    # Custom metric calculation    # Custom metric calculation

    return custom_value    return custom_value

``````



## Sample Results## Sample Results



### Strategy Performance Example### Strategy Performance Example



``````

Strategy: SMA Crossover (9/21)Strategy: SMA Crossover (9/21)

Symbol: AAPLSymbol: AAPL

Period: 2023-01-01 to 2024-01-01Period: 2023-01-01 to 2024-01-01

Initial Balance: $100,000Initial Balance: $100,000



Performance Metrics:Performance Metrics:

- Net P&L: $12,450.67- Net P&L: $12,450.67

- Win Rate: 58.3%- Win Rate: 58.3%

- Sharpe Ratio: 1.24- Sharpe Ratio: 1.24

- Max Drawdown: -$2,180.50- Max Drawdown: -$2,180.50

- Total Trades: 127- Total Trades: 127

- Profit Factor: 1.67- Profit Factor: 1.67

- Average Trade P&L: $98.04- Average Trade P&L: $98.04



Equity Curve: Available in generated PDF reportEquity Curve: Available in generated PDF report

Trade History: 127 trades logged with timestampsTrade History: 127 trades logged with timestamps

``````



### Data Processing Example### Data Processing Example



``````

Data Gathering: EURUSD (Forex)Data Gathering: EURUSD (Forex)

Timeframe: 30mTimeframe: 30m

Period: 2024-01-01 to 2024-10-18Period: 2024-01-01 to 2024-10-18



Raw Data: 10,368 candles fetchedRaw Data: 10,368 candles fetched

Processed Data: 10,368 candles standardizedProcessed Data: 10,368 candles standardized

Cache Status: Forex data bypass enabledCache Status: Forex data bypass enabled

Processing Time: 2.3 secondsProcessing Time: 2.3 seconds

Data Quality: 100% OHLCV complianceData Quality: 100% OHLCV compliance

``````



## Screenshots## Screenshots



### Main Dashboard### Main Dashboard

![Trading Strategy Backtester Main Dashboard](assets/img01.png)![Trading Strategy Backtester Main Dashboard](assets/img01.png)



### Strategy Results and Analytics### Strategy Results and Analytics

![Strategy Performance Analytics](assets/img02.png)![Strategy Performance Analytics](assets/img02.png)



## Contributing## Contributing



1. Fork the repository1. Fork the repository

2. Create a feature branch (`git checkout -b feature/new-strategy`)2. Create a feature branch (`git checkout -b feature/new-strategy`)

3. Implement changes with comprehensive tests3. Implement changes with comprehensive tests

4. Ensure all tests pass (`python -m pytest tests/`)4. Ensure all tests pass (`python -m pytest tests/`)

5. Submit a pull request with detailed description5. Submit a pull request with detailed description



### Development Guidelines### Development Guidelines



- Follow PEP 8 style guidelines- Follow PEP 8 style guidelines

- Add type hints for new functions- Add type hints for new functions

- Include comprehensive error handling- Include comprehensive error handling

- Update documentation for API changes- Update documentation for API changes

- Test with multiple market types and timeframes- Test with multiple market types and timeframes



## License## License



MIT License - see LICENSE file for details.MIT License - see LICENSE file for details.



## Acknowledgments## Acknowledgments



- Yahoo Finance for market data access- Yahoo Finance for market data access

- Finnhub for alternative data sources- Finnhub for alternative data sources

- Alpha Vantage for supplementary market data- Alpha Vantage for supplementary market data

- Streamlit for modern web interface framework- Streamlit for modern web interface framework

- Plotly for interactive data visualization- Plotly for interactive data visualization

- ReportLab for PDF report generation- ReportLab for PDF report generation

- Pandas and NumPy for data processing capabilities- Pandas and NumPy for data processing capabilities
│   │   ├── strategy_routes.py # Strategy execution
│   │   └── report_routes.py # Report generation
│   │
│   ├── static/charts/       # Generated chart images
│   ├── templates/           # HTML templates
│   ├── data/                # Data storage
│   │   ├── raw/            # Raw API data
│   │   ├── processed/      # Cleaned data
│   │   └── trade_history/  # Trade logs
│   └── reports/            # Generated PDF reports
│
├── streamlit_app.py         # Modern frontend
├── run_enhanced.py          # Enhanced app runner
├── requirements.txt         # Dependencies
└── README.md
```

---

## ⚡ Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone and run with Docker Compose
git clone <repository-url>
cd trading-backtester

# Start all services
docker-compose up --build

# Or run individual services
docker-compose up trading-backtester  # Flask API only
docker-compose up trading-ui          # Streamlit UI only
```

### Option 2: Local Development
```bash
pip install -r requirements.txt

# Run Flask API
python app.py flask

# Run Streamlit UI (in another terminal)
python app.py streamlit

# Run both (experimental)
python app.py both
```

This starts:
- **Flask Backend API:** http://localhost:5000
- **Streamlit Frontend:** http://localhost:8501

---

## 🎯 Usage Workflow

1. **Configure Inputs:**
   - Enter symbol (e.g., `RELIANCE.NS`, `EURUSD=X`, `AAPL`)
   - Select market type and timeframe
   - Set date range and initial balance

2. **Gather Data:**
   - Click "🔍 Gather Data" to fetch market data
   - Data is automatically saved to `/data/raw/` and `/data/processed/`

3. **Run Strategies:**
   - Select individual strategies or compare all
   - View real-time metrics and equity curves

4. **Generate Reports:**
   - Create PDF reports with charts and analysis
   - Download professional strategy reports

---

## 🔧 API Endpoints

### Data Management
- `POST /api/data/gather` - Fetch market data
- `GET /api/data/status` - Check data availability
- `GET /api/data/preview` - Preview stored data

### Strategy Execution
- `POST /api/strategy/run/{id}` - Run specific strategy
- `POST /api/strategy/compare` - Compare multiple strategies
- `GET /api/strategy/list` - List available strategies

### Report Generation
- `POST /api/report/generate` - Generate PDF report
- `POST /api/report/compare` - Generate comparison report
- `GET /api/report/download/{filename}` - Download reports

---

## 📈 Metrics Calculated

- **Net Profit/Loss** - Total portfolio return
- **Gross Profit/Loss** - Total winning/losing amounts
- **Win Rate** - Percentage of profitable trades
- **Profit Factor** - Gross profit divided by gross loss
- **Sharpe Ratio** - Risk-adjusted return measure
- **Sortino Ratio** - Downside risk-adjusted return
- **Max Drawdown** - Largest peak-to-valley decline
- **Average Trade P&L** - Mean profit per trade
- **Equity Curve** - Portfolio value over time
- **Trade History** - Detailed trade log with timestamps

---

## 🔑 API Keys Setup

### Finnhub (Free tier available)
1. Sign up at [finnhub.io](https://finnhub.io)
2. Get your API key from dashboard
3. Add to `.env`: `FINNHUB_API_KEY=your_key`

### Alpha Vantage (Free tier available)
1. Sign up at [alphavantage.co](https://www.alphavantages.co)
2. Get your API key
3. Add to `.env`: `ALPHA_VANTAGE_API_KEY=your_key`

### Yahoo Finance
- No API key required (free access)

---

## 🛠️ Development

### Adding New Strategies
1. Create `app/strategies/strategy6.py`
2. Implement strategy function following existing patterns
3. Add route in `strategy_routes.py`
4. Update Streamlit UI

### Customizing Metrics
Edit `backtest_service.py` to add new performance metrics.

### Data Sources
Extend `data_service.py` to add new market data providers.

---

## 📊 Sample Results

```
Strategy: SMA Crossover (9/21)
Symbol: AAPL
Period: 2023-01-01 to 2024-01-01

📈 Performance Metrics:
• Net P&L: $12,450.67
• Win Rate: 58.3%
• Sharpe Ratio: 1.24
• Max Drawdown: -$2,180.50
• Total Trades: 127
• Profit Factor: 1.67

📊 Equity Curve: Available in PDF report
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new strategies
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- **Yahoo Finance** - Primary data source
- **Finnhub** - Alternative market data
- **Alpha Vantage** - Additional data provider
- **Streamlit** - Modern web UI framework
- **Plotly** - Interactive charting
- **ReportLab** - PDF generation