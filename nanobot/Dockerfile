FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY config.json ./config.json
COPY workspace/ ./workspace/

# Install dependencies
RUN uv sync --frozen --no-dev

# Add MCP package
COPY ../mcp /mcp
RUN uv add /mcp

ENV PYTHONUNBUFFERED=1

# Gateway port
EXPOSE 18790
# Webchat port
EXPOSE 8765

CMD ["uv", "run", "nanobot", "gateway", "-c", "./config.json"]
