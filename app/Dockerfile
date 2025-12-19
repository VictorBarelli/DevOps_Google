# ===========================================
# Production Dockerfile for Cloud Run
# ===========================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=True \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app \
    PORT=8080

WORKDIR $APP_HOME

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . ./

# Expose port
EXPOSE $PORT

# Run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
