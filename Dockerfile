# Multi-stage build for Smart CLI
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install build

# Copy source code
COPY . .

# Build the package
RUN python -m build

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/smartcli/.local/bin:$PATH" \
    SMART_CLI_HOME="/home/smartcli/.smart-cli"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash smartcli && \
    mkdir -p /home/smartcli/.smart-cli && \
    chown -R smartcli:smartcli /home/smartcli

# Switch to non-root user
USER smartcli
WORKDIR /home/smartcli

# Copy built package from builder stage
COPY --from=builder /app/dist/*.whl /tmp/

# Install Smart CLI
RUN pip install --user /tmp/*.whl && \
    rm /tmp/*.whl

# Create directories for Smart CLI
RUN mkdir -p ~/.smart-cli/{cache,logs,config,sessions} && \
    mkdir -p ~/.config/smart-cli

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD smart --version || exit 1

# Set default command
CMD ["smart", "--help"]

# Labels
LABEL maintainer="Rauf Alizada <raufalizada@example.com>"
LABEL description="Smart CLI - AI-powered development automation tool"
LABEL version="1.0.0"
LABEL org.opencontainers.image.title="Smart CLI"
LABEL org.opencontainers.image.description="Enterprise-grade AI-powered CLI platform"
LABEL org.opencontainers.image.vendor="Rauf Alizada"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/raufA1/smart-cli"
LABEL org.opencontainers.image.documentation="https://github.com/raufA1/smart-cli/wiki"