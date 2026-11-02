# Single-stage build for Django application
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY config/ ./config/
COPY library/ ./library/
COPY templates/ ./templates/
COPY static/ ./static/
COPY manage.py .
COPY .env.example .env.example

# Create staticfiles directory and collect static
RUN mkdir -p staticfiles media && \
    python manage.py collectstatic --noinput --clear && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 2445

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:2445/health/')" || exit 1

# Run Django with gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:2445", "--workers", "3", "--timeout", "120"]