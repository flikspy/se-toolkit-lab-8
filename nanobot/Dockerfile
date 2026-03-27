# syntax=docker/dockerfile:1

# Multi-stage build for nanobot gateway service
ARG REGISTRY_PREFIX_DOCKER_HUB=

# ------------------------------------------------------------------------------
# Builder stage
# ------------------------------------------------------------------------------
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Copy workspace root (includes mcp/, nanobot-websocket-channel/, pyproject.toml, uv.lock)
COPY --from=workspace pyproject.toml uv.lock /app/
COPY --from=workspace mcp/ /app/mcp/
COPY --from=workspace nanobot-websocket-channel/ /app/nanobot-websocket-channel/

# Copy nanobot project files (build context is ./nanobot)
COPY pyproject.toml uv.lock /app/nanobot/
COPY . /app/nanobot/

# Sync dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot

# ------------------------------------------------------------------------------
# Runtime stage
# ------------------------------------------------------------------------------
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm AS runtime

# Create non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy virtual environment from builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Create workspace directory
RUN mkdir -p /home/nonroot/.nanobot && chown nonroot:nonroot /home/nonroot/.nanobot

WORKDIR /app

# Set environment for nanobot
ENV PATH="/app/.venv/bin:$PATH"

# Run entrypoint
USER nonroot
ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
