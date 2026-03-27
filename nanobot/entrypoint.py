#!/usr/bin/env python3
"""
Entrypoint for nanobot gateway in Docker.

Resolves environment variables into config.json at runtime,
then execs 'nanobot gateway' with the resolved config.
"""

import json
import os
import sys
from pathlib import Path


def resolve_config():
    """Load config.json, inject env vars, write resolved config."""
    config_path = Path(__file__).parent / "config.json"
    resolved_path = Path(__file__).parent / "config.resolved.json"
    workspace_path = Path(__file__).parent / "workspace"

    with open(config_path) as f:
        config = json.load(f)

    # Resolve LLM provider config from env vars
    llm_api_key = os.environ.get("LLM_API_KEY", "")
    llm_base_url = os.environ.get("LLM_API_BASE_URL", "")
    llm_model = os.environ.get("LLM_API_MODEL", "coder-model")

    # Update all providers with the same values (nanobot checks multiple)
    for provider in config.get("providers", {}):
        config["providers"][provider]["apiKey"] = llm_api_key
        config["providers"][provider]["apiBase"] = llm_base_url

    # Set default model
    config["agents"]["defaults"]["model"] = llm_model

    # Resolve gateway host/port from env vars
    gateway_address = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS", "0.0.0.0")
    gateway_port = int(os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT", "18790"))
    config["gateway"]["host"] = gateway_address
    config["gateway"]["port"] = gateway_port

    # Resolve webchat channel config
    webchat_enabled = os.environ.get("NANOBOT_WEBCHAT_ENABLED", "true").lower() == "true"
    webchat_port = int(os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT", "8765"))
    access_key = os.environ.get("NANOBOT_ACCESS_KEY", "")

    if "webchat" not in config["channels"]:
        config["channels"]["webchat"] = {}

    config["channels"]["webchat"]["enabled"] = webchat_enabled
    config["channels"]["webchat"]["port"] = webchat_port
    config["channels"]["webchat"]["allow_from"] = ["*"]
    config["channels"]["webchat"]["access_key"] = access_key

    # Resolve MCP server env vars (LMS backend)
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL", "")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY", "")

    if "mcpServers" not in config["tools"]:
        config["tools"]["mcpServers"] = {}

    if "lms" in config["tools"]["mcpServers"]:
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key

    # Resolve MCP server env vars (Observability)
    victorialogs_url = os.environ.get("VICTORIALOGS_URL", "http://victorialogs:9428")
    victoriatraces_url = os.environ.get("VICTORIATRACES_URL", "http://victoriatraces:10428")

    if "observability" in config["tools"]["mcpServers"]:
        config["tools"]["mcpServers"]["observability"]["env"]["VICTORIALOGS_URL"] = victorialogs_url
        config["tools"]["mcpServers"]["observability"]["env"]["VICTORIATRACES_URL"] = victoriatraces_url

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    return str(resolved_path), str(workspace_path)


def main():
    resolved_config, workspace = resolve_config()

    # Exec nanobot gateway with resolved config
    os.execvp("nanobot", ["nanobot", "gateway", "--config", resolved_config, "--workspace", workspace])


if __name__ == "__main__":
    main()
