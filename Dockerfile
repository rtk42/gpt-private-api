FROM python:3.9-slim

WORKDIR /app

# Install Redis
RUN apt-get update && \
    apt-get install -y redis-server && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY utils.py .
COPY templates/ templates/

# Create directory for Flask sessions
RUN mkdir -p flask_session

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV REDIS_URL=redis://localhost:6379

# Create a script to start both Redis and Gunicorn
RUN echo '#!/bin/bash\nredis-server --daemonize yes\ngunicorn --bind 0.0.0.0:8080 --workers 1 --threads 4 --timeout 120 --log-level info app:app' > /app/start.sh && \
    chmod +x /app/start.sh

CMD ["/app/start.sh"] 