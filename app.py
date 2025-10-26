#!/usr/bin/env python3
"""
Enhanced Trading Strategy Backtester
Main application entry point
"""

import os
import sys
import subprocess
from app import create_app

def run_flask_app():
    """Run the Flask backend application"""
    print("🚀 Starting Enhanced Trading Strategy Backtester...")
    print("🔧 Backend: Flask API Server")
    print("🌐 API available at: http://localhost:3000")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    # Create and run Flask app
    app = create_app()
    app.run(host='0.0.0.0', port=3000, debug=os.getenv('FLASK_ENV') == 'development')

def run_streamlit_app():
    """Run the Streamlit frontend application"""
    print("🚀 Starting Enhanced Trading Strategy Backtester...")
    print("📊 Frontend: Streamlit Dashboard")
    print("🌐 UI available at: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    # Run Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

def run_both():
    """Run both Flask backend and Streamlit frontend"""
    print("🚀 Starting Enhanced Trading Strategy Backtester...")
    print("🔧 Backend: Flask API Server")
    print("📊 Frontend: Streamlit Dashboard")
    print("🌐 API: http://localhost:3000")
    print("🌐 UI: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop both servers")
    print("-" * 50)

    # Start Flask in background
    flask_process = subprocess.Popen([
        sys.executable, "-m", "flask", "run", "--host=0.0.0.0", "--port=3000"
    ], cwd=os.path.dirname(__file__), env={**os.environ, "FLASK_APP": "app"})

    # Wait a moment for Flask to start
    import time
    time.sleep(3)

    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
    finally:
        flask_process.terminate()
        flask_process.wait()
        print("✅ All servers stopped")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "flask":
            run_flask_app()
        elif mode == "streamlit":
            run_streamlit_app()
        elif mode == "both":
            run_both()
        else:
            print("Usage: python app.py [flask|streamlit|both]")
            print("Default: runs Flask backend only")
            run_flask_app()
    else:
        # Default: run Flask backend
        run_flask_app()