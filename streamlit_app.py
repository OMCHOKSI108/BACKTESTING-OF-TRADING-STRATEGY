import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import logging
import re
from typing import Dict, Any, Optional
import bleach
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('streamlit_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_SYMBOL_LENGTH = 20
MAX_QUERY_LENGTH = 500
ALLOWED_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"]
ALLOWED_MARKET_TYPES = ["US Stocks", "Indian Stocks", "Forex", "Crypto"]

# Configure page with elegant modern settings
st.set_page_config(
    page_title="Trading Strategy Backtester | AI-Powered Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API base URL
import os
if os.getenv('DOCKER_ENV'):
    API_BASE = "http://localhost:8000"  # Within container, use localhost
    DISPLAY_API_BASE = "http://localhost:8000"
else:
    API_BASE = "http://localhost:8000"
    DISPLAY_API_BASE = "http://localhost:8000"

def sanitize_html(text: str) -> str:
    """Sanitize HTML content to prevent XSS attacks"""
    if not isinstance(text, str):
        return ""
    # Escape HTML characters
    return html.escape(text)

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    if not symbol or not isinstance(symbol, str):
        return False
    if len(symbol) > MAX_SYMBOL_LENGTH:
        return False
    # Allow alphanumeric, dots, hyphens, and forward slashes
    if not re.match(r'^[A-Za-z0-9./-]+$', symbol):
        return False
    return True

def validate_query(query: str) -> bool:
    """Validate user query input"""
    if not query or not isinstance(query, str):
        return False
    if len(query) > MAX_QUERY_LENGTH:
        return False
    # Basic validation - could be enhanced with more sophisticated checks
    return True

def validate_timeframe(timeframe: str) -> bool:
    """Validate timeframe parameter"""
    return timeframe in ALLOWED_TIMEFRAMES

def validate_market_type(market_type: str) -> bool:
    """Validate market type parameter"""
    return market_type in ALLOWED_MARKET_TYPES

def safe_markdown(content: str, **kwargs) -> None:
    """Safe markdown rendering with HTML sanitization"""
    if not isinstance(content, str):
        content = str(content)

    # Remove any unsafe_allow_html from kwargs for security
    safe_kwargs = {k: v for k, v in kwargs.items() if k != 'unsafe_allow_html'}

    # Use bleach to clean any HTML content
    clean_content = bleach.clean(content, tags=['b', 'i', 'em', 'strong', 'code', 'pre'], strip=True)

    st.markdown(clean_content, **safe_kwargs)

def safe_write(content: Any) -> None:
    """Safe content writing with sanitization"""
    if isinstance(content, str):
        # Clean any HTML and limit length
        clean_content = bleach.clean(content, tags=[], strip=True)
        if len(clean_content) > 10000:  # Limit output length
            clean_content = clean_content[:10000] + "..."
        st.write(clean_content)
    else:
        st.write(content)

def make_api_call(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make API call with error handling and logging"""
    try:
        url = f"{API_BASE}{endpoint}"
        logger.info(f"Making {method} request to: {url}")

        if method == "POST":
            response = requests.post(url, json=data, timeout=60)
        else:
            response = requests.get(url, timeout=60)

        response.raise_for_status()
        result = response.json()
        logger.info(f"API call successful: {endpoint}")
        return result

    except requests.exceptions.Timeout:
        error_msg = f"Request timeout for endpoint: {endpoint}"
        logger.error(error_msg)
        return {"success": False, "error": "Request timed out. Please try again."}
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": "Network error. Please check your connection."}
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON response: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": "Invalid response from server"}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": "An unexpected error occurred"}

def get_currency_symbol(market_type):
    """Get currency symbol based on market type"""
    if market_type in ["US Stocks", "Forex", "Crypto"]:
        return "$"
    elif market_type == "Indian Stocks":
        return "₹"
    else:
        return "$"

def main():
    """Main application function with security enhancements"""
    logger.info("Starting Trading Strategy Backtester application")

    # Add elegant custom CSS styling
    st.markdown("""
    <style>
        /* Light / Whiteish Professional Color Scheme */
        :root {
            --primary-gradient: linear-gradient(135deg, #e6f0ff 0%, #ffffff 100%);
            --success-gradient: linear-gradient(135deg, #e9f7ef 0%, #f0fff6 100%);
            --danger-gradient: linear-gradient(135deg, #fff5f5 0%, #fffaf0 100%);
            --info-gradient: linear-gradient(135deg, #eef6ff 0%, #f8feff 100%);
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #0b2545;
            --text-secondary: #556676;
            --accent-blue: #2b7cff;
            --accent-purple: #6b8cff;
            --muted: #9aa8b2;
        }

        /* Main Background */
        .stApp {
            background: var(--bg-color);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
        }
        
        /* Elegant Header Styling */
        .perplexity-header {
            background: var(--card-bg);
            padding: 2rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
            margin-bottom: 1.25rem;
            text-align: center;
            animation: fadeInDown 0.6s ease-in-out;
            border: 1px solid rgba(11, 37, 69, 0.04);
        }

        .perplexity-header h1 {
            color: var(--text-primary);
            font-size: 2.25rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }

        .perplexity-header p {
            color: var(--muted);
            font-size: 1rem;
            margin-top: 0.4rem;
            font-weight: 400;
        }
        
        /* Search Container */
        .search-container {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1.25rem;
            border: 1px solid rgba(11, 37, 69, 0.04);
            box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
        }
        
        /* Card Styling */
        .info-card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1rem;
            margin: 0.8rem 0;
            border: 1px solid rgba(11, 37, 69, 0.04);
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }
        
        .info-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
        }
        
        /* AI Response Card */
        .ai-response {
            background: #fbfdff;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.8rem 0;
            border-left: 4px solid var(--accent-blue);
            box-shadow: 0 6px 18px rgba(43, 124, 255, 0.06);
        }
        
        /* User Query Card */
        .user-query {
            background: #ffffff;
            border-radius: 10px;
            padding: 0.85rem;
            margin: 0.8rem 0;
            border-left: 4px solid #2b7cff;
            box-shadow: 0 6px 14px rgba(11, 37, 69, 0.03);
        }
        
        /* Button Styling */
        .stButton > button {
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.1rem;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.18s ease;
            box-shadow: 0 6px 18px rgba(43, 124, 255, 0.12);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5);
        }
        
        /* Input Field Styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: #fbfdff;
            border: 1px solid rgba(11, 37, 69, 0.06);
            border-radius: 8px;
            color: var(--text-primary);
            padding: 0.75rem;
            font-size: 0.95rem;
            transition: all 0.18s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 8px 26px rgba(43, 124, 255, 0.06);
            background: #ffffff;
        }
        
        /* Selectbox Styling */
        .stSelectbox > div > div {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 10px;
        }
        
        /* Expander Styling */
        .streamlit-expanderHeader {
            background: rgba(102, 126, 234, 0.1);
            border-radius: 10px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        /* Metrics Display */
        .metric-container {
            background: linear-gradient(135deg, rgba(17, 153, 142, 0.2) 0%, rgba(56, 239, 125, 0.2) 100%);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(56, 239, 125, 0.3);
            box-shadow: 0 4px 15px rgba(17, 153, 142, 0.2);
        }
        
        /* Spinner Animation */
        .stSpinner > div {
            border-top-color: var(--accent-purple) !important;
        }
        
        /* Success/Error Messages */
        .stSuccess {
            background: var(--success-gradient);
            color: white;
            border-radius: 10px;
            padding: 1rem;
            font-weight: 500;
        }
        
        .stError {
            background: var(--danger-gradient);
            color: white;
            border-radius: 10px;
            padding: 1rem;
            font-weight: 500;
        }
        
        .stInfo {
            background: var(--info-gradient);
            color: white;
            border-radius: 10px;
            padding: 1rem;
            font-weight: 500;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid rgba(11, 37, 69, 0.04);
            padding-top: 1rem;
        }
        
        section[data-testid="stSidebar"] .stButton > button {
            background: rgba(102, 126, 234, 0.2);
            border: 1px solid rgba(102, 126, 234, 0.3);
        }
        
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: var(--primary-gradient);
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 1.25rem;
            margin-top: 2rem;
            border-top: 1px solid rgba(11, 37, 69, 0.04);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        /* Animations */
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        /* Responsive Typography */
    h1 { color: var(--text-primary); font-weight: 700; }
    h2 { color: var(--text-primary); font-weight: 600; }
    h3 { color: var(--text-primary); font-weight: 600; }
    p { color: var(--text-secondary); line-height: 1.6; }
        
        /* Data Table Styling */
        .dataframe {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--accent-purple);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-blue);
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'home'
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    # Sidebar with validation
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        # Navigation
        st.markdown("**Navigation**")
        nav_options = {
            "🏠 Home": "home",
            "📊 Data Gathering": "data",
            "📋 Dataset View": "dataset",
            "⚡ Strategy Testing": "strategy",
            "📈 Results": "results",
            "🤖 AI Agent": "ai"
        }

        for label, view in nav_options.items():
            if st.button(label, key=f"nav_{view}",
                        use_container_width=True,
                        type="primary" if st.session_state.current_view == view else "secondary"):
                st.session_state.current_view = view
                logger.info(f"Navigation changed to: {view}")
                st.rerun()

        st.markdown("---")

        # Quick Settings with validation
        st.markdown("**Quick Settings**")
        symbol_input = st.text_input("Symbol", value="AAPL", key="sidebar_symbol", max_chars=MAX_SYMBOL_LENGTH)
        symbol = symbol_input if validate_symbol(symbol_input) else "AAPL"

        market_type = st.selectbox("Market", ALLOWED_MARKET_TYPES, key="sidebar_market")
        timeframe = st.selectbox("Timeframe", ALLOWED_TIMEFRAMES, key="sidebar_timeframe")

        if not validate_symbol(symbol):
            st.warning("⚠️ Invalid symbol format. Using default.")
        if not validate_market_type(market_type):
            st.warning("⚠️ Invalid market type.")
        if not validate_timeframe(timeframe):
            st.warning("⚠️ Invalid timeframe.")

    # Main Content
    try:
        if st.session_state.current_view == 'home':
            render_home_page()
        elif st.session_state.current_view == 'data':
            render_data_page()
        elif st.session_state.current_view == 'dataset':
            render_dataset_page()
        elif st.session_state.current_view == 'strategy':
            render_strategy_page()
        elif st.session_state.current_view == 'results':
            render_results_page()
        elif st.session_state.current_view == 'ai':
            render_ai_page()
        else:
            st.error("❌ Invalid page view")
            logger.warning(f"Invalid view requested: {st.session_state.current_view}")

    except Exception as e:
        logger.error(f"Error in main content rendering: {str(e)}")
        st.error("❌ An error occurred while rendering the page. Please refresh and try again.")

    # Footer
    st.markdown("""
    <div class="footer">
        <p>Built with ❤️ using Streamlit, Flask, and advanced trading analysis tools</p>
    </div>
    """, unsafe_allow_html=True)

def render_home_page():
    """Render home page with security validations and elegant design"""
    # Header with modern gradient design
    st.markdown("""
    <div class="perplexity-header">
        <h1>📈 Trading Strategy Backtester</h1>
        <p>Advanced quantitative analysis powered by AI and real-time market data</p>
    </div>
    """, unsafe_allow_html=True)

    # Search Interface with validation
    st.markdown('<div class="search-container">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        with st.form("search_form"):
            query_input = st.text_input(
                "",
                placeholder="Enter trading symbol (e.g., AAPL, EURUSD, BTC) or analysis query...",
                key="main_search",
                label_visibility="collapsed",
                max_chars=MAX_QUERY_LENGTH
            )

            submitted = st.form_submit_button("🔍 Analyze", use_container_width=True)

            if submitted:
                if validate_query(query_input) and query_input.strip():
                    st.session_state.search_query = sanitize_html(query_input.strip())
                    st.session_state.current_view = 'results'
                    logger.info(f"Search query submitted: {query_input[:50]}...")
                    st.rerun()
                else:
                    st.error("❌ Invalid query. Please enter a valid search term.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Quick Actions
    st.markdown('<div class="results-container">', unsafe_allow_html=True)

    st.markdown("### 🚀 Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Popular Stocks", use_container_width=True):
            st.session_state.search_query = "AAPL MSFT GOOGL TSLA"
            st.session_state.current_view = 'dataset'
            logger.info("Quick action: Popular Stocks")
            st.rerun()

    with col2:
        if st.button("💱 Forex Pairs", use_container_width=True):
            st.session_state.search_query = "EURUSD GBPUSD USDJPY"
            st.session_state.current_view = 'dataset'
            logger.info("Quick action: Forex Pairs")
            st.rerun()

    with col3:
        if st.button("₿ Crypto", use_container_width=True):
            st.session_state.search_query = "BTC ETH BNB"
            st.session_state.current_view = 'dataset'
            logger.info("Quick action: Crypto")
            st.rerun()

    with col4:
        if st.button("🤖 AI Analysis", use_container_width=True):
            st.session_state.current_view = 'ai'
            logger.info("Quick action: AI Analysis")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def render_data_page():
    """Render data gathering page with validation"""
    st.markdown("""
    <div class="results-container">
        <h2>📊 Data Gathering</h2>
    </div>
    """, unsafe_allow_html=True)

    # Data gathering interface with validation
    with st.form("data_form"):
        symbol_input = st.text_input("Symbol", value=st.session_state.get('sidebar_symbol', 'AAPL'), max_chars=MAX_SYMBOL_LENGTH)
        symbol = symbol_input if validate_symbol(symbol_input) else st.session_state.get('sidebar_symbol', 'AAPL')

        market_options = ["US Stocks", "Indian Stocks", "Forex", "Crypto"]
        market = st.selectbox("Market Type", market_options,
                            index=market_options.index(st.session_state.get('sidebar_market', 'US Stocks')))

        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
        end_date = st.date_input("End Date", datetime.now())

        timeframe_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"]
        timeframe = st.selectbox("Timeframe", timeframe_options,
                               index=timeframe_options.index(st.session_state.get('sidebar_timeframe', '1d')))

        if st.form_submit_button("🔍 Gather Data", use_container_width=True):
            if not validate_symbol(symbol):
                st.error("❌ Invalid symbol format")
                return
            if not validate_market_type(market):
                st.error("❌ Invalid market type")
                return
            if not validate_timeframe(timeframe):
                st.error("❌ Invalid timeframe")
                return

            with st.spinner("Fetching market data..."):
                data_payload = {
                    "symbol": symbol,
                    "market_type": market,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "timeframe": timeframe
                }

                result = make_api_call("/api/data/gather", method="POST", data=data_payload)

                if result.get("success"):
                    st.success(f"✅ Successfully gathered {result.get('data_points', 0)} data points!")
                    logger.info(f"Data gathered successfully: {symbol}, {result.get('data_points', 0)} points")
                else:
                    st.error(f"❌ {result.get('error', 'Failed to gather data')}")
                    logger.error(f"Data gathering failed: {result.get('error', 'Unknown error')}")

def render_dataset_page():
    """Render dataset viewer page with validation"""
    st.markdown("""
    <div class="results-container">
        <h2>📋 Dataset Viewer</h2>
    </div>
    """, unsafe_allow_html=True)

    # Dataset viewer with validation
    symbol_input = st.text_input("Symbol", value=st.session_state.get('sidebar_symbol', 'AAPL'), max_chars=MAX_SYMBOL_LENGTH)
    symbol = symbol_input if validate_symbol(symbol_input) else st.session_state.get('sidebar_symbol', 'AAPL')

    timeframe_options = ["1d", "1h", "1w"]
    timeframe = st.selectbox("Timeframe", timeframe_options,
                           index=timeframe_options.index(st.session_state.get('sidebar_timeframe', '1d')))

    if st.button("📊 Load Data"):
        if not validate_symbol(symbol):
            st.error("❌ Invalid symbol format")
            return
        if not validate_timeframe(timeframe):
            st.error("❌ Invalid timeframe")
            return

        preview_result = make_api_call(f"/api/data/preview?symbol={symbol}&timeframe={timeframe}&limit=50")

        if preview_result.get("success"):
            data_records = preview_result.get("data", [])
            if data_records:
                df = pd.DataFrame(data_records)
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Download CSV", df.to_csv(index=False), "data.csv")
                logger.info(f"Dataset loaded: {symbol}, {len(data_records)} records")
            else:
                st.warning("No data available")
        else:
            st.error("Failed to load data")
            logger.error(f"Dataset loading failed: {preview_result.get('error', 'Unknown error')}")

def render_strategy_page():
    """Render strategy testing page with validation"""
    st.markdown("""
    <div class="results-container">
        <h2>⚡ Strategy Testing</h2>
    </div>
    """, unsafe_allow_html=True)

    # Strategy testing with validation
    strategies = ["SMA Crossover", "RSI Mean Reversion", "Bollinger Bands", "MACD Crossover", "Multi-Indicator"]

    selected_strategy = st.selectbox("Select Strategy", strategies)

    symbol_input = st.text_input("Symbol", value=st.session_state.get('sidebar_symbol', 'AAPL'), max_chars=MAX_SYMBOL_LENGTH)
    symbol = symbol_input if validate_symbol(symbol_input) else st.session_state.get('sidebar_symbol', 'AAPL')

    if st.button("🚀 Run Strategy"):
        if not validate_symbol(symbol):
            st.error("❌ Invalid symbol format")
            return

        with st.spinner(f"Running {selected_strategy}..."):
            strategy_payload = {
                "symbol": symbol,
                "market_type": st.session_state.get('sidebar_market', 'US Stocks'),
                "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "timeframe": st.session_state.get('sidebar_timeframe', '1d'),
                "initial_balance": 100000
            }

            result = make_api_call(f"/api/strategy/run/{strategies.index(selected_strategy) + 1}",
                                 method="POST", data=strategy_payload)

            if result.get("success"):
                st.session_state.search_results = result.get("results", {})
                st.session_state.current_view = 'results'
                st.success("Strategy executed successfully!")
                logger.info(f"Strategy executed: {selected_strategy} on {symbol}")
                st.rerun()
            else:
                st.error("Strategy execution failed")
                logger.error(f"Strategy execution failed: {result.get('error', 'Unknown error')}")

def render_results_page():
    """Render results page with secure data display"""
    st.markdown("""
    <div class="results-container">
        <h2>📈 Analysis Results</h2>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.search_results:
        results = st.session_state.search_results

        # Main Results Card
        st.markdown('<div class="result-card">', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="result-header">
            <span class="result-icon">📊</span>
            <div>
                <h3 class="result-title">Strategy Performance Analysis</h3>
                <p class="result-meta">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Key Metrics with validation
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            net_pnl = results.get("net_profit_loss", 0)
            if isinstance(net_pnl, (int, float)):
                st.metric("💰 Net P&L", f"${net_pnl:.2f}",
                         delta=f"{(net_pnl/100000)*100:.1f}%" if net_pnl != 0 else "0.0%")

        with col2:
            total_trades = results.get("total_trades", 0)
            if isinstance(total_trades, (int, float)):
                st.metric("📊 Total Trades", int(total_trades))

        with col3:
            win_rate = results.get("win_rate", 0) * 100 if results.get("win_rate") else 0
            if isinstance(win_rate, (int, float)):
                st.metric("🎯 Win Rate", f"{win_rate:.1f}%")

        with col4:
            avg_trade = results.get("average_trade_pnl", 0)
            if isinstance(avg_trade, (int, float)):
                st.metric("📈 Avg Trade", f"${avg_trade:.2f}")

        # Equity Curve with validation
        if "equity_curve" in results:
            equity_curve = results["equity_curve"]
            if equity_curve and isinstance(equity_curve, list) and len(equity_curve) > 0:
                st.subheader("📈 Equity Curve")
                eq_df = pd.DataFrame({
                    "Trade": range(len(equity_curve)),
                    "Equity": equity_curve
                })
                st.line_chart(eq_df.set_index("Trade"))

        st.markdown('</div>', unsafe_allow_html=True)

        # Trade History with validation
        if "trades" in results and results["trades"]:
            trades = results["trades"]
            if isinstance(trades, list) and len(trades) > 0:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("""
                <div class="result-header">
                    <span class="result-icon">📋</span>
                    <h3 class="result-title">Trade History</h3>
                </div>
                """, unsafe_allow_html=True)

                trades_df = pd.DataFrame(trades)
                st.dataframe(trades_df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        logger.info("Results page rendered successfully")
    else:
        st.info("No results available. Run a strategy first.")

def render_ai_page():
    """Render AI agent page with enhanced security and elegant design"""
    # AI Agent interface with modern elegant header
    st.markdown("""
    <div class="perplexity-header">
        <h1>🤖 AI Financial Analyst</h1>
        <p>Professional market research powered by advanced AI and real-time financial data</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []

    # Chat History with enhanced styling
    if st.session_state.ai_chat_history:
        st.markdown("### 💬 Research History")
        for i, message in enumerate(st.session_state.ai_chat_history):
            if message['role'] == 'user':
                safe_content = sanitize_html(message.get('content', ''))
                st.markdown(f"""
                <div class="user-query">
                    <strong>👤 Your Question:</strong><br>
                    <p style="margin-top: 0.5rem; font-size: 1.05rem;">{safe_content}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                with st.expander(f"🤖 AI Analysis #{i//2 + 1} - {message.get('timestamp', '')}", expanded=False):
                    safe_content = sanitize_html(message.get('content', ''))
                    st.markdown(f'<div class="ai-response">{safe_content}</div>', unsafe_allow_html=True)

    # If a recent result exists, show structured sources and provenance
    if 'last_ai_result' in st.session_state and st.session_state.last_ai_result:
        res = st.session_state.last_ai_result
        st.markdown("### 🧾 Latest Research Summary")
        bullets = res.get('summary', [])
        for b in bullets:
            st.markdown(f"- {sanitize_html(b)}")

        st.markdown("### 🔎 Sources & Evidence")
        sources_list = res.get('sources') or []
        # Render each source with an include checkbox so user can resummarize from a subset
        for i, s in enumerate(sources_list):
            title = sanitize_html(s.get('title') or s.get('url'))
            domain = sanitize_html(s.get('domain', ''))
            publish = sanitize_html(s.get('publish_date') or s.get('scrape_timestamp') or '')
            score = s.get('relevance_score', 0)

            # checkbox + expander in a two-column layout
            col_check, col_content = st.columns([0.5, 11])
            include_key = f"include_source_{i}"
            # default include True
            try:
                default_include = True
            except Exception:
                default_include = True

            with col_check:
                included = st.checkbox("", value=default_include, key=include_key)

            with col_content.expander(f"{title} — {domain} — score: {score}"):
                st.markdown(f"**Source:** [{title}]({s.get('url')})")
                excerpt = s.get('main_text') or (s.get('excerpts') and s.get('excerpts')[0]) or s.get('snippet')
                if excerpt:
                    st.write(sanitize_html(excerpt))
                # show raw json for provenance
                st.json(s)

        # Regenerate summary button
        if sources_list:
            if st.button("🔁 Regenerate summary using selected sources"):
                # Gather selected sources
                selected = []
                for i, s in enumerate(sources_list):
                    key = f"include_source_{i}"
                    if st.session_state.get(key, True):
                        # only send relevant fields to the server
                        selected.append({
                            'url': s.get('url'),
                            'title': s.get('title'),
                            'domain': s.get('domain'),
                            'publish_date': s.get('publish_date') or s.get('scrape_timestamp'),
                            'excerpts': s.get('excerpts') or [],
                            'main_text': s.get('main_text')
                        })

                if not selected:
                    st.warning("Select at least one source to regenerate the summary.")
                else:
                    payload = {"query": res.get('query'), "sources": selected}
                    with st.spinner("Regenerating summary from selected sources..."):
                        summary_res = make_api_call("/api/ai/resummarize", method="POST", data=payload)
                        if summary_res and summary_res.get('success'):
                            # Replace last result with new summary
                            st.session_state.last_ai_result = summary_res
                            st.success("✅ Regenerated summary successfully.")
                            st.rerun()
                        else:
                            err = summary_res.get('error') if summary_res else 'Resummarization failed'
                            st.error(f"❌ {err}")

        # Export PDF report for the AI research
        if st.button("💾 Export PDF Report") and res:
            with st.spinner("Generating PDF report..."):
                payload = {"research": res, "title": f"AI Research - {res.get('query', '')}"}
                rpt = make_api_call("/api/report/generate_ai", method="POST", data=payload)
                if rpt and rpt.get("success"):
                    download_url = rpt.get("download_url")
                    st.success("✅ PDF report generated")
                    # Show download link (relative to API base)
                    full_url = f"{DISPLAY_API_BASE}{download_url}"
                    st.markdown(f"[Download PDF report]({full_url})")
                else:
                    st.error(f"Failed to generate PDF: {rpt.get('error') if rpt else 'Unknown error'}")


    # Input Section with elegant design
    st.markdown("### 🔍 Ask Your Financial Question")
    
    st.markdown("""
    <div class="info-card">
        <p style="margin: 0; color: var(--text-primary);">
            <strong>📊 Example Queries:</strong> 
            "Analyze EUR/USD technical trends" • "What are Bitcoin's key resistance levels?" • 
            "Evaluate S&P 500 market conditions" • "Assess gold price outlook"
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("ai_form"):
        user_query_input = st.text_area(
            "",
            placeholder="Enter your financial analysis question here... (e.g., 'What are the current market trends for EUR/USD?')",
            height=100,
            label_visibility="collapsed",
            max_chars=MAX_QUERY_LENGTH
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            max_results = st.selectbox(
                "Research Depth", 
                [3, 5, 7, 10], 
                index=1,
                help="Number of data sources to analyze"
            )

            start_date = st.date_input("Start date (optional)", value=None)
            end_date = st.date_input("End date (optional)", value=None)
            sources = st.multiselect("Sources to include", ["web", "news"], default=["web", "news"]) 
        
        with col2:
            submit_button = st.form_submit_button("🚀 Analyze Markets", use_container_width=True)

        if submit_button:
            if validate_query(user_query_input) and user_query_input.strip():
                # Add to chat history with sanitization
                safe_query = sanitize_html(user_query_input.strip())
                st.session_state.ai_chat_history.append({
                    'role': 'user',
                    'content': safe_query,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                # Professional loading animation
                with st.spinner("🔍 AI Analyst is researching financial markets..."):
                    time.sleep(2)  # Simulate processing

                    research_payload = {
                        "query": safe_query,
                        "max_results": max_results,
                        "start_date": str(start_date) if start_date else None,
                        "end_date": str(end_date) if end_date else None,
                        "sources": sources
                    }

                    result = make_api_call("/api/ai/search_and_cite", method="POST", data=research_payload)

                    if result and result.get("success"):
                        # Save last result to session for rendering sources/summary
                        st.session_state.last_ai_result = result

                        # Build a human-readable summary content
                        summary = result.get("summary", [])
                        summary_md = "\n".join([f"- {sanitize_html(s)}" for s in summary])

                        response_content = f"""
<div style=\"line-height:1.8;\">\n
### ✅ Top Summary\n
{summary_md}\n
### � Top Sources\n
"""
                        # Add a compact list of top sources
                        for s in (result.get("sources") or [])[:5]:
                            title = sanitize_html(s.get('title') or s.get('url'))
                            domain = sanitize_html(s.get('domain', ''))
                            score = s.get('relevance_score', 0)
                            response_content += f"- {title} ({domain}) — score: {score}\n"

                        response_content += "\n</div>"

                        st.session_state.ai_chat_history.append({
                            'role': 'assistant',
                            'content': response_content,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                        st.success("✅ Market analysis completed successfully!")
                        logger.info(f"AI search_and_cite completed for query: {safe_query[:50]}...")
                        st.rerun()
                    else:
                        error_msg = result.get("error", "Analysis failed") if result else "Failed to connect to AI service"
                        st.error(f"❌ {error_msg}")
                        logger.error(f"AI analysis failed: {error_msg}")
            else:
                st.error("❌ Invalid query. Please enter a valid financial question.")

    # Clear history with elegant button
    if st.session_state.ai_chat_history:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.ai_chat_history = []
                st.success("✨ History cleared successfully!")
                logger.info("AI chat history cleared")
                st.rerun()
    
    # Disclaimer footer
    st.markdown("""
    <div class="info-card" style="margin-top: 2rem;">
        <p style="margin: 0; font-size: 0.9rem; color: var(--text-secondary); text-align: center;">
            ⚠️ <strong>Disclaimer:</strong> This AI-powered analysis is for informational and educational purposes only. 
            Not financial advice. Always consult with qualified financial advisors before making investment decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()