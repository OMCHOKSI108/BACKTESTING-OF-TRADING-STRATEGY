# AI Agent Instructions for Trading Strategy Backtester

## Enhanced Vision: Full Backtesting Frontend + Strategy Engine

**Goal:** Rebuild current system to have a modern interactive frontend and modular backend that performs backtesting of different trading strategies for Forex, Indian Stocks, or US Stocks.

---

## Architecture Overview

### Current Implementation (Flask-based)
This is a Flask web application for backtesting trading strategies using Yahoo Finance data. The app follows a service-oriented architecture:

- **Routes** (`app/routes/`): Handle HTTP requests and coordinate between services
- **Services** (`app/services/`): Core business logic (data fetching, strategy parsing, backtesting)
- **Templates** (`app/templates/`): Jinja2 HTML templates with Bootstrap + Plotly.js
- **Static** (`app/static/`): CSS, JS, and assets

Data flows: User Input → Route Handler → Data Service → Backtester Service → Results Template

### Enhanced Target Architecture
```
app/
├── __init__.py
├── config.py
├── routes/
│   ├── data_routes.py         # Handle data gathering API
│   ├── strategy_routes.py     # Handle strategy execution
│   └── report_routes.py       # Generate and export reports
├── services/
│   ├── data_service.py        # Fetch data from APIs (Finnhub, AlphaVantage, Yahoo Finance)
│   ├── backtest_service.py    # Run strategies and compute metrics
│   └── report_service.py      # Generate professional summary + charts + PDF
├── strategies/
│   ├── strategy1.py
│   ├── strategy2.py
│   ├── strategy3.py
│   ├── strategy4.py
│   └── strategy5.py
├── static/
│   └── charts/
├── templates/
│   ├── index.html
│   ├── report.html
│   └── layout.html
├── data/
│   ├── raw/
│   ├── processed/
│   └── trade_history/
└── reports/
    └── *.pdf
```

---

## Frontend Requirements

1. **Clean Dashboard Interface** (Streamlit or Flask + HTML templates)
2. **Inputs for:**
   - **Symbol:** Manual entry (e.g. `RELIANCE.NS`, `EURUSD=X`, `AAPL`)
   - **Market Type Selector:** Dropdown → `Forex`, `Indian Stocks`, `US Stocks`
   - **Timeframe Selector:** Dropdown with 8–9 options (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo)
   - **Date Range Selector (Calendar Picker):** Start date – End date
3. **Buttons:**
   - `📊 Gather Data`: Runs data fetching according to user input
   - `⚙️ Strategy 1`, `Strategy 2`, `Strategy 3`, etc. — executes specific strategy
   - `💾 Export PDF`: Saves full report (charts + metrics) into `/reports/` folder
4. Show loading spinner and progress messages

---

## Core Features

### Data Management
- Fetch and auto-store candles using multiple APIs:
  - `yfinance` for Yahoo data
  - `Finnhub` and `AlphaVantage` for Forex + Global stocks
- Each fetched dataset saved as CSV inside `/data/raw/` automatically
- After cleaning, save as `/data/processed/{symbol}_{timeframe}.csv`

### Backtesting & Strategy Report
Each `strategyX.py` will:
- Accept **symbol, timeframe, data path, and balance** as inputs
- Simulate trades and output metrics:
  - **Net Profit / Net Loss, Gross Profit / Gross Loss**
  - **Initial Balance / Final Balance**
  - **Total Trades, Win Rate, Profit Factor**
  - **Max Drawdown, Max Profit, Avg Trade Duration**
  - **Sharpe Ratio, Sortino Ratio**
  - **Equity Curve + Trade History**
- Generate **visual charts**: Time vs Profit, Time vs Loss, Drawdown curve, Strategy performance comparison
- Save **full PDF report** in `/reports/{symbol}_{strategy}_{date}.pdf`

### Visualization
Use `matplotlib` or `plotly` for plots, `pandas` + `numpy` for calculations, `reportlab` or `fpdf2` for PDF reports. Optionally use `mplfinance` for candlestick visualizations.

---

## Key Conventions

### Data Format Standardization
All stock data uses standardized OHLCV columns: `'o', 'h', 'l', 'c', 'v'` (open, high, low, close, volume). Always rename yfinance columns:
```python
df = df.rename(columns={
    'Open': 'o', 'High': 'h', 'Low': 'l', 'Close': 'c', 'Volume': 'v'
})
```

### Strategy Implementation Pattern
Strategies are implemented as functions in `backtester.py` that:
1. Take a pandas DataFrame with OHLCV data
2. Calculate indicators (RSI, VWAP, ATR, CPR) using helper functions
3. Loop through data simulating trades with position tracking
4. Return standardized results dict: `{"total_trades", "total_profit", "average_profit", "trades", "candles"}`

### Route Handler Pattern
Routes follow POST-redirect pattern:
```python
if request.method == "POST":
    # Get form data
    # Call services
    # Return results template
return render_template("form_template.html")
```

---

## Development Workflow

### Running the App
```bash
python run.py  # Starts Flask dev server on http://127.0.0.1:5000
```

### Testing Data/APIs
Use `TESTING.py` for manual validation of data sources and API responses. Example:
```python
df = yf.download(symbol, period='1y', interval='1d', progress=False)
print(f"Candles: {len(df)}")
```

### Adding New Strategies
1. Implement strategy function in `backtester.py` following existing patterns
2. Add route handler in appropriate blueprint (`routes/strategies.py` for predefined)
3. Update HTML dropdowns in templates
4. Test with sample data first

### Example Workflow
1. User enters symbol `RELIANCE.NS`, timeframe `1d`, date range `2024-01-01 → 2024-03-01`
2. Clicks **"Gather Data"** → system fetches candles and saves in `/data/raw/RELIANCE.NS_1d.csv`
3. Clicks **"Strategy 1"** → runs `strategies/strategy1.py` → performs backtest
4. Displays live metrics and charts
5. Clicks **"Export PDF"** → saves professional report

---

## Service Dependencies

### Data Sources
- **Yahoo Finance** (`yfinance`): Primary data source, handles both NSE (.NS) and US stocks
- **Finnhub** (`finnhub_service.py`): Alternative data source for Forex + Global stocks
- **AlphaVantage**: Additional data source for comprehensive market coverage
- **Gemini AI** (`gemini_service.py`): Parses natural language strategies (currently mocked)

### Key Libraries
- `pandas` + `numpy`: Data manipulation and calculations
- `plotly`: Chart generation (limited to last 100 candles for performance)
- `flask`: Web framework with blueprint organization
- `matplotlib` or `plotly`: Enhanced plotting capabilities
- `reportlab` or `fpdf2`: PDF report generation
- `mplfinance`: Candlestick visualizations

---

## Common Patterns

### Indicator Calculations
Reuse existing functions from `backtester.py`:
- `compute_rsi(data, window=14)`
- `calculate_vwap(df)`
- `calculate_atr(df, period=14)`
- `calculate_cpr(df)` - Central Pivot Range

### Error Handling
Check for empty DataFrames after API calls:
```python
df = get_stock_data(stock, duration)
if df.empty:
    return render_template("error.html", error="No data found")
```

### Visualization Data Structure
Candlestick data for Plotly uses this exact format:
```python
candles = {
    'dates': last.index.strftime('%Y-%m-%d').tolist(),
    'open': last['o'].astype(float).tolist(),
    'high': last['h'].astype(float).tolist(),
    'low': last['l'].astype(float).tolist(),
    'close': last['c'].astype(float).tolist(),
}
```

---

## Environment Setup
- API keys stored in `.env` file (GEMINI_API_KEY, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY)
- Virtual environment required: `python -m venv env && env\Scripts\activate`
- Dependencies: `pip install -r requirements.txt`

---

## Developer Notes for Copilot

- Use modular design and follow clean architecture
- Each API must have its own function with exception handling
- Add logging and timestamps for every action
- Default balance = 100,000 USD/INR with adjustable parameter
- Keep code documented and ready for future ML integration