FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy the entire workspace for context
COPY . /workspace/
WORKDIR /workspace/nanobot

# Sync dependencies (including MCP and webchat from workspace)
RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1

# Gateway port
EXPOSE 18790
# Webchat port
EXPOSE 8765

CMD ["uv", "run", "nanobot", "gateway", "-c", "./config.json"]
