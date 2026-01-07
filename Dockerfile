# --------------------------
# Stage 1: Builder
# --------------------------
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    uv sync --frozen

# --------------------------
# Stage 2: Runtime
# --------------------------
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

USER appuser

COPY --chown=appuser:appuser . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${AGENT_PORT:-8000}/health || exit 1

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