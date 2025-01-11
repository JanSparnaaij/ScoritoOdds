# Use the Heroku-22 stack as the base image
FROM heroku/heroku:22

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    libgstreamer1.0-0 \
    libwoff1 \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-gl1.0-0 \
    libenchant-2-2 \
    libsecret-1-0

# Install Python and pip
RUN apt-get install -y python3 python3-pip

# Copy your application code to the container
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Install Playwright and browsers
RUN pip3 install playwright
RUN playwright install

# Command to run your app
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8000"]
