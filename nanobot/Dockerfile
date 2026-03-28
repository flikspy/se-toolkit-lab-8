FROM python:3.14-slim

WORKDIR /app

# Copy the project
COPY . .

# Install all packages system-wide
RUN pip install --upgrade pip && \
    pip install "nanobot-ai @ https://github.com/HKUDS/nanobot/archive/e7d371ec1e6531b28898ec2c869ef338e8dd46ec.zip" && \
    pip install -e ./mcp && \
    pip install -e ./nanobot-websocket-channel/nanobot-webchat

ENV PYTHONPATH="/app"

CMD ["python", "/app/nanobot/entrypoint.py"]
