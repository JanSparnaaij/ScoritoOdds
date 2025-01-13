# Base Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers \
    PORT=8000  

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libenchant-2-2 \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright \
    && PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers playwright install --with-deps

# Set working directory and copy application files
WORKDIR /app
COPY . /app

# Expose the application port
EXPOSE 8000

# Start the web application
CMD ["sh", "-c", "flask db upgrade && hypercorn --bind 0.0.0.0:${PORT} run:app"]
