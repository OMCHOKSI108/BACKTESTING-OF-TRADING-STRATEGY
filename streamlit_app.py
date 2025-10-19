import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import json

# Configure page
st.set_page_config(
    page_title="Trading Strategy Backtester",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL (adjust for your setup)
# Use service name when running in Docker, localhost for local development
import os
if os.getenv('DOCKER_ENV'):
    API_BASE = "http://trading-backtester:3000"  # For internal API calls
    DISPLAY_API_BASE = "http://localhost:3000"   # For user-facing links
else:
    API_BASE = "http://localhost:3000"
    DISPLAY_API_BASE = "http://localhost:3000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

def make_api_call(endpoint, method="GET", data=None):
    """Make API call with error handling"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "POST":
            response = requests.post(url, json=data, timeout=60)  # Increased timeout for Currency Layer API
        else:
            response = requests.get(url, timeout=60)  # Increased timeout for Currency Layer API

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid response from server")
        return None

def get_currency_symbol(market_type):
    """Get currency symbol based on market type"""
    if market_type in ["US Stocks", "Forex", "CRYPTO"]:
        return "$"  # USD for US stocks, Forex, and Crypto
    elif market_type == "Indian Stocks":
        return "₹"  # INR for Indian stocks
    else:
        return "$"  # Default to USD

def main():
    st.markdown('<div class="main-header">⚡ Trading Strategy Backtester</div>', unsafe_allow_html=True)
    
    # System Information
    with st.expander("📋 System Information & API Access"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌐 Frontend (Streamlit UI)**")
            st.markdown("- **URL**: http://localhost:8501")
            st.markdown("- **Status**: ✅ Active")
            
        with col2:
            st.markdown("**🔧 Backend (Flask API)**")
            st.markdown(f"- **Internal**: `{API_BASE}`")
            st.markdown(f"- **External**: `{DISPLAY_API_BASE}`")
            st.markdown("- **Status**: ✅ Active")
            
        st.markdown("**🚀 Enhanced Features**")
        st.markdown("- ⚡ Concurrent processing for multiple symbols")
        st.markdown("- 💾 SQLite caching for improved performance") 
        st.markdown("- 📊 Real-time performance monitoring")
        st.markdown("- 🔄 Professional exchange selection (US/Indian/Forex/Crypto)")

    # Sidebar for inputs
    st.sidebar.title("⚙️ Configuration")

    # Exchange/Market selection with professional icons
    st.sidebar.subheader("🏛️ Exchange Market")
    exchange_options = {
        "🇺🇸 US Stocks": "US",
        "🇮🇳 Indian Stocks": "NSE", 
        "💱 Forex": "FX",
        "₿ Crypto": "CRYPTO"
    }
    
    selected_exchange = st.sidebar.selectbox(
        "Exchange Market",
        list(exchange_options.keys()),
        help="Select the exchange market"
    )
    
    exchange_code = exchange_options[selected_exchange]

    # Define symbols for each exchange (Top 40)
    symbols_by_exchange = {
        "US": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "UNH", "JNJ",
            "V", "PG", "JPM", "HD", "CVX", "MA", "ABBV", "PFE", "AVGO", "KO",
            "COST", "PEP", "TMO", "MRK", "ACN", "WMT", "ABT", "CSCO", "DHR", "LIN",
            "VZ", "ADBE", "CRM", "NKE", "NFLX", "DIS", "CMCSA", "TXN", "NEE", "QCOM"
        ],
        "NSE": [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "INFY.NS", 
            "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS", "KOTAKBANK.NS",
            "AXISBANK.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "ASIANPAINT.NS",
            "ULTRACEMCO.NS", "TITAN.NS", "SUNPHARMA.NS", "NESTLEIND.NS", "WIPRO.NS",
            "POWERGRID.NS", "ONGC.NS", "NTPC.NS", "JSWSTEEL.NS", "TATAMOTORS.NS",
            "BAJAJFINSV.NS", "M&M.NS", "HINDUNILVR.NS", "TECHM.NS", "COALINDIA.NS",
            "HINDALCO.NS", "GRASIM.NS", "ADANIENT.NS", "CIPLA.NS",
            "EICHERMOT.NS", "BPCL.NS", "INDUSINDBK.NS", "BRITANNIA.NS", "TATASTEEL.NS"
        ],
        "FX": [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD",
            "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "EURCHF", "EURAUD",
            "EURNZD", "EURCAD", "GBPCHF", "GBPAUD", "GBPNZD", "GBPCAD",
            "AUDJPY", "AUDCHF", "AUDNZD", "AUDCAD", "NZDJPY", "NZDCHF",
            "NZDCAD", "CADJPY", "CADCHF", "CHFJPY", "USDINR", "USDSGD",
            "USDHKD", "USDMXN", "USDBRL", "USDRUB", "USDCNY", "USDZAR",
            "USDTRY", "USDKRW", "USDTHB", "USDPLN", "USDSEK", "USDNOK"
        ],
        "CRYPTO": [
            "BTC", "ETH", "BNB", "XRP", "ADA", "SOL",
            "DOGE", "DOT", "AVAX", "SHIB", "MATIC", "LTC",
            "UNI", "LINK", "BCH", "ALGO", "XLM", "VET",
            "ICP", "ETC", "FIL", "TRX", "ATOM", "HBAR",
            "NEAR", "FTM", "MANA", "SAND", "THETA", "EGLD",
            "XTZ", "AXS", "FLOW", "ENJ", "CHZ", "KLAY",
            "ZIL", "COMP", "YFI", "SUSHI", "AAVE", "MKR",
            "1INCH", "ALPHA", "BAL", "CRV", "SNX", "RUNE"
        ]
    }

    # Symbol selector based on exchange
    st.sidebar.subheader("📊 Symbol Selection")
    available_symbols = symbols_by_exchange.get(exchange_code, ["AAPL"])
    
    # Option to use predefined list or custom symbol
    use_custom_symbol = st.sidebar.checkbox("🔧 Enter Custom Symbol", help="Enable to enter symbols not in the predefined list")
    
    if use_custom_symbol:
        symbol = st.sidebar.text_input(
            "Custom Symbol",
            value="",
            help=f"Enter custom symbol for {selected_exchange} (e.g., BTC for crypto, EURUSD for forex)"
        ).upper()
        
        if not symbol:
            st.sidebar.warning("Please enter a symbol")
            symbol = available_symbols[0]  # Default fallback
    else:
        symbol = st.sidebar.selectbox(
            "Symbol",
            available_symbols,
            help=f"Select from curated list of symbols in {selected_exchange}"
        )

    # Set market type based on exchange
    market_type_mapping = {
        "US": "US Stocks",
        "NSE": "Indian Stocks", 
        "FX": "Forex",
        "CRYPTO": "Crypto"
    }
    market_type = market_type_mapping.get(exchange_code, "US Stocks")

    # Show data source information
    if exchange_code == "CRYPTO":
        st.sidebar.info("🔗 **Crypto Data Sources:** Binance API (primary), CoinGecko API (fallback)")
    elif exchange_code == "FX":
        st.sidebar.info("🔗 **Forex Data Sources:** Alpha Vantage API with advanced validation")
    else:
        st.sidebar.info("🔗 **Stock Data Sources:** Yahoo Finance, Alpha Vantage, Finnhub")

    # Timeframe selector
    timeframe_options = {
        "1 Minute": "1m",
        "5 Minutes": "5m",
        "15 Minutes": "15m",
        "30 Minutes": "30m",
        "1 Hour": "1h",
        "4 Hours": "4h",
        "1 Day": "1d",
        "1 Week": "1w",
        "1 Month": "1mo"
    }

    timeframe_display = st.sidebar.selectbox(
        "Timeframe",
        list(timeframe_options.keys()),
        index=6,  # Default to 1 Day
        help="Select the timeframe for analysis"
    )
    timeframe = timeframe_options[timeframe_display]

    # Date range selector with intelligent defaults based on timeframe
    st.sidebar.subheader("📅 Date Range")
    
    # Calculate appropriate default date range based on timeframe
    if timeframe in ['1m', '5m', '15m', '30m', '45m']:
        # Intraday data - limit to last 30 days to avoid API restrictions
        default_days = 30
        st.sidebar.info("📋 Note: Intraday data limited to last 30 days due to API restrictions")
    elif timeframe in ['1h', '4h']:
        # Hourly data - 90 days
        default_days = 90
    else:
        # Daily, weekly, monthly - full year
        default_days = 365
    
    col1, col2 = st.sidebar.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=default_days),
            help=f"Start date for data analysis (max {default_days} days for {timeframe_display})"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            help="End date for data analysis"
        )

    # Initial balance
    currency_symbol = get_currency_symbol(market_type)
    initial_balance = st.sidebar.number_input(
        f"Initial Balance ({currency_symbol})",
        value=100000,
        min_value=1000,
        step=1000,
        help="Starting portfolio balance"
    )

    # Main content area
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Data Gathering", "📋 Dataset View", "⚡ Strategy Testing", "📈 Results", "📋 Reports", "🤖 AI Agent"])

    # Tab 1: Data Gathering
    with tab1:
        st.header("Data Gathering")

        if st.button("🔍 Gather Data", type="primary", use_container_width=True):
            with st.spinner("Fetching market data..."):
                progress_bar = st.progress(0)

                # Simulate progress
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)

                # Make API call
                data_payload = {
                    "symbol": symbol,
                    "market_type": market_type,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "timeframe": timeframe
                }

                result = make_api_call("/api/data/gather", method="POST", data=data_payload)

                if result and result.get("success"):
                    st.markdown(f"""
                    <div class="success-message">
                        ✅ Successfully gathered {result.get('data_points', 0)} data points for {symbol}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="error-message">
                        ❌ Failed to gather data. Please check your inputs and try again.
                    </div>
                    """, unsafe_allow_html=True)

        # Data status check
        st.subheader("Data Status")
        if st.button("Check Data Availability"):
            status_result = make_api_call(f"/api/data/status?symbol={symbol}&timeframe={timeframe}")

            if status_result and status_result.get("success"):
                if status_result.get("available"):
                    st.success(f"✅ Data available: {status_result.get('data_points', 0)} points")
                    st.info(f"Last updated: {status_result.get('last_updated', 'Unknown')}")
                else:
                    st.warning("⚠️ No processed data available. Please gather data first.")
            else:
                st.error("❌ Unable to check data status")

    # Tab 2: Dataset View
    with tab2:
        st.header("📋 Dataset Viewer")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader("📊 Data Preview")
            
        with col2:
            show_limit = st.selectbox("Show Records", [10, 20, 50, 100], index=0)
            
        with col3:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()

        # Get data preview
        if symbol:
            preview_result = make_api_call(f"/api/data/preview?symbol={symbol}&timeframe={timeframe}&limit={show_limit}")
            
            if preview_result and preview_result.get("success"):
                data_records = preview_result.get("data", [])
                total_records = preview_result.get("total_records", 0)
                
                if data_records:
                    # Convert to DataFrame for better display
                    import pandas as pd
                    df_display = pd.DataFrame(data_records)
                    
                    # Rename columns for better display
                    column_mapping = {
                        'o': '💹 Open', 'h': '📈 High', 'l': '📉 Low', 
                        'c': '💰 Close', 'v': '📊 Volume', 'timestamp': '📅 Date'
                    }
                    df_display = df_display.rename(columns=column_mapping)
                    
                    # Format numeric columns
                    numeric_cols = ['💹 Open', '📈 High', '📉 Low', '💰 Close']
                    for col in numeric_cols:
                        if col in df_display.columns:
                            df_display[col] = df_display[col].round(2)
                    
                    if '📊 Volume' in df_display.columns:
                        df_display['📊 Volume'] = df_display['📊 Volume'].apply(lambda x: f"{x:,.0f}")
                    
                    # Format date column
                    if '📅 Date' in df_display.columns:
                        df_display['📅 Date'] = pd.to_datetime(df_display['📅 Date']).dt.strftime('%Y-%m-%d')
                    
                    # Display statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Total Records", f"{total_records:,}")
                    
                    with col2:
                        if '💰 Close' in df_display.columns:
                            latest_price = df_display['💰 Close'].iloc[-1] if len(df_display) > 0 else 0
                            currency_symbol = get_currency_symbol(market_type)
                            st.metric("💰 Latest Price", f"{currency_symbol}{latest_price}")
                    
                    with col3:
                        if '📅 Date' in df_display.columns:
                            date_range = f"{df_display['📅 Date'].iloc[0]} to {df_display['📅 Date'].iloc[-1]}" if len(df_display) > 1 else df_display['📅 Date'].iloc[0]
                            st.metric("📅 Date Range", date_range)
                    
                    with col4:
                        st.metric("⏱️ Timeframe", timeframe.upper())
                    
                    # Display the data table
                    st.markdown(f"**Showing last {len(df_display)} of {total_records} records for {symbol}**")
                    currency_symbol = get_currency_symbol(market_type)
                    st.dataframe(
                        df_display, 
                        use_container_width=True,
                        height=400,
                        column_config={
                            "💹 Open": st.column_config.NumberColumn("💹 Open", format=f"{currency_symbol}%.2f"),
                            "📈 High": st.column_config.NumberColumn("📈 High", format=f"{currency_symbol}%.2f"),
                            "📉 Low": st.column_config.NumberColumn("📉 Low", format=f"{currency_symbol}%.2f"),
                            "💰 Close": st.column_config.NumberColumn("💰 Close", format=f"{currency_symbol}%.2f"),
                            "📊 Volume": st.column_config.TextColumn("📊 Volume"),
                            "📅 Date": st.column_config.DateColumn("📅 Date")
                        }
                    )
                    
                    # Download option
                    csv_data = df_display.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"{symbol}_{timeframe}_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                else:
                    st.warning("📋 No data records found for the selected symbol and timeframe.")
                    
            else:
                error_msg = preview_result.get("error", "Unknown error") if preview_result else "Failed to fetch data"
                st.error(f"❌ Error loading data preview: {error_msg}")
                st.info("💡 Make sure to gather data first in the 'Data Gathering' tab.")
        else:
            st.info("👆 Select a symbol from the sidebar to view its dataset.")

    # Tab 3: Strategy Testing  
    with tab3:
        st.header("Strategy Testing")

        # Strategy selection
        strategies = {
            1: "SMA Crossover (9/21)",
            2: "RSI Mean Reversion",
            3: "Bollinger Bands",
            4: "MACD Crossover",
            5: "Multi-Indicator (RSI + EMA)"
        }

        selected_strategy = st.selectbox(
            "Select Strategy",
            list(strategies.keys()),
            format_func=lambda x: strategies[x],
            help="Choose a trading strategy to backtest"
        )

        if st.button("🚀 Run Strategy", type="primary", use_container_width=True):
            with st.spinner(f"Running {strategies[selected_strategy]}..."):
                progress_bar = st.progress(0)

                # Simulate progress
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)

                # Make API call
                strategy_payload = {
                    "symbol": symbol,
                    "market_type": market_type,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "timeframe": timeframe,
                    "initial_balance": initial_balance
                }

                result = make_api_call(f"/api/strategy/run/{selected_strategy}", method="POST", data=strategy_payload)

                if result and result.get("success"):
                    # Store results in session state
                    st.session_state.last_results = result.get("results", {})
                    st.session_state.last_strategy = selected_strategy

                    st.markdown(f"""
                    <div class="success-message">
                        ✅ Strategy {selected_strategy} completed successfully!<br>
                        {result['results'].get('total_trades', 0)} trades executed
                    </div>
                    """, unsafe_allow_html=True)

                    # Switch to results tab
                    st.rerun()
                else:
                    st.markdown("""
                    <div class="error-message">
                        ❌ Strategy execution failed. Please ensure data is available and try again.
                    </div>
                    """, unsafe_allow_html=True)

        # Strategy comparison
        st.subheader("⚖️ Strategy Comparison")
        if st.button("Compare All Strategies", use_container_width=True):
            with st.spinner("Comparing all strategies..."):
                comparison_payload = {
                    "symbol": symbol,
                    "market_type": market_type,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "timeframe": timeframe,
                    "strategy_ids": [1, 2, 3, 4, 5],
                    "initial_balance": initial_balance
                }

                result = make_api_call("/api/strategy/compare", method="POST", data=comparison_payload)

                if result and result.get("success"):
                    st.session_state.comparison_results = result
                    st.success("✅ Strategy comparison completed!")
                else:
                    st.error("❌ Strategy comparison failed")

    # Tab 4: Results
    with tab4:
        st.header("📈 Strategy Results & Analysis")
        
        if "last_results" in st.session_state:
            results = st.session_state.last_results
            strategy_id = st.session_state.get("last_strategy", 1)
            strategies = {1: "SMA Crossover", 2: "RSI Divergence", 3: "Bollinger Bands", 4: "MACD Crossover", 5: "Multi-Indicator"}
            strategy_name = strategies.get(strategy_id, f"Strategy {strategy_id}")
            
            st.subheader(f"{strategy_name} Results for {symbol}")
            
            # Display key metrics with better formatting
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                net_profit = results.get("net_profit_loss", 0)
                profit_pct = (net_profit / initial_balance) * 100 if initial_balance > 0 else 0
                currency_symbol = get_currency_symbol(market_type)
                st.metric(
                    "💰 Net P&L", 
                    f"{currency_symbol}{net_profit:.2f}", 
                    delta=f"{profit_pct:.2f}%",
                    delta_color="normal" if net_profit >= 0 else "inverse"
                )
            
            with col2:
                total_trades = results.get("total_trades", 0)
                st.metric("📊 Total Trades", total_trades)
            
            with col3:
                win_rate = results.get("win_rate", 0) * 100 if results.get("win_rate") else 0
                st.metric("🎯 Win Rate", f"{win_rate:.1f}%", delta=f"{win_rate - 50:.1f}% vs 50%")
            
            with col4:
                avg_trade = results.get("average_trade_pnl", 0)
                currency_symbol = get_currency_symbol(market_type)
                st.metric("📈 Avg Trade", f"{currency_symbol}{avg_trade:.2f}")
            
            # Enhanced Performance Charts
            st.subheader("📊 Performance Analysis")
            
            # Create tabs for different views
            chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs(["💹 Equity Curve", "📈 Trade Analysis", "📋 Trade History", "📊 Statistics"])
            
            with chart_tab1:
                st.markdown("**💹 Portfolio Equity Curve**")
                
                # Get equity curve data
                equity_curve = results.get("equity_curve", [])
                if equity_curve:
                    import pandas as pd
                    import plotly.graph_objects as go
                    from plotly.subplots import make_subplots
                    
                    # Create equity curve DataFrame with better labeling
                    eq_df = pd.DataFrame({
                        'Trade_Number': range(len(equity_curve)),
                        'Portfolio_Value': equity_curve,
                        'Returns': [(val - initial_balance) for val in equity_curve],
                        'Returns_Pct': [((val - initial_balance) / initial_balance * 100) for val in equity_curve]
                    })
                    
                    # Create subplots
                    fig = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('Portfolio Value Over Time', 'Returns Percentage Over Time'),
                        vertical_spacing=0.12,
                        row_heights=[0.7, 0.3]
                    )
                    
                    # Portfolio value chart with markers
                    fig.add_trace(
                        go.Scatter(
                            x=eq_df['Trade_Number'],
                            y=eq_df['Portfolio_Value'],
                            mode='lines+markers',
                            name='Portfolio Value',
                            line=dict(color='#0068c9', width=3),
                            marker=dict(size=6, color='#0068c9'),
                            hovertemplate=f'<b>Trade:</b> %{{x}}<br><b>Equity:</b> {get_currency_symbol(market_type)}%{{y:,.2f}}<extra></extra>'
                        ),
                        row=1, col=1
                    )
                    
                    # Add initial balance reference line
                    fig.add_hline(
                        y=initial_balance, 
                        line_dash="dash", 
                        line_color="red", 
                        annotation_text="Initial Balance",
                        row=1, col=1
                    )
                    
                    # Returns percentage chart with improved styling
                    colors = ['green' if x >= 0 else 'red' for x in eq_df['Returns_Pct']]
                    fig.add_trace(
                        go.Scatter(
                            x=eq_df['Trade_Number'],
                            y=eq_df['Returns_Pct'],
                            mode='lines+markers',
                            name='Returns %',
                            line=dict(color='#ff7f0e', width=2),
                            marker=dict(color=colors, size=5),
                            hovertemplate='<b>Trade:</b> %{x}<br><b>Return:</b> %{y:.2f}%<extra></extra>'
                        ),
                        row=2, col=1
                    )
                    
                    # Add zero line for returns
                    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
                    
                    # Update layout
                    fig.update_layout(
                        title=f'{strategy_name} - Portfolio Performance',
                        height=600,
                        showlegend=True,
                        hovermode='x unified'
                    )
                    
                    fig.update_xaxes(title_text="Trade Number", row=2, col=1)
                    fig.update_yaxes(title_text=f"Portfolio Value ({get_currency_symbol(market_type)})", row=1, col=1)
                    fig.update_yaxes(title_text="Returns (%)", row=2, col=1)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Key statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        max_value = max(equity_curve)
                        st.metric("� Peak Value", f"{currency_symbol}{max_value:,.2f}")
                    with col2:
                        min_value = min(equity_curve)
                        st.metric("📉 Lowest Value", f"{currency_symbol}{min_value:,.2f}")
                    with col3:
                        total_return_pct = ((equity_curve[-1] - initial_balance) / initial_balance) * 100
                        st.metric("�📊 Total Return", f"{total_return_pct:.2f}%")
                    with col4:
                        max_drawdown = max(equity_curve) - min(equity_curve)
                        st.metric("⚠️ Max Drawdown", f"{currency_symbol}{max_drawdown:,.2f}")
                else:
                    st.warning("⚠️ No equity curve data available")
            
            with chart_tab2:
                st.markdown("**📈 Trade Performance Analysis**")
                
                trades = results.get("trades", [])
                if trades:
                    import pandas as pd
                    import plotly.graph_objects as go
                    import plotly.express as px
                    
                    # Convert trades to DataFrame
                    trades_df = pd.DataFrame(trades)
                    trades_df['profit_loss'] = pd.to_numeric(trades_df.get('pnl', 0))
                    trades_df['entry_price'] = pd.to_numeric(trades_df.get('entry_price', 0))
                    trades_df['exit_price'] = pd.to_numeric(trades_df.get('exit_price', 0))
                    trades_df['trade_number'] = range(1, len(trades_df) + 1)
                    trades_df['cumulative_pnl'] = trades_df['profit_loss'].cumsum()
                    trades_df['win_loss'] = trades_df['profit_loss'].apply(lambda x: 'Win' if x > 0 else 'Loss' if x < 0 else 'Breakeven')
                    
                    # Trade P&L Distribution
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_pnl = px.bar(
                            trades_df, 
                            x='trade_number', 
                            y='profit_loss',
                            color='win_loss',
                            color_discrete_map={'Win': 'green', 'Loss': 'red', 'Breakeven': 'gray'},
                            title="Trade P&L by Trade Number",
                            labels={'profit_loss': f'Profit/Loss ({currency_symbol})', 'trade_number': 'Trade #'}
                        )
                        fig_pnl.update_layout(height=400)
                        st.plotly_chart(fig_pnl, use_container_width=True)
                    
                    with col2:
                        fig_cum = go.Figure()
                        fig_cum.add_trace(
                            go.Scatter(
                                x=trades_df['trade_number'],
                                y=trades_df['cumulative_pnl'],
                                mode='lines+markers',
                                name='Cumulative P&L',
                                line=dict(color='blue', width=3),
                                marker=dict(size=6)
                            )
                        )
                        fig_cum.update_layout(
                            title="Cumulative P&L Over Time",
                            xaxis_title="Trade Number",
                            yaxis_title=f"Cumulative P&L ({currency_symbol})",
                            height=400
                        )
                        st.plotly_chart(fig_cum, use_container_width=True)
                    
                    # Trade statistics
                    st.markdown("**📊 Trade Statistics**")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        winning_trades = len(trades_df[trades_df['profit_loss'] > 0])
                        st.metric("🟢 Winning Trades", winning_trades)
                    
                    with col2:
                        losing_trades = len(trades_df[trades_df['profit_loss'] < 0])
                        st.metric("🔴 Losing Trades", losing_trades)
                    
                    with col3:
                        largest_win = trades_df['profit_loss'].max()
                        currency_symbol = get_currency_symbol(market_type)
                        st.metric("🎯 Largest Win", f"{currency_symbol}{largest_win:.2f}")
                    
                    with col4:
                        largest_loss = trades_df['profit_loss'].min()
                        currency_symbol = get_currency_symbol(market_type)
                        st.metric("⚠️ Largest Loss", f"{currency_symbol}{largest_loss:.2f}")
                else:
                    st.warning("⚠️ No trade data available")
            
            with chart_tab3:
                st.markdown("**📋 Individual Trade History**")
                
                trades = results.get("trades", [])
                if trades:
                    import pandas as pd
                    
                    # Convert trades to DataFrame with better formatting
                    trades_df = pd.DataFrame(trades)
                    
                    # Format the data for display
                    display_df = trades_df.copy()
                    
                    # Rename columns for better display
                    column_mapping = {
                        'entry_time': '📅 Entry Date',
                        'entry_price': '💹 Entry Price', 
                        'exit_time': '📅 Exit Date',
                        'exit_price': '💰 Exit Price',
                        'pnl': '💵 P&L',
                        'duration': '⏱️ Duration',
                        'type': '🔄 Type'
                    }
                    
                    # Rename columns that exist
                    display_df = display_df.rename(columns={k: v for k, v in column_mapping.items() if k in display_df.columns})
                    
                    # Format numeric columns
                    currency_symbol = get_currency_symbol(market_type)
                    if '💹 Entry Price' in display_df.columns:
                        display_df['💹 Entry Price'] = display_df['💹 Entry Price'].apply(lambda x: f"{currency_symbol}{float(x):.4f}")
                    if '💰 Exit Price' in display_df.columns:
                        display_df['💰 Exit Price'] = display_df['💰 Exit Price'].apply(lambda x: f"{currency_symbol}{float(x):.4f}")
                    if '💵 P&L' in display_df.columns:
                        display_df['💵 P&L'] = display_df['💵 P&L'].apply(lambda x: f"{currency_symbol}{float(x):.2f}")
                        display_df['📊 Result'] = display_df['💵 P&L'].apply(lambda x: '🟢 Win' if float(str(x).replace(currency_symbol, '')) > 0 else '🔴 Loss' if float(str(x).replace(currency_symbol, '')) < 0 else '⚪ Breakeven')
                    
                    # Add trade number
                    display_df.insert(0, '#️⃣ Trade', range(1, len(display_df) + 1))
                    
                    # Display summary statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    pnl_values = [float(str(x).replace(currency_symbol, '')) for x in trades_df.get('pnl', [])]
                    
                    with col1:
                        st.metric("📊 Total Trades", len(trades_df))
                    with col2:
                        winning_pct = (len([x for x in pnl_values if x > 0]) / len(pnl_values) * 100) if pnl_values else 0
                        st.metric("🎯 Win Rate", f"{winning_pct:.1f}%")
                    with col3:
                        avg_win = sum([x for x in pnl_values if x > 0]) / len([x for x in pnl_values if x > 0]) if [x for x in pnl_values if x > 0] else 0
                        st.metric("📈 Avg Win", f"{currency_symbol}{avg_win:.2f}")
                    with col4:
                        avg_loss = sum([x for x in pnl_values if x < 0]) / len([x for x in pnl_values if x < 0]) if [x for x in pnl_values if x < 0] else 0
                        st.metric("📉 Avg Loss", f"{currency_symbol}{avg_loss:.2f}")
                    
                    # Display trade table
                    st.markdown(f"**All {len(display_df)} Trades:**")
                    st.dataframe(
                        display_df, 
                        use_container_width=True,
                        height=400,
                        column_config={
                            "#️⃣ Trade": st.column_config.NumberColumn("#️⃣ Trade", width="small"),
                            "📅 Entry Date": st.column_config.TextColumn("📅 Entry Date", width="medium"), 
                            "💹 Entry Price": st.column_config.TextColumn("💹 Entry Price", width="small"),
                            "📅 Exit Date": st.column_config.TextColumn("📅 Exit Date", width="medium"),
                            "💰 Exit Price": st.column_config.TextColumn("💰 Exit Price", width="small"),
                            "💵 P&L": st.column_config.TextColumn("� P&L", width="small"),
                            "📊 Result": st.column_config.TextColumn("📊 Result", width="small"),
                            "🔄 Type": st.column_config.TextColumn("🔄 Type", width="small")
                        }
                    )
                    
                    # CSV download for trades
                    trades_csv = trades_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Trade History CSV",
                        data=trades_csv,
                        file_name=f"{symbol}_{strategy_name}_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ No trade history available")
            
            with chart_tab4:
                st.markdown("**📊 Detailed Performance Statistics**")
                
                # Comprehensive statistics display
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📈 Profitability Metrics**")
                    st.write(f"• **Net Profit/Loss:** {currency_symbol}{results.get('net_profit_loss', 0):.2f}")
                    st.write(f"• **Gross Profit:** {currency_symbol}{results.get('gross_profit', 0):.2f}")
                    st.write(f"• **Gross Loss:** {currency_symbol}{results.get('gross_loss', 0):.2f}")
                    st.write(f"• **Profit Factor:** {results.get('profit_factor', 0):.2f}")
                    st.write(f"• **Total Return:** {((results.get('net_profit_loss', 0) / initial_balance) * 100):.2f}%")
                    
                    st.markdown("**⚠️ Risk Metrics**")
                    st.write(f"• **Max Drawdown:** {currency_symbol}{results.get('max_drawdown', 0):.2f}")
                    st.write(f"• **Max Drawdown %:** {((results.get('max_drawdown', 0) / initial_balance) * 100):.2f}%")
                    st.write(f"• **Sharpe Ratio:** {results.get('sharpe_ratio', 0):.3f}")
                
                with col2:
                    st.markdown("**📊 Trade Statistics**")
                    st.write(f"• **Total Trades:** {results.get('total_trades', 0)}")
                    st.write(f"• **Winning Trades:** {results.get('winning_trades', 0)}")
                    st.write(f"• **Losing Trades:** {results.get('losing_trades', 0)}")
                    st.write(f"• **Win Rate:** {results.get('win_rate', 0):.1f}%")
                    st.write(f"• **Average Trade P&L:** {currency_symbol}{results.get('average_trade_pnl', 0):.2f}")
                    
                    st.markdown("**⏱️ Duration Metrics**")
                    st.write(f"• **Average Trade Duration:** {results.get('average_trade_duration', 0):.1f} periods")
                    st.write(f"• **Largest Win:** {currency_symbol}{results.get('largest_win', 0):.2f}")
                    st.write(f"• **Largest Loss:** {currency_symbol}{results.get('largest_loss', 0):.2f}")
                
                # Performance summary CSV download
                summary_data = {
                    'Metric': ['Net P&L', 'Total Trades', 'Win Rate', 'Profit Factor', 'Max Drawdown', 'Sharpe Ratio', 'Total Return %'],
                    'Value': [
                        f"{currency_symbol}{results.get('net_profit_loss', 0):.2f}",
                        results.get('total_trades', 0),
                        f"{results.get('win_rate', 0):.1f}%",
                        f"{results.get('profit_factor', 0):.2f}",
                        f"{currency_symbol}{results.get('max_drawdown', 0):.2f}",
                        f"{results.get('sharpe_ratio', 0):.3f}",
                        f"{((results.get('net_profit_loss', 0) / initial_balance) * 100):.2f}%"
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_csv = summary_df.to_csv(index=False)
                
                st.download_button(
                    label="📊 Download Performance Summary CSV",
                    data=summary_csv,
                    file_name=f"{symbol}_{strategy_name}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("📊 No results available. Please run a strategy first.")

    # Tab 5: Reports
    with tab5:
        st.header("📋 Reports")
        
        if "last_results" in st.session_state:
            st.subheader("Generate Strategy Report")

            if st.button("📄 Generate PDF Report", use_container_width=True):
                with st.spinner("Generating PDF report..."):
                    report_payload = {
                        "symbol": symbol,
                        "strategy_name": f"Strategy {st.session_state.get('last_strategy', 1)}",
                        "results": st.session_state.last_results
                    }

                    result = make_api_call("/api/report/generate", method="POST", data=report_payload)

                    if result and result.get("success"):
                        st.success("✅ PDF report generated successfully!")
                        download_url = result.get("download_url", "")
                        if download_url:
                            st.markdown(f"[📥 Download Report]({DISPLAY_API_BASE}{download_url})")
                    else:
                        st.error("❌ Failed to generate PDF report")

        if "comparison_results" in st.session_state:
            st.subheader("Generate Comparison Report")

            if st.button("📊 Generate Comparison Report", use_container_width=True):
                with st.spinner("Generating comparison PDF report..."):
                    comparison_payload = {
                        "symbol": symbol,
                        "results_list": st.session_state.comparison_results.get("individual_results", [])
                    }

                    result = make_api_call("/api/report/compare", method="POST", data=comparison_payload)

                    if result and result.get("success"):
                        st.success("✅ Comparison report generated successfully!")
                        download_url = result.get("download_url", "")
                        if download_url:
                            st.markdown(f"[📥 Download Comparison Report]({DISPLAY_API_BASE}{download_url})")
                    else:
                        st.error("❌ Failed to generate comparison report")
        
        if not ("last_results" in st.session_state or "comparison_results" in st.session_state):
            st.info("📋 No results available for report generation. Please run strategies first.")

    # Tab 6: AI Agent
    with tab6:
        # Perplexity-inspired Custom CSS
        st.markdown("""
        <style>
        /* Clean Perplexity-style design */
        .perplexity-header {
            background: white;
            padding: 2.5rem 1rem;
            text-align: center;
            margin-bottom: 2rem;
        }
        .perplexity-header h1 {
            font-size: 2.8rem;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .perplexity-header p {
            font-size: 1.1rem;
            color: #6b7280;
            margin-top: 0.75rem;
            font-weight: 400;
        }
        .thinking-animation {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 2.5rem;
            text-align: center;
            margin: 2rem 0;
        }
        .thinking-header {
            font-size: 1.25rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 1rem;
        }
        .thinking-subtext {
            font-size: 0.95rem;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }
        .thinking-dots {
            display: flex;
            gap: 6px;
            justify-content: center;
            align-items: center;
        }
        .thinking-dot {
            width: 8px;
            height: 8px;
            background: #3b82f6;
            border-radius: 50%;
            animation: bounce 1.4s ease-in-out infinite both;
        }
        .thinking-dot:nth-child(1) { animation-delay: -0.32s; }
        .thinking-dot:nth-child(2) { animation-delay: -0.16s; }
        .thinking-dot:nth-child(3) { animation-delay: 0s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
            40% { transform: translateY(-10px); opacity: 1; }
        }
        .response-container {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 2rem;
            margin: 1.5rem 0;
        }
        .response-section {
            margin-bottom: 1.5rem;
        }
        .response-section h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.75rem;
        }
        .response-section p {
            font-size: 1rem;
            line-height: 1.6;
            color: #374151;
        }
        .source-item {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            transition: border-color 0.2s;
        }
        .source-item:hover {
            border-color: #3b82f6;
        }
        .source-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.25rem;
        }
        .source-url {
            font-size: 0.85rem;
            color: #3b82f6;
            text-decoration: none;
        }
        .metric-box {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        .metric-box-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a1a1a;
        }
        .metric-box-label {
            font-size: 0.875rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }
        .progress-step {
            font-size: 0.95rem;
            color: #6b7280;
            padding: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Clean Header
        st.markdown("""
        <div class="perplexity-header">
            <h1>🤖 AI Financial Analyst</h1>
            <p>Advanced market research powered by AI and real-time data</p>
        </div>
        """, unsafe_allow_html=True)

        # Initialize session state for chat history
        if 'ai_chat_history' not in st.session_state:
            st.session_state.ai_chat_history = []

        # Chat History Section
        if st.session_state.ai_chat_history:
            st.markdown("### 💬 Research History")

            chat_container = st.container()

            with chat_container:
                for i, message in enumerate(st.session_state.ai_chat_history):
                    if message['role'] == 'user':
                        st.markdown(f"""
                        <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #2196f3;">
                            <strong>👤 Your Question:</strong><br>{message['content']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        with st.expander(f"🤖 AI Analysis #{i//2 + 1}", expanded=False):
                            st.markdown(message['content'])
                            if 'timestamp' in message:
                                st.caption(f"📅 Generated on: {message['timestamp']}")

        # Input Section
        st.markdown("### � Ask Your Financial Question")

        with st.form(key="ai_chat_form"):
            col1, col2 = st.columns([3, 1])

            with col1:
                user_query = st.text_area(
                    "",
                    placeholder="e.g., 'What are the current market trends for EURUSD?', 'Analyze Bitcoin's technical indicators', 'Research Fed's impact on stocks'",
                    height=80,
                    label_visibility="collapsed"
                )

            with col2:
                max_results = st.selectbox(
                    "Research Depth",
                    options=[3, 5, 7, 10],
                    index=1,
                    help="Number of sources to analyze"
                )

            # Submit button with custom styling
            submit_button = st.form_submit_button(
                "🚀 Analyze Markets",
                type="primary",
                use_container_width=True
            )

        # Enhanced AI Agent interaction with Perplexity-style animation
        if submit_button and user_query.strip():
            # Create placeholders for dynamic content
            animation_placeholder = st.empty()
            response_placeholder = st.empty()

            # Perplexity-style thinking animation
            with animation_placeholder.container():
                st.markdown("""
                <div class="thinking-animation">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🧠</div>
                    <div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem;">AI Analyst is Thinking</div>
                    <div style="font-size: 1rem; opacity: 0.9; margin-bottom: 1rem;">Searching financial databases & analyzing market data</div>
                    <div class="thinking-dots">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Progress stages with smooth transitions
                progress_phases = [
                    "🔍 Scanning financial news sources...",
                    "📊 Analyzing market indicators...",
                    "📰 Cross-referencing latest reports...",
                    "🤖 Processing with advanced AI algorithms...",
                    "📈 Generating comprehensive analysis...",
                    "✨ Finalizing professional insights..."
                ]

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, phase in enumerate(progress_phases):
                    status_text.markdown(f"**{phase}**")
                    progress_bar.progress((i + 1) / len(progress_phases))
                    time.sleep(0.7)

                progress_bar.empty()
                status_text.empty()

            # Clear animation and make API call
            animation_placeholder.empty()

            with st.spinner(""):
                research_payload = {
                    "query": user_query.strip(),
                    "max_results": max_results
                }

                result = make_api_call("/api/ai/research", method="POST", data=research_payload)

                if result and result.get("success"):
                    # Add to chat history
                    st.session_state.ai_chat_history.append({
                        'role': 'user',
                        'content': user_query.strip(),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                    # Format and display response
                    with response_placeholder.container():
                        ai_response = result.get("analysis", {})

                        # Main Analysis Card
                        st.markdown("""
                        <div class="response-card">
                            <h3 style="color: #667eea; margin-top: 0;">📊 AI Market Analysis</h3>
                        </div>
                        """, unsafe_allow_html=True)

                        # Market Overview
                        if isinstance(ai_response, dict) and ai_response.get('market_overview'):
                            st.markdown(f"**Market Overview:** {ai_response['market_overview']}")

                        # Key Factors
                        if isinstance(ai_response, dict) and ai_response.get('key_factors'):
                            st.markdown("**Key Market Factors:**")
                            for factor in ai_response['key_factors']:
                                st.markdown(f"• {factor}")

                        # Technical Analysis
                        if isinstance(ai_response, dict) and ai_response.get('technical_analysis'):
                            st.markdown("**📊 Technical Analysis:**")
                            st.info(ai_response['technical_analysis'])

                        # Risk Assessment
                        if isinstance(ai_response, dict) and ai_response.get('risk_assessment'):
                            st.markdown("**⚠️ Risk Assessment:**")
                            st.warning(ai_response['risk_assessment'])

                        # Market Outlook
                        if isinstance(ai_response, dict) and ai_response.get('outlook'):
                            st.markdown("**🔮 Market Outlook:**")
                            st.success(ai_response['outlook'])

                        # Confidence Level
                        if isinstance(ai_response, dict) and ai_response.get('confidence_level'):
                            confidence_color = {
                                'High': '🟢',
                                'Medium': '🟡',
                                'Low': '🔴'
                            }.get(ai_response['confidence_level'], '⚪')
                            st.markdown(f"**🎯 Confidence Level:** {confidence_color} {ai_response['confidence_level']}")

                        # Research Sources
                        if 'web_sources' in result and result['web_sources']:
                            st.markdown("### 🌐 Research Sources")
                            for i, source in enumerate(result['web_sources'][:max_results]):
                                with st.expander(f"📄 Source {i+1}: {source.get('source', 'Unknown')}", expanded=False):
                                    st.markdown(f"**URL:** {source.get('url', 'N/A')}")
                                    st.markdown(f"**Summary:** {source.get('snippet', 'No description available')}")

                        # Recommendations
                        if 'recommendations' in result and result['recommendations']:
                            st.markdown("### 💡 AI Recommendations")
                            for rec in result['recommendations']:
                                st.markdown(f"• {rec}")

                        # Metrics Grid
                        st.markdown("### � Analysis Metrics")
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("Sources Analyzed", len(result.get('web_sources', [])))
                        with col2:
                            st.metric("Research Method", "AI + Web Search")
                        with col3:
                            st.metric("Analysis Depth", f"Top {max_results}")
                        with col4:
                            st.metric("Generated", datetime.now().strftime("%H:%M:%S"))

                    # Add to history
                    st.session_state.ai_chat_history.append({
                        'role': 'assistant',
                        'content': response_placeholder,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                    st.success("✅ Analysis completed! Results displayed above.")
                    st.rerun()

                else:
                    animation_placeholder.empty()
                    error_msg = result.get("error", "Unknown error") if result else "Failed to connect to AI service"
                    st.error(f"❌ Analysis failed: {error_msg}")

        # Clear chat history
        if st.session_state.ai_chat_history:
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.ai_chat_history = []
                    st.success("History cleared!")
                    st.rerun()

        # Capabilities Section
        with st.expander("ℹ️ AI Analyst Capabilities", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                **🔍 Research Capabilities:**
                - Real-time market data analysis
                - Multi-source news aggregation
                - Technical indicator evaluation
                - Risk assessment modeling
                - Trend prediction algorithms
                """)

            with col2:
                st.markdown("""
                **📊 Analysis Types:**
                - Forex market analysis
                - Stock market research
                - Cryptocurrency trends
                - Economic indicator impact
                - Trading strategy evaluation
                """)

            st.markdown("""
            **💡 Example Queries:**
            - "Analyze EURUSD technical indicators"
            - "What are Bitcoin's market trends?"
            - "Research impact of Fed decisions"
            - "Compare stock market sectors"
            - "Analyze commodity price movements"
            """)

    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit, Flask, and modern trading analysis tools*")

if __name__ == "__main__":
    main()