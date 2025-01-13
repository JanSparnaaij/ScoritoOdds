# Base Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser

# Create the Playwright browsers directory and set permissions
RUN mkdir -p /ms-playwright-browsers && \
    chown -R appuser:appuser /ms-playwright-browsers

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install system dependencies required by Playwright
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
    libavif-dev \
    libenchant-2-2 \
    libflite1 \
    libgles2-mesa \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-gl1.0-0 \
    libgstreamer1.0-0 \
    libgtk-3-0 \
    libhyphen0 \
    libmanette-0.2-0 \
    libsecret-1-0 \
    libwoff1 \
    libxcursor1 \
    libxdamage1 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    && apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install Playwright as root and pre-install the browsers
RUN pip install playwright \
    && PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers playwright install --with-deps

# Switch to appuser
RUN chown -R appuser:appuser /ms-playwright-browsers

# Switch to the non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Run the application
CMD gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --timeout 120
