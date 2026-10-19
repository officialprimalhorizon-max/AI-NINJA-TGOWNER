# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DATA_DIR=/data \
    PORT=8080

# Agent ke liye multi-language toolchain + terminal tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        nodejs npm \
        default-jdk-headless \
        gcc g++ build-essential \
        lua5.4 php-cli ruby \
        git curl ca-certificates unzip \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /data && useradd -m -u 10001 agent && chown -R agent:agent /app /data
USER agent

EXPOSE 8080

# Single worker + threads (SSE streaming ke liye). Railway $PORT inject karta hai.
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 24 \
    --worker-class gthread --timeout 600 --graceful-timeout 30 \
    --access-logfile - --error-logfile - server:app
