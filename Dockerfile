# Dockerfile para API de predição de risco de defasagem
# Passos Mágicos - Datathon FIAP 2025
# Phase 8: Production Hardened

FROM python:3.11-slim AS builder

# Build stage - install dependencies
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt


FROM python:3.11-slim

# Metadata
LABEL maintainer="Datathon FIAP Team"
LABEL version="2.0.0"
LABEL description="API para predição de risco de defasagem escolar (Hardened)"
LABEL org.opencontainers.image.source="https://github.com/datathon-fiap/defasagem-api"

# Security: Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    LOG_LEVEL=INFO \
    # Security defaults
    API_KEYS="" \
    RATE_LIMIT_RPM=60 \
    MAX_BODY_BYTES=262144 \
    REQUEST_TIMEOUT_MS=3000 \
    METRICS_ENABLED=true \
    AUDIT_ENABLED=true

# Create non-root user for security (fixed UID/GID)
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --no-create-home appuser

# Set work directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy application code (ownership to appuser)
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup artifacts/ ./artifacts/

# Create logs directory with proper permissions
RUN mkdir -p logs monitoring/inference_store && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

