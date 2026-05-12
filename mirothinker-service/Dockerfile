# Multi-stage Dockerfile for optimized builds

# === Stage 1: Builder ===
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# === Stage 2: Production ===
FROM python:3.10-slim AS production

# Create non-root user
RUN groupadd -r mirothinker && useradd -r -g mirothinker -d /app -s /sbin/nologin mirothinker

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY pyproject.toml /app/
COPY .env.example /app/

# Create data directories
RUN mkdir -p /app/data/{traces,logs,cache} && \
    chown -R mirothinker:mirothinker /app

# Switch to non-root user
USER mirothinker

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with uvicorn (optimized for 2GB memory)
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
