# Perplexity-Inspired AI Agent Tab - Clean Code Snippet
# Replace the Tab 6 section in streamlit_app.py with this
import streamlit as st
import requests
import os

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
            margin-bottom: 0.5rem;
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
        .question-card {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
        }
        .question-label {
            font-size: 0.875rem;
            color: #6b7280;
            margin-bottom: 0.25rem;
        }
        .question-text {
            color: #1a1a1a;
            font-size: 1rem;
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

        # Initialize session state
        if 'ai_chat_history' not in st.session_state:
            st.session_state.ai_chat_history = []

        # Chat History
        if st.session_state.ai_chat_history:
            st.markdown("#### 💬 Research History")
            
            for i, message in enumerate(st.session_state.ai_chat_history):
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="question-card">
                        <div class="question-label">Your Question</div>
                        <div class="question-text">{message['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    with st.expander(f"🤖 AI Analysis #{i//2 + 1}", expanded=False):
                        st.markdown(message['content'])
                        if 'timestamp' in message:
                            st.caption(f"📅 {message['timestamp']}")

        # Input Section
        st.markdown("#### 💭 Ask Your Financial Question")

        with st.form(key="ai_chat_form"):
            user_query = st.text_area(
                "",
                placeholder="e.g., 'What are the current market trends for EURUSD?'",
                height=100,
                label_visibility="collapsed"
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                submit_button = st.form_submit_button(
                    "🔍 Analyze Markets",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                max_results = st.selectbox(
                    "Depth",
                    options=[3, 5, 7, 10],
                    index=1
                )

        # AI Interaction
        if submit_button and user_query.strip():
            animation_placeholder = st.empty()
            response_placeholder = st.empty()

            # Clean thinking animation
            with animation_placeholder.container():
                st.markdown("""
                <div class="thinking-animation">
                    <div class="thinking-header">🔍 Researching...</div>
                    <div class="thinking-subtext">Analyzing financial data and market trends</div>
                    <div class="thinking-dots">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                progress_bar = st.progress(0)
                for i in range(100):
                    progress_bar.progress(i + 1)
                    time.sleep(0.02)
                progress_bar.empty()

            animation_placeholder.empty()

            # API call
            result = make_api_call("/api/ai/research", method="POST", data={
                "query": user_query.strip(),
                "max_results": max_results
            })

            if result and result.get("success"):
                # Add to history
                st.session_state.ai_chat_history.append({
                    'role': 'user',
                    'content': user_query.strip(),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                # Display response
                with response_placeholder.container():
                    st.markdown('<div class="response-container">', unsafe_allow_html=True)
                    
                    ai_response = result.get("analysis", {})
                    
                    if isinstance(ai_response, dict):
                        if ai_response.get('market_overview'):
                            st.markdown(f"**Market Overview:** {ai_response['market_overview']}")
                        
                        if ai_response.get('key_factors'):
                            st.markdown("**Key Factors:**")
                            for factor in ai_response['key_factors']:
                                st.markdown(f"• {factor}")
                    
                    # Sources
                    if result.get('web_sources'):
                        st.markdown("#### 🌐 Sources")
                        for i, source in enumerate(result['web_sources'][:max_results]):
                            with st.expander(f"Source {i+1}: {source.get('source', 'Unknown')}", expanded=False):
                                st.markdown(f"**URL:** {source.get('url', 'N/A')}")
                                st.markdown(source.get('snippet', 'No description'))
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Sources", len(result.get('web_sources', [])))
                    with col2:
                        st.metric("Depth", max_results)
                    with col3:
                        st.metric("Method", "AI + Web")
                    with col4:
                        st.metric("Time", datetime.now().strftime("%H:%M"))

                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': response_placeholder,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                st.success("✅ Analysis completed!")
                st.rerun()
            else:
                animation_placeholder.empty()
                st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

        # Clear history button
        if st.session_state.ai_chat_history:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.ai_chat_history = []
                st.success("History cleared!")
                st.rerun()
