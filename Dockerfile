FROM python:3.9-slim

WORKDIR /app

# Install system dependencies needed by some Python packages (like grpcio)
RUN apt-get update && \
    apt-get install -y gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY utils.py .
COPY templates/ templates/

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Run app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120", "--log-level", "info", "app:app"]
