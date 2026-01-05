# Dockerfile for CADVI Auto-Trader
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 300 -r requirements.txt

# Copy all application files
COPY . .

# Create directory for logs
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the auto-trader - AGGRESSIVE GROWTH MODE
CMD ["python", "auto_trader.py", "--live", "--continuous", "--interval", "15", "--max-positions", "4", "--min-score", "75", "--confirm"]
