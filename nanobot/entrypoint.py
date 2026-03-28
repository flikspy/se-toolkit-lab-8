#!/usr/bin/env python3
"""Entrypoint for nanobot Docker deployment.

Resolves environment variables into config.json at runtime, then launches `nanobot gateway`.

Environment variables:
- NANOBOT_LLM_API_KEY: API key for the LLM provider
- NANOBOT_LLM_API_BASE: Base URL for the LLM provider
- NANOBOT_LLM_MODEL: Model name to use
- NANOBOT_GATEWAY_HOST: Host to bind the gateway (default: 0.0.0.0)
- NANOBOT_GATEWAY_PORT: Port for the gateway (default: 18790)
- NANOBOT_WEBCHAT_HOST: Host for webchat (default: 0.0.0.0)
- NANOBOT_WEBCHAT_PORT: Port for webchat (default: 18791)
- NANOBOT_LMS_BACKEND_URL: URL for LMS backend
- NANOBOT_LMS_API_KEY: API key for LMS backend
- VICTORIALOGS_URL: URL for VictoriaLogs
- VICTORIATRACES_URL: URL for VictoriaTraces
"""

import json
import os
import sys


def main():
    config_path = os.environ.get("NANOBOT_CONFIG_PATH", "/app/nanobot/config.json")
    workspace_path = os.environ.get("NANOBOT_WORKSPACE_PATH", "/app/nanobot/workspace")

    # Load existing config
    with open(config_path, "r") as f:
        config = json.load(f)

    # Resolve LLM provider settings
    llm_api_key = os.environ.get("NANOBOT_LLM_API_KEY")
    llm_api_base = os.environ.get("NANOBOT_LLM_API_BASE")
    llm_model = os.environ.get("NANOBOT_LLM_MODEL")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base:
        config["providers"]["custom"]["apiBase"] = llm_api_base
    if llm_model:
        config["agents"]["defaults"]["model"] = llm_model

    # Resolve gateway settings
    gateway_host = os.environ.get("NANOBOT_GATEWAY_HOST", "0.0.0.0")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_PORT", "18790")
    if "gateway" not in config:
        config["gateway"] = {}
    config["gateway"]["host"] = gateway_host
    config["gateway"]["port"] = int(gateway_port)

    # Resolve webchat settings
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_HOST", "0.0.0.0")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_PORT", "18791")
    if "webchat" not in config["channels"]:
        config["channels"]["webchat"] = {}
    config["channels"]["webchat"]["enabled"] = True
    config["channels"]["webchat"]["allow_from"] = ["*"]
    config["channels"]["webchat"]["host"] = webchat_host
    config["channels"]["webchat"]["port"] = int(webchat_port)

    # Resolve MCP server settings
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")
    victorialogs_url = os.environ.get("VICTORIALOGS_URL")
    victoriatraces_url = os.environ.get("VICTORIATRACES_URL")

    if lms_backend_url and "mcpServers" in config["tools"]:
        if "lms" in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = (
                lms_backend_url
            )
            if lms_api_key:
                config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = (
                    lms_api_key
                )
        if victorialogs_url:
            config["tools"]["mcpServers"]["lms"]["env"]["VICTORIALOGS_URL"] = (
                victorialogs_url
            )
        if victoriatraces_url:
            config["tools"]["mcpServers"]["lms"]["env"]["VICTORIATRACES_URL"] = (
                victoriatraces_url
            )

    # Write resolved config
    resolved_path = "/tmp/nanobot-resolved-config.json"
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Resolved config written to {resolved_path}", file=sys.stderr)

    # Launch nanobot gateway
    os.execvp(
        "nanobot",
        [
            "nanobot",
            "gateway",
            "--config",
            resolved_path,
            "--workspace",
            workspace_path,
        ],
    )


if __name__ == "__main__":
    main()
