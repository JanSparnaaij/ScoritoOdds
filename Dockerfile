FROM heroku/heroku:22

# Copy .env file
COPY .env /app/.env

# Debug: Check .env contents
RUN cat /app/.env

# Set environment variables
ENV FLASK_ENV=production
ENV SECRET_KEY=${SECRET_KEY}

# Install Python and other dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libgstcodecparsers-1.0-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-good1.0-0 \
    libflite1 \
    libwoff1 \
    libenchant-2-2 \
    libsecret-1-0 \
    libavif13 \
    libhyphen0 \
    libmanette-0.2-0 \
    libgles2-mesa \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcursor1 \
    libgtk-3-0 \
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
