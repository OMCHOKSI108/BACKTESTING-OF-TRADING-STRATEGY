# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p app/data/raw app/data/processed app/data/trade_history app/reports

# Expose ports
EXPOSE 3000 8501

# Set environment variables
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Default command: run both Flask and Streamlit (can be overridden by docker-compose)
CMD ["python", "app.py", "both"]