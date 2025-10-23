# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy package and application files
COPY btc_monitor/ ./btc_monitor/
COPY monitor.py .
COPY backtest.py .
COPY test_telegram.py .

# Create directory for logs
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import requests; requests.get('https://api.binance.com/api/v3/ping', timeout=5)" || exit 1

# Run the monitor
CMD ["python", "-u", "monitor.py"]
