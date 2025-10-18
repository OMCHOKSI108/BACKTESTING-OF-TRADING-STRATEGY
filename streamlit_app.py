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
            response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid response from server")
        return None

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
            "HINDALCO.NS", "GRASIM.NS", "ADANIENT.NS", "CIPLA.NS", "DRREDDY.NS",
            "EICHERMOT.NS", "BPCL.NS", "INDUSINDBK.NS", "BRITANNIA.NS", "TATASTEEL.NS"
        ],
        "FX": [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X",
            "NZDUSD=X", "EURJPY=X", "GBPJPY=X", "EURGBP=X", "EURCHF=X", "EURAUD=X",
            "EURNZD=X", "EURCAD=X", "GBPCHF=X", "GBPAUD=X", "GBPNZD=X", "GBPCAD=X",
            "AUDJPY=X", "AUDCHF=X", "AUDNZD=X", "AUDCAD=X", "NZDJPY=X", "NZDCHF=X",
            "NZDCAD=X", "CADJPY=X", "CADCHF=X", "CHFJPY=X", "USDINR=X", "USDSGD=X",
            "USDHKD=X", "USDMXN=X", "USDBRL=X", "USDRUB=X", "USDCNY=X", "USDZAR=X",
            "USDTRY=X", "USDKRW=X", "USDTHB=X", "USDPLN=X"
        ],
        "CRYPTO": [
            "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD", "SOL-USD",
            "DOGE-USD", "DOT-USD", "AVAX-USD", "SHIB-USD", "MATIC-USD", "LTC-USD",
            "UNI-USD", "LINK-USD", "BCH-USD", "ALGO-USD", "XLM-USD", "VET-USD",
            "ICP-USD", "ETC-USD", "FIL-USD", "TRX-USD", "ATOM-USD", "HBAR-USD",
            "NEAR-USD", "FTM-USD", "MANA-USD", "SAND-USD", "THETA-USD", "EGLD-USD",
            "XTZ-USD", "AXS-USD", "FLOW-USD", "ENJ-USD", "CHZ-USD", "KLAY-USD",
            "ZIL-USD", "COMP-USD", "YFI-USD", "SUSHI-USD"
        ]
    }

    # Symbol selector based on exchange
    st.sidebar.subheader("📊 Symbol Selection")
    available_symbols = symbols_by_exchange.get(exchange_code, ["AAPL"])
    
    symbol = st.sidebar.selectbox(
        "Symbol",
        available_symbols,
        help=f"Select from top 40 symbols in {selected_exchange}"
    )

    # Set market type based on exchange
    market_type_mapping = {
        "US": "US Stocks",
        "NSE": "Indian Stocks", 
        "FX": "Forex",
        "CRYPTO": "Crypto"
    }
    market_type = market_type_mapping.get(exchange_code, "US Stocks")

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

    # Date range selector
    st.sidebar.subheader("📅 Date Range")
    col1, col2 = st.sidebar.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365),
            help="Start date for data analysis"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            help="End date for data analysis"
        )

    # Initial balance
    initial_balance = st.sidebar.number_input(
        "Initial Balance ($)",
        value=100000,
        min_value=1000,
        step=1000,
        help="Starting portfolio balance"
    )

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Gathering", "⚡ Strategy Testing", "📈 Results", "📋 Reports"])

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

    # Tab 2: Strategy Testing
    with tab2:
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

    # Tab 3: Results
    with tab3:
        st.header("Results")

        # Display last strategy results
        if "last_results" in st.session_state:
            results = st.session_state.last_results
            strategy_id = st.session_state.get("last_strategy", "Unknown")

            # Key metrics in columns
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Net P&L", f"${results.get('net_profit_loss', 0):,.2f}")
            with col2:
                st.metric("Win Rate", f"{results.get('win_rate', 0):.1f}%")
            with col3:
                st.metric("Total Trades", results.get('total_trades', 0))
            with col4:
                st.metric("Sharpe Ratio", f"{results.get('sharpe_ratio', 0):.2f}")

            # Additional metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Max Drawdown", f"${results.get('max_drawdown', 0):,.2f}")
            with col2:
                st.metric("Profit Factor", f"{results.get('profit_factor', 0):.2f}")
            with col3:
                st.metric("Avg Trade P&L", f"${results.get('average_trade_pnl', 0):,.2f}")
            with col4:
                st.metric("Final Balance", f"${results.get('final_balance', 0):,.2f}")

            # Equity curve placeholder
            st.subheader("Equity Curve")
            if "equity_curve" in results and results["equity_curve"]:
                equity_df = pd.DataFrame({
                    "Trade": range(len(results["equity_curve"])),
                    "Equity": results["equity_curve"]
                })
                st.line_chart(equity_df.set_index("Trade"))
            else:
                st.info("Equity curve data not available")

        # Display comparison results
        if "comparison_results" in st.session_state:
            st.subheader("⚖️ Strategy Comparison")

            comparison = st.session_state.comparison_results.get("comparison", {})
            individual_results = st.session_state.comparison_results.get("individual_results", [])

            if comparison:
                # Best strategy highlight
                best_strategy = comparison.get("best_strategy", "N/A")
                best_pnl = comparison.get("best_net_profit", 0)

                st.success(f"🏆 Best Performing Strategy: {best_strategy} (${best_pnl:,.2f} P&L)")

                # Comparison table
                comp_data = {
                    "Strategy": comparison.get("strategies", []),
                    "Net P&L": comparison.get("net_profits", []),
                    "Win Rate": comparison.get("win_rates", []),
                    "Sharpe Ratio": comparison.get("sharpe_ratios", []),
                    "Max Drawdown": comparison.get("max_drawdowns", [])
                }

                comp_df = pd.DataFrame(comp_data)
                st.dataframe(comp_df, use_container_width=True)

    # Tab 4: Reports
    with tab4:
        st.header("Reports")

        if "last_results" in st.session_state:
            st.subheader("📄 Generate PDF Report")

            if st.button("Generate Strategy Report", use_container_width=True):
                with st.spinner("Generating PDF report..."):
                    report_payload = {
                        "symbol": symbol,
                        "strategy_name": f"Strategy {st.session_state.get('last_strategy', 'Unknown')}",
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

            if st.button("Generate Comparison Report", use_container_width=True):
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

    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit, Flask, and modern trading analysis tools*")

if __name__ == "__main__":
    main()