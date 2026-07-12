FROM python:3.11-slim

WORKDIR /app

# System deps for Selenium, PDF, etc.
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
