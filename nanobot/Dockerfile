# ---
# Stage 1: Build the application
# ---
ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace root first
COPY --from=workspace pyproject.toml uv.lock /app/
COPY --from=workspace nanobot/ /app/nanobot/
COPY --from=workspace mcp/ /app/mcp/
COPY --from=workspace nanobot-websocket-channel/ /app/nanobot-websocket-channel/

# Sync all dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# ---
# Stage 2: Final image
# ---
ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Setup non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy application
COPY --from=builder --chown=nonroot:nonroot /app /app

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/nanobot"

USER nonroot

WORKDIR /app

# Run the entrypoint
CMD ["python", "/app/nanobot/entrypoint.py"]
