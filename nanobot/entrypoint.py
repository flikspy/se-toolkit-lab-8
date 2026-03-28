#!/usr/bin/env python3
"""Entrypoint for nanobot Docker deployment."""

import json
import os
import sys

def main():
    config_path = os.environ.get("NANOBOT_CONFIG_PATH", "/app/nanobot/config.json")
    workspace_path = os.environ.get("NANOBOT_WORKSPACE_PATH", "/app/nanobot/workspace")

    with open(config_path, "r") as f:
        config = json.load(f)

    # Resolve settings from env vars
    if os.environ.get("NANOBOT_LLM_API_KEY"):
        config["providers"]["custom"]["apiKey"] = os.environ["NANOBOT_LLM_API_KEY"]
    if os.environ.get("NANOBOT_LLM_API_BASE"):
        config["providers"]["custom"]["apiBase"] = os.environ["NANOBOT_LLM_API_BASE"]
    if os.environ.get("NANOBOT_LLM_MODEL"):
        config["agents"]["defaults"]["model"] = os.environ["NANOBOT_LLM_MODEL"]

    gateway_host = os.environ.get("NANOBOT_GATEWAY_HOST", "0.0.0.0")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_PORT", "18790")
    if "gateway" not in config:
        config["gateway"] = {}
    config["gateway"]["host"] = gateway_host
    config["gateway"]["port"] = int(gateway_port)

    webchat_host = os.environ.get("NANOBOT_WEBCHAT_HOST", "0.0.0.0")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_PORT", "18791")
    if "webchat" not in config["channels"]:
        config["channels"]["webchat"] = {}
    config["channels"]["webchat"]["enabled"] = True
    config["channels"]["webchat"]["allow_from"] = ["*"]
    config["channels"]["webchat"]["host"] = webchat_host
    config["channels"]["webchat"]["port"] = int(webchat_port)

    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")
    if lms_backend_url and "mcpServers" in config["tools"] and "lms" in config["tools"]["mcpServers"]:
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
        if lms_api_key:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key

    victorialogs_url = os.environ.get("VICTORIALOGS_URL")
    victoriatraces_url = os.environ.get("VICTORIATRACES_URL")
    if victorialogs_url:
        config["tools"]["mcpServers"]["lms"]["env"]["VICTORIALOGS_URL"] = victorialogs_url
    if victoriatraces_url:
        config["tools"]["mcpServers"]["lms"]["env"]["VICTORIATRACES_URL"] = victoriatraces_url

    resolved_path = "/tmp/nanobot-resolved-config.json"
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Resolved config written to {resolved_path}", file=sys.stderr)

    # Launch nanobot gateway
    os.execvp(
        "/app/.venv/bin/python",
        ["-m", "nanobot.gateway", "--config", resolved_path, "--workspace", workspace_path],
    )

if __name__ == "__main__":
    main()
