# --------------------------
# Base image
# --------------------------
FROM python:3.11-slim

# --------------------------
# Install system dependencies
# --------------------------
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# --------------------------
# Create non-root user
# --------------------------
RUN useradd -m -u 1000 appuser
USER appuser
WORKDIR /app

# --------------------------
# Create virtual environment
# --------------------------
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# --------------------------
# Copy dependency files first (for caching)
# --------------------------
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# --------------------------
# Upgrade pip and install dependencies
# --------------------------
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir uv
RUN uv sync --frozen

# --------------------------
# Copy application code
# --------------------------
COPY --chown=appuser:appuser . .

# --------------------------
# Expose ports
# --------------------------
EXPOSE 8000 8080

# --------------------------
# Entrypoint for multi-mode support
# --------------------------
ENTRYPOINT ["/bin/bash", "-c", "\
set -e; \
MODE=${AGENT_MODE:-api}; \
HOST=${AGENT_HOST:-0.0.0.0}; \
PORT=${AGENT_PORT:-8000}; \
export PORT=$PORT; \
echo \"Starting ADK Agent in $MODE mode on $HOST:$PORT\"; \
case \"$MODE\" in \
  web) export SERVE_WEB_INTERFACE=true && exec python3 main.py ;; \
  api|api_server) unset SERVE_WEB_INTERFACE && exec python3 main.py ;; \
  *) echo \"Error: Unknown mode $MODE. Use web or api_server\"; exit 1 ;; \
esac"]