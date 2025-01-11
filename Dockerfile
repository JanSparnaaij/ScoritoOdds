FROM heroku/heroku:22

# Copy .env file
COPY .env /app/.env

# Export the variables from .env as environment variables
RUN export $(grep -v '^#' /app/.env | xargs) && \
    echo "Environment variables loaded for build."

# Set the working directory and other configurations
WORKDIR /app
COPY . /app
ENV FLASK_ENV=production

# Debug: Check .env contents
RUN cat /app/.env

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
    libavif13 \
    libenchant-2-2 \
    libflite1 \
    libgles2-mesa \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-plugins-good1.0-0 \
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

# Set Python3 as the default python
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Set working directory and copy files
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install

# Expose port and run the app
EXPOSE 8000
CMD gunicorn "app:create_app()" --bind 0.0.0.0:8000
