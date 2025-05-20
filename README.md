# Strategy Backtester

A professional, user-friendly web application for backtesting trading strategies on Indian (NSE) and US stocks using Yahoo Finance data. Visualize results with modern charts and easily select from predefined or custom strategies.

---

## Features

- **Stock Selection Dropdown:** Choose from top NSE and US stocks (RELIANCE.NS, TCS.NS, AAPL, etc.)
- **Predefined Strategies:**
  - ORB (Opening Range Breakout)
  - EMA Crossover (9/21 EMA)
  - RSI (Buy when RSI < 30, Sell when RSI > 70)
- **Custom Strategy Input:** Enter your own strategy logic (RSI, etc.)
- **Multiple Visualizations:**
  - Cumulative Profit (INR)
  - Candlestick Chart (last 100 days)
  - Drawdown Chart
- **Beautiful, Responsive UI:** Built with Flask, Bootstrap, and Plotly.js
- **No API Key Hassles:** Uses Yahoo Finance (yfinance) for free, reliable data

---

## Project Structure

```
strategy-backtester/
│
├── app/
│   ├── static/
│   │   ├── css/           # Custom styles
│   │   ├── js/            # JS scripts
│   │   └── assets/        # Logo, images
│   ├── templates/         # HTML (Jinja2) templates
│   ├── routes/            # Flask route handlers
│   ├── services/          # Data, strategy, and logic modules
│   ├── __init__.py        # Flask app factory
│   └── config.py          # App config
│
├── .env                   # (Optional) Environment variables
├── requirements.txt        # Python dependencies
├── run.py                 # App entry point
├── TESTING.py             # Data/API test script
└── README.md              # This file
```

---

## How to Run

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd strategy-backtester
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv env
   env\Scripts\activate  # On Windows
   # Or: source env/bin/activate  # On Mac/Linux
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Run the app:**
   ```sh
   python run.py
   ```
5. **Open your browser:**
   - Go to [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Usage

- **Select a stock** from the dropdown (NSE or US)
- **Choose a strategy** (ORB, EMA Crossover, RSI, or custom)
- **Set duration** (1Y, 2Y, etc.)
- **Click Backtest**
- **View results:**
  - Trade metrics (total trades, profit, average profit)
  - Trade history table
  - Cumulative profit (in ₹)
  - Candlestick and drawdown charts

---

## Strategies Explained

- **ORB (Opening Range Breakout):**
  - Uses first 30 min high/low as breakout zone
  - Confirms with CPR, VWAP, ATR
  - Entry after 9:45 AM breakout, ATR-based stop loss
- **EMA Crossover:**
  - Buy when 9 EMA crosses above 21 EMA
  - Sell when 9 EMA crosses below 21 EMA
- **RSI:**
  - Buy when RSI < 30, Sell when RSI > 70

---

## Customization

- **Add more stocks:**
  - Edit the dropdowns in `index.html` and `predefined.html`
- **Add new strategies:**
  - Implement in `app/services/backtester.py`
  - Add to dropdowns and routes
- **Change chart types:**
  - Edit `results.html` (uses Plotly.js)

---

## Requirements

- Python 3.9+
- Flask
- yfinance
- pandas, numpy, plotly, etc. (see `requirements.txt`)

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Credits

- Yahoo Finance (yfinance)
- Plotly.js
- Flask
- Bootstrap

---

## Author

- Om Choksi
- omchoksi108@gmail.com
