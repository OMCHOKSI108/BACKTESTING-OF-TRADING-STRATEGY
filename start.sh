#!/bin/bash
# Startup script to run both Flask and Streamlit applications

# Start Flask application with gunicorn in background
echo "Starting Flask application..."
gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 --worker-class sync --worker-tmp-dir /dev/shm --log-level info wsgi:app &

# Wait a moment for Flask to start
sleep 5

# Start Streamlit application
echo "Starting Streamlit application..."
streamlit run streamlit_app_ai_clean.py --server.port 8502 --server.address 0.0.0.0 --server.headless true --server.runOnSave false &

# Wait for both processes
wait