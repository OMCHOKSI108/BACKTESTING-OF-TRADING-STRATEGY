# Enhanced Trading Strategy Backtester

A professional, modern web application for backtesting trading strategies across Forex, Indian Stocks, and US Stocks with comprehensive analytics and PDF reporting.

---

## 🚀 Features

- **Multi-Market Support:** Forex, Indian Stocks (NSE), and US Stocks
- **Multiple Timeframes:** 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo
- **Advanced Strategies:** 5 professional trading strategies with customizable parameters
- **Comprehensive Metrics:** Sharpe Ratio, Sortino Ratio, Max Drawdown, Profit Factor, Win Rate
- **Data Sources:** Yahoo Finance, Finnhub, Alpha Vantage integration
- **Visual Analytics:** Interactive charts, equity curves, drawdown analysis
- **PDF Reports:** Professional report generation with charts and metrics
- **Modern UI:** Streamlit dashboard with real-time progress and responsive design
- **API Architecture:** Modular Flask backend with RESTful endpoints

---

## 📊 Available Strategies

1. **📈 SMA Crossover** - Simple Moving Average crossover strategy
2. **📊 RSI Mean Reversion** - RSI-based mean reversion with overbought/oversold levels
3. **🎯 Bollinger Bands** - Bollinger Bands mean reversion strategy
4. **💹 MACD Crossover** - MACD line and signal line crossover strategy
5. **🔥 Multi-Indicator** - Combined RSI + EMA confirmation strategy

---

## 🏗️ Architecture

```
trading-backtester/
│
├── app/
│   ├── strategies/          # Trading strategy implementations
│   │   ├── strategy1.py     # SMA Crossover
│   │   ├── strategy2.py     # RSI Mean Reversion
│   │   ├── strategy3.py     # Bollinger Bands
│   │   ├── strategy4.py     # MACD Crossover
│   │   └── strategy5.py     # Multi-Indicator
│   │
│   ├── services/            # Core business logic
│   │   ├── data_service.py  # Multi-API data fetching
│   │   ├── backtest_service.py # Strategy execution & metrics
│   │   └── report_service.py # PDF generation
│   │
│   ├── routes/              # API endpoints
│   │   ├── data_routes.py   # Data gathering APIs
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