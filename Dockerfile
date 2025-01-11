FROM python:3.10-slim

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers

# Create a non-root user for better security
RUN adduser --disabled-password --gecos '' appuser

# Copy .env file
COPY .env /app/.env

# Set the working directory and other configurations
WORKDIR /app
COPY . /app
ENV FLASK_ENV=production

# Install Python and other dependencies
RUN apt-get update && apt-get install -y \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libavif12 \
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
    python3 \
    python3-pip \
    && apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Change to the non-root user
USER appuser

# Expose port and run the app
EXPOSE 8000
CMD gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --timeout 120
