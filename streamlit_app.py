import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import logging
import re
from typing import Dict, Any, Optional
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

# Configure page with Perplexity-style settings
st.set_page_config(
    page_title="Trading Strategy Backtester",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API base URL
import os
if os.getenv('DOCKER_ENV'):
    API_BASE = "http://trading-backtester:3000"
    DISPLAY_API_BASE = "http://localhost:3000"
else:
    API_BASE = "http://localhost:3000"
    DISPLAY_API_BASE = "http://localhost:3000"

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
    if 'unsafe_allow_html' in kwargs and kwargs['unsafe_allow_html']:
        # Only allow specific safe HTML elements
        safe_content = sanitize_html(content)
        st.markdown(safe_content, **kwargs)
    else:
        st.markdown(content, **kwargs)

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
    """Render home page with security validations"""
    # Header
    st.markdown("""
    <div class="perplexity-header">
        <h1>⚡ Trading Strategy Backtester</h1>
        <p>Advanced market analysis powered by AI and real-time data</p>
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
    """Render AI agent page with enhanced security"""
    # AI Agent interface (Perplexity-style)
    st.markdown("""
    <div class="perplexity-header">
        <h1>🤖 AI Financial Analyst</h1>
        <p>Advanced market research powered by AI and real-time data</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []

    # Chat History with sanitization
    if st.session_state.ai_chat_history:
        st.markdown("### 💬 Research History")
        for i, message in enumerate(st.session_state.ai_chat_history):
            if message['role'] == 'user':
                safe_content = sanitize_html(message.get('content', ''))
                st.markdown(f"""
                <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #2196f3;">
                    <strong>👤 Your Question:</strong><br>{safe_content}
                </div>
                """, unsafe_allow_html=True)
            else:
                with st.expander(f"🤖 AI Analysis #{i//2 + 1}", expanded=False):
                    safe_content = sanitize_html(message.get('content', ''))
                    st.markdown(safe_content)

    # Input Section with validation
    st.markdown("### 🔍 Ask Your Financial Question")

    with st.form("ai_form"):
        user_query_input = st.text_area(
            "",
            placeholder="e.g., 'What are the current market trends for EURUSD?', 'Analyze Bitcoin's technical indicators'",
            height=80,
            label_visibility="collapsed",
            max_chars=MAX_QUERY_LENGTH
        )

        max_results = st.selectbox("Research Depth", [3, 5, 7, 10], index=1)

        if st.form_submit_button("🚀 Analyze Markets", use_container_width=True):
            if validate_query(user_query_input) and user_query_input.strip():
                # Add to chat history with sanitization
                safe_query = sanitize_html(user_query_input.strip())
                st.session_state.ai_chat_history.append({
                    'role': 'user',
                    'content': safe_query,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                # Loading animation
                with st.spinner("AI Analyst is researching..."):
                    time.sleep(2)  # Simulate processing

                    research_payload = {
                        "query": safe_query,
                        "max_results": max_results
                    }

                    result = make_api_call("/api/ai/research", method="POST", data=research_payload)

                    if result and result.get("success"):
                        ai_response = result.get("analysis", {})

                        # Format response with sanitization
                        response_content = f"""
**Market Overview:** {sanitize_html(ai_response.get('market_overview', 'Analysis generated'))}

**Key Factors:**
"""
                        for factor in ai_response.get('key_factors', []):
                            response_content += f"• {sanitize_html(str(factor))}\n"

                        response_content += f"""
**Technical Analysis:** {sanitize_html(ai_response.get('technical_analysis', 'N/A'))}

**Risk Assessment:** {sanitize_html(ai_response.get('risk_assessment', 'N/A'))}

**Market Outlook:** {sanitize_html(ai_response.get('outlook', 'N/A'))}

**Confidence:** {sanitize_html(ai_response.get('confidence_level', 'Medium'))}
"""

                        # Add AI response to history
                        st.session_state.ai_chat_history.append({
                            'role': 'assistant',
                            'content': response_content,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                        st.success("✅ Analysis completed!")
                        logger.info(f"AI analysis completed for query: {safe_query[:50]}...")
                        st.rerun()
                    else:
                        error_msg = result.get("error", "Analysis failed") if result else "Failed to connect to AI service"
                        st.error(f"❌ {error_msg}")
                        logger.error(f"AI analysis failed: {error_msg}")
            else:
                st.error("❌ Invalid query. Please enter a valid question.")

    # Clear history
    if st.session_state.ai_chat_history:
        if st.button("🗑️ Clear History"):
            st.session_state.ai_chat_history = []
            st.success("History cleared!")
            logger.info("AI chat history cleared")
            st.rerun()

if __name__ == "__main__":
    main()