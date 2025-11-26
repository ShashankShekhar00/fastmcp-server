# Multi-stage build for optimized production image
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt


# Production stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    mkdir -p /app/data && \
    chown -R mcpuser:mcpuser /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY --chown=mcpuser:mcpuser . .

# Create directory for database and logs
RUN mkdir -p /app/data /app/logs && \
    chown -R mcpuser:mcpuser /app/data /app/logs

# Switch to non-root user
USER mcpuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/healthcheck.py || exit 1

# Run the application
CMD ["python", "-m", "src.server_oauth"]
