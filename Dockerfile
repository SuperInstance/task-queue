# Multi-stage Dockerfile for task-queue

# Stage 1: Build stage (if needed)
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY python/ /app/
COPY setup.py .
COPY pyproject.toml .

# Install task-queue package
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 worker && \
    chown -R worker:worker /app

USER worker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from taskqueue import health; health.check()" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "taskqueue"]
CMD ["worker", "--broker=redis://localhost:6379/0", "--queues=default"]
