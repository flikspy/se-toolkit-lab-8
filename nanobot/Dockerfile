# syntax=docker/dockerfile:1

# Multi-stage build for nanobot gateway service
ARG REGISTRY_PREFIX_DOCKER_HUB=

# ------------------------------------------------------------------------------
# Builder stage
# ------------------------------------------------------------------------------
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY nanobot/ ./nanobot/

# Sync dependencies (including workspace packages like mcp/)
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

# Copy nanobot project files
COPY --chown=nonroot:nonroot nanobot/ /app/nanobot/

# Create workspace directory
RUN mkdir -p /home/nonroot/.nanobot && chown nonroot:nonroot /home/nonroot/.nanobot

WORKDIR /app

# Set environment for nanobot
ENV PATH="/app/.venv/bin:$PATH"

# Run entrypoint
USER nonroot
ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
