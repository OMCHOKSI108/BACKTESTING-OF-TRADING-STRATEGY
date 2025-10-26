# Use Python 3.11 slim image for security
FROM python:3.11-slim

# Add security labels
LABEL maintainer="Trading Backtester Team"
LABEL version="1.0.0"
LABEL description="Secure Trading Strategy Backtester Application"

# Set working directory
WORKDIR /app

# Install security updates and required system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        && rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser -d /home/appuser appuser && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser /app

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies as non-root user
USER appuser
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Create data directories with proper permissions
RUN mkdir -p app/data/raw app/data/processed app/data/trade_history app/reports && \
    chmod 755 app/data/raw app/data/processed app/data/trade_history app/reports

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Expose ports
EXPOSE 3000 8501

# Set environment variables for security
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Use gunicorn for production WSGI server
USER root
RUN pip install gunicorn
USER appuser

# Copy startup script and make it executable
COPY --chown=appuser:appuser start.sh .
RUN chmod +x start.sh

# Default command with security options
CMD ["./start.sh"]