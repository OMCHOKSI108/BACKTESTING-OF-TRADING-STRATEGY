# Trading Strategy Backtester# Trading Strategy Backtester



A comprehensive web application for backtesting trading strategies across multiple markets including Forex, Indian Stocks, and US Stocks. Features advanced analytics, PDF report generation, and a modern Streamlit interface.A comprehensive web application for backtesting trading strategies across multiple markets including Forex, Indian Stocks, and US Stocks. Features advanced analytics, PDF report generation, and a modern Streamlit interface.



## Table of Contents## Table of Contents



- [Features](#features)- [Features](#features)

- [Screenshots](#screenshots)- [Screenshots](#screenshots)

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



## Screenshots## Screenshots



### Application Dashboard### Application Dashboard

![Trading Strategy Backtester Dashboard](assets/trades.png)![Trading Strategy Backtester Dashboard](assets/trades.png)

*Main application interface showing strategy selection, market configuration, and data gathering controls.**Main application interface showing strategy selection, market configuration, and data gathering controls.*



### Performance Analytics### Performance Analytics

![Performance Metrics](assets/performance.png)![Performance Metrics](assets/performance.png)

*Comprehensive performance metrics including Sharpe Ratio, Sortino Ratio, Max Drawdown, and equity curves.**Comprehensive performance metrics including Sharpe Ratio, Sortino Ratio, Max Drawdown, and equity curves.*



### Trade History Analysis### Trade History Analysis

![Trade History](assets/trade_history.png)![Trade History](assets/trade_history.png)

*Detailed trade history with P&L analysis, win/loss ratios, and trade timing information.**Detailed trade history with P&L analysis, win/loss ratios, and trade timing information.*



### Docker Deployment### Docker Deployment

![Docker Setup](assets/docker.png)![Docker Setup](assets/docker.png)

*Docker containerization setup for easy deployment and scaling.**Docker containerization setup for easy deployment and scaling.*



## Architecture## Architecture## Architecture



`````````

trading-backtester/trading-backtester/trading-backtester/

├── app/├── app/├── app/

│   ├── strategies/          # Trading strategy implementations│   ├── strategies/          # Trading strategy implementations│   ├── strategies/          # Trading strategy implementations

│   │   ├── strategy1.py     # SMA Crossover Strategy│   │   ├── strategy1.py     # SMA Crossover Strategy│   │   ├── strategy1.py     # SMA Crossover Strategy

│   │   ├── strategy2.py     # RSI Mean Reversion Strategy│   │   ├── strategy2.py     # RSI Mean Reversion Strategy│   │   ├── strategy2.py     # RSI Mean Reversion Strategy

│   │   ├── strategy3.py     # Bollinger Bands Strategy│   │   ├── strategy3.py     # Bollinger Bands Strategy│   │   ├── strategy3.py     # Bollinger Bands Strategy

│   │   ├── strategy4.py     # MACD Crossover Strategy│   │   ├── strategy4.py     # MACD Crossover Strategy│   │   ├── strategy4.py     # MACD Crossover Strategy

│   │   └── strategy5.py     # Multi-Indicator Strategy│   │   └── strategy5.py     # Multi-Indicator Strategy│   │   └── strategy5.py     # Multi-Indicator Strategy

│   ││   ││   │

│   ├── services/            # Core business logic│   ├── services/            # Core business logic│   ├── services/            # Core business logic

│   │   ├── data_service.py  # Multi-API data fetching with caching│   │   ├── data_service.py  # Multi-API data fetching with caching│   │   ├── data_service.py  # Multi-API data fetching with caching

│   │   ├── backtest_service.py # Strategy execution and metrics calculation│   │   ├── backtest_service.py # Strategy execution and metrics calculation│   │   ├── backtest_service.py # Strategy execution and metrics calculation

│   │   ├── report_service.py # PDF report generation│   │   ├── report_service.py # PDF report generation│   │   ├── report_service.py # PDF report generation

│   │   └── crypto_forex_data_service.py # Advanced forex data handling│   │   └── crypto_forex_data_service.py # Advanced forex data handling│   │   └── crypto_forex_data_service.py # Advanced forex data handling

│   ││   ││   │

│   ├── routes/              # API endpoints│   ├── routes/              # API endpoints│   ├── routes/              # API endpoints

│   │   ├── data_routes.py   # Data gathering and management APIs│   │   ├── data_routes.py   # Data gathering and management APIs│   │   ├── data_routes.py   # Data gathering and management APIs

│   │   ├── strategy_routes.py # Strategy execution APIs│   │   ├── strategy_routes.py # Strategy execution APIs│   │   ├── strategy_routes.py # Strategy execution APIs

│   │   ├── report_routes.py # Report generation APIs│   │   ├── report_routes.py # Report generation APIs│   │   ├── report_routes.py # Report generation APIs

│   │   └── performance_routes.py # System monitoring APIs│   │   └── performance_routes.py # System monitoring APIs│   │   └── performance_routes.py # System monitoring APIs

│   ││   ││   │

│   ├── static/charts/       # Generated chart images│   ├── static/charts/       # Generated chart images│   ├── static/charts/       # Generated chart images

│   ├── templates/           # HTML templates (legacy)│   ├── templates/           # HTML templates (legacy)│   ├── templates/           # HTML templates (legacy)

│   ├── data/                # Data storage│   ├── data/                # Data storage│   ├── data/                # Data storage

│   │   ├── raw/            # Raw API response data│   │   ├── raw/            # Raw API response data│   │   ├── raw/            # Raw API response data

│   │   ├── processed/      # Cleaned and standardized data│   │   ├── processed/      # Cleaned and standardized data│   │   ├── processed/      # Cleaned and standardized data

│   │   └── trade_history/  # Detailed trade execution logs│   │   └── trade_history/  # Detailed trade execution logs│   │   └── trade_history/  # Detailed trade execution logs

│   └── reports/            # Generated PDF reports│   └── reports/            # Generated PDF reports│   └── reports/            # Generated PDF reports

│││

├── streamlit_app.py         # Modern Streamlit frontend├── streamlit_app.py         # Modern Streamlit frontend├── streamlit_app.py         # Modern Streamlit frontend

├── app.py                   # Flask application entry point├── app.py                   # Flask application entry point├── app.py                   # Flask application entry point

├── requirements.txt         # Python dependencies├── requirements.txt         # Python dependencies├── requirements.txt         # Python dependencies

├── Dockerfile              # Container configuration├── Dockerfile              # Container configuration├── Dockerfile              # Container configuration

├── docker-compose.yml      # Multi-service orchestration├── docker-compose.yml      # Multi-service orchestration├── docker-compose.yml      # Multi-service orchestration

└── README.md└── README.md└── README.md

`````````



## Technical Insights## Technical Insights## Technical Insights



### Data Pipeline Architecture### Data Pipeline Architecture### Data Pipeline Architecture



The system implements a sophisticated multi-layer data pipeline:The system implements a sophisticated multi-layer data pipeline:The system implements a sophisticated multi-layer data pipeline:



1. **Data Acquisition Layer**1. **Data Acquisition Layer**1. **Data Acquisition Layer**

   - Yahoo Finance: Primary source with automatic fallback   - Yahoo Finance: Primary source with automatic fallback   - Yahoo Finance: Primary source with automatic fallback

   - Finnhub API: Alternative forex and global market data   - Finnhub API: Alternative forex and global market data   - Finnhub API: Alternative forex and global market data

   - Alpha Vantage: Supplementary data validation   - Alpha Vantage: Supplementary data validation   - Alpha Vantage: Supplementary data validation

   - Currency Layer: Real-time forex rates   - Currency Layer: Real-time forex rates   - Currency Layer: Real-time forex rates



2. **Data Processing Layer**2. **Data Processing Layer**2. **Data Processing Layer**

   - Standardization: All data normalized to OHLCV format   - Standardization: All data normalized to OHLCV format   - Standardization: All data normalized to OHLCV format

   - MultiIndex Handling: Complex column structures flattened   - MultiIndex Handling: Complex column structures flattened   - MultiIndex Handling: Complex column structures flattened

   - Caching Strategy: SQLite-based with TTL and market-specific bypass   - Caching Strategy: SQLite-based with TTL and market-specific bypass   - Caching Strategy: SQLite-based with TTL and market-specific bypass

   - Error Recovery: Automatic retry with exponential backoff   - Error Recovery: Automatic retry with exponential backoff   - Error Recovery: Automatic retry with exponential backoff



3. **Strategy Execution Engine**3. **Strategy Execution Engine**3. **Strategy Execution Engine**

   - Concurrent Processing: Multi-threaded backtesting   - Concurrent Processing: Multi-threaded backtesting   - Concurrent Processing: Multi-threaded backtesting

   - Memory Optimization: Pandas DataFrame operations   - Memory Optimization: Pandas DataFrame operations   - Memory Optimization: Pandas DataFrame operations

   - Position Tracking: Real-time portfolio state management   - Position Tracking: Real-time portfolio state management   - Position Tracking: Real-time portfolio state management

   - Risk Management: Configurable stop-loss and position sizing   - Risk Management: Configurable stop-loss and position sizing   - Risk Management: Configurable stop-loss and position sizing



### Performance Optimizations### Performance Optimizations### Performance Optimizations



- **Caching Layer**: Multi-level caching prevents redundant API calls- **Caching Layer**: Multi-level caching prevents redundant API calls- **Caching Layer**: Multi-level caching prevents redundant API calls

- **Async Operations**: Concurrent data fetching improves response times- **Async Operations**: Concurrent data fetching improves response times- **Async Operations**: Concurrent data fetching improves response times

- **Memory Management**: DataFrame chunking for large datasets- **Memory Management**: DataFrame chunking for large datasets- **Memory Management**: DataFrame chunking for large datasets

- **Database Indexing**: Optimized queries for historical data retrieval- **Database Indexing**: Optimized SQLite queries for historical data- **Database Indexing**: Optimized SQLite queries for historical data

- **Connection Pooling**: Efficient API connection management

### API Design Patterns### API Design Patterns

### API Design Patterns

- **Blueprint Architecture**: Modular Flask routing with URL prefixes- **Blueprint Architecture**: Modular Flask routing with URL prefixes

- **RESTful Endpoints**: Consistent HTTP method usage- **Service Layer Pattern**: Separation of business logic from API endpoints- **Service Layer Pattern**: Separation of business logic from API endpoints

- **Error Handling**: Comprehensive exception management with meaningful messages- **Error Handling**: Comprehensive exception handling with proper HTTP status codes- **Error Handling**: Comprehensive exception handling with proper HTTP status codes

- **Rate Limiting**: Built-in protection against API quota exhaustion- **Response Standardization**: Consistent JSON response formats across all endpoints- **Response Standardization**: Consistent JSON response formats across all endpoints

- **Response Caching**: Intelligent caching with configurable TTL

- **Health Checks**: System monitoring and diagnostic endpoints## Quick Start## Quick Start



## Quick Start### Option 1: Docker (Recommended)### Option 1: Docker (Recommended)



### Option 1: Docker (Recommended)```bash```bash

# Clone repository# Clone repository

```bashgit clone https://github.com/OMCHOKSI108/BACKTESTING-OF-TRADING-STRATEGY.git

# Clone the repositorycd BACKTESTING-OF-TRADING-STRATEGYcd BACKTESTING-OF-TRADING-STRATEGY

git clone https://github.com/OMCHOKSI108/BACKTESTING-OF-TRADING-STRATEGY.git

cd BACKTESTING-OF-TRADING-STRATEGY# Start all services# Start all services

docker-compose up --builddocker-compose up --build

# Start the application

docker-compose up -d# Access the application# Access the application

# Frontend: http://localhost:8501# Frontend: http://localhost:8501

# Access the application# Backend API: http://localhost:3000# Backend API: http://localhost:3000

# Streamlit UI: http://localhost:8501``````

# Flask API: http://localhost:3000

```### Option 2: Local Development### Option 2: Local Development



### Option 2: Local Development```bash```bash

# Install dependencies# Install dependencies

```bashpip install -r requirements.txtpip install -r requirements.txt

# Install dependencies

pip install -r requirements.txt# Set up environment variables (optional)# Set up environment variables (optional)

cp .env.example .envcp .env.example .env

# Set environment variables# Edit .env with your API keys# Edit .env with your API keys

export GEMINI_API_KEY="your_gemini_key"

export FINNHUB_API_KEY="your_finnhub_key"# Run Flask backend# Run Flask backend

export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"python app.py flaskpython app.py flask



# Run Flask backend# Run Streamlit frontend (in another terminal)# Run Streamlit frontend (in another terminal)

python app.py flaskpython app.py streamlitpython app.py streamlit



# Run Streamlit frontend (in another terminal)# Access the application# Access the application

python app.py streamlit# Frontend: http://localhost:8501# Frontend: http://localhost:8501

```# Backend API: http://localhost:3000# Backend API: http://localhost:3000

``````

### Option 3: Direct Execution

### Option 3: Direct Execution### Option 3: Direct Execution

```bash

# Run Streamlit app directly```bash```bash

streamlit run streamlit_app.py# Run both services simultaneously# Run both services simultaneously

python app.py bothpython app.py both

# Or run Flask app directly

python app.py# Or run individual components# Or run individual components

```python streamlit_app.py  # Frontend onlypython streamlit_app.py  # Frontend only

python -c "from app import create_app; app = create_app(); app.run(port=3000)"  # Backend onlypython -c "from app import create_app; app = create_app(); app.run(port=3000)"  # Backend only

## Usage Workflow``````



1. **Select Market & Symbol**: Choose from Forex, Indian Stocks, or US Stocks

2. **Configure Parameters**: Set timeframe, date range, and initial balance

3. **Gather Data**: Click "Gather Data" to fetch and cache market data

4. **Run Strategy**: Select from 5 professional strategies and execute backtest

5. **Analyze Results**: Review performance metrics, charts, and trade history

6. **Export Report**: Generate comprehensive PDF report with all findings



## API Endpoints



### Data Management

- `GET /api/data/status` - Check data availability

- `POST /api/data/gather` - Fetch market data

- `GET /api/data/symbols` - List available symbols



### Strategy Execution

- `POST /api/strategy/{id}/run` - Execute specific strategy

- `GET /api/strategy/{id}/status` - Check execution status

- `GET /api/strategy/{id}/results` - Retrieve results



### Reporting

- `POST /api/report/generate` - Create PDF report

- `GET /api/report/{id}/download` - Download generated report



## Performance Metrics



The system calculates comprehensive trading performance metrics:



- **Profitability**: Net P&L, Gross Profit/Loss, Profit Factor

- **Risk Metrics**: Max Drawdown, Sharpe Ratio, Sortino Ratio

- **Trade Statistics**: Win Rate, Average Trade P&L, Total Trades

- **Timing**: Average Trade Duration, Best/Worst Trade

- **Portfolio**: Initial/Final Balance, Total Return %



## Configuration



### Environment Variables

```bash

# API Keys

GEMINI_API_KEY=your_gemini_api_key

FINNHUB_API_KEY=your_finnhub_api_key

ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key



# Application Settings

FLASK_ENV=development

STREAMLIT_SERVER_PORT=8501

```



### Strategy Parameters

Each strategy supports customizable parameters:

- **SMA Crossover**: Short/Long period windows

- **RSI**: Overbought/Oversold levels, period

- **Bollinger Bands**: Standard deviation multiplier, period

- **MACD**: Fast/Slow/Signal periods

- **Multi-Indicator**: Combined strategy weights



## Development



### Project Structure

- `app/services/` - Business logic and data processing

- `app/routes/` - API endpoint definitions

- `app/strategies/` - Trading strategy implementations

- `tests/` - Unit and integration tests



### Adding New Strategies

1. Create strategy file in `app/strategies/`

2. Implement strategy logic following existing patterns

3. Add API endpoint in `app/routes/strategies.py`

4. Update frontend strategy selection



### Testing

```bash

# Run all tests

python -m pytest tests/



# Run specific test

python -m pytest tests/test_data_service.py

```



## Sample Results



### Strategy Performance Comparison

| Strategy | Win Rate | Profit Factor | Max Drawdown | Sharpe Ratio |

|----------|----------|---------------|--------------|--------------|

| SMA Crossover | 65.2% | 1.45 | 12.3% | 1.23 |

| RSI Mean Reversion | 58.7% | 1.28 | 15.1% | 0.98 |

| Bollinger Bands | 62.1% | 1.52 | 10.8% | 1.45 |

| MACD Crossover | 59.3% | 1.35 | 13.7% | 1.12 |

| Multi-Indicator | 67.8% | 1.68 | 9.2% | 1.67 |



### Market Performance (RELIANCE.NS, 2024)

- **Total Return**: +24.7%

- **Annualized Return**: +31.2%

- **Max Drawdown**: -8.4%

- **Sharpe Ratio**: 1.89

- **Total Trades**: 156

- **Win Rate**: 68.5%



## Contributing



1. Fork the repository

2. Create a feature branch (`git checkout -b feature/new-strategy`)

3. Commit changes (`git commit -am 'Add new strategy'`)

4. Push to branch (`git push origin feature/new-strategy`)

5. Create Pull Request



### Development Guidelines

- Follow PEP 8 style guidelines

- Add unit tests for new features

- Update documentation for API changes

- Ensure Docker compatibility



---



**Built with ❤️ for quantitative traders and algorithmic strategists**





























































































│   │   ├── strategy_routes.py # Strategy execution
│   │
│   ├── templates/           # HTML templates
│   │   ├── raw/            # Raw API data
│   │   └── trade_history/  # Trade logs
│
├── run_enhanced.py          # Enhanced app runner
└── README.md



```bash
git clone <repository-url>

docker-compose up --build
# Or run individual services
docker-compose up trading-ui          # Streamlit UI only

```bash

python app.py flask
# Run Streamlit UI (in another terminal)

python app.py both

- **Flask Backend API:** http://localhost:5000



   - Enter symbol (e.g., `RELIANCE.NS`, `EURUSD=X`, `AAPL`)
   - Set date range and initial balance
2. **Gather Data:**
   - Data is automatically saved to `/data/raw/` and `/data/processed/`
3. **Run Strategies:**
   - View real-time metrics and equity curves
4. **Generate Reports:**
   - Download professional strategy reports
---
## 🔧 API Endpoints
### Data Management
- `GET /api/data/status` - Check data availability

- `POST /api/strategy/run/{id}` - Run specific strategy
- `GET /api/strategy/list` - List available strategies
### Report Generation
- `POST /api/report/compare` - Generate comparison report



- **Gross Profit/Loss** - Total winning/losing amounts
- **Profit Factor** - Gross profit divided by gross loss
- **Sortino Ratio** - Downside risk-adjusted return
- **Average Trade P&L** - Mean profit per trade
- **Trade History** - Detailed trade log with timestamps
---
## 🔑 API Keys Setup
### Finnhub (Free tier available)
2. Get your API key from dashboard

1. Sign up at [alphavantage.co](https://www.alphavantages.co)
3. Add to `.env`: `ALPHA_VANTAGE_API_KEY=your_key`
### Yahoo Finance



1. Create `app/strategies/strategy6.py`
3. Add route in `strategy_routes.py`

Edit `backtest_service.py` to add new performance metrics.
### Data Sources



Strategy: SMA Crossover (9/21)
Period: 2023-01-01 to 2024-01-01
📈 Performance Metrics:
• Win Rate: 58.3%
• Max Drawdown: -$2,180.50
• Profit Factor: 1.67
📊 Equity Curve: Available in PDF report



2. Create a feature branch
4. Submit a pull request
---
## 📄 License
MIT License - see LICENSE file for details.
---
## 🙏 Acknowledgments
- **Yahoo Finance** - Primary data source
- **Alpha Vantage** - Additional data provider
- **Plotly** - Interactive charting