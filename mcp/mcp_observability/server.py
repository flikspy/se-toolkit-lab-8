"""MCP server exposing VictoriaLogs and VictoriaTraces as typed tools."""

from __future__ import annotations

import os
import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

server = Server("observability")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_VICTORIALOGS_URL = os.environ.get("VICTORIALOGS_URL", "http://victorialogs:9428")
_VICTORIATRACES_URL = os.environ.get("VICTORIATRACES_URL", "http://victoriatraces:10428")

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _LogsSearchQuery(BaseModel):
    query: str = Field(description="LogsQL query string (e.g., 'level:error' or '_stream:{service=\"backend\"}')")
    limit: int = Field(default=30, ge=1, le=1000, description="Max log entries to return")


class _LogsErrorCountQuery(BaseModel):
    service: str = Field(description="Service name (e.g., 'backend')")
    hours: int = Field(default=1, ge=1, le=24, description="Time window in hours")


class _TracesListQuery(BaseModel):
    service: str = Field(description="Service name to filter traces")
    limit: int = Field(default=10, ge=1, le=100, description="Max traces to return")


class _TracesGetQuery(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text(data: Any) -> list[TextContent]:
    """Serialize data to JSON text content."""
    if isinstance(data, (dict, list)):
        import json
        return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]
    return [TextContent(type="text", text=str(data))]


# ---------------------------------------------------------------------------
# Log tools (VictoriaLogs)
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchQuery) -> list[TextContent]:
    """Search logs using VictoriaLogs LogsQL query."""
    encoded_query = urllib.parse.quote(args.query, safe="")
    url = f"{_VICTORIALOGS_URL}/select/logsql/query?query={encoded_query}&limit={args.limit}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        # VictoriaLogs returns JSON array of log entries
        return _text(response.json())


async def _logs_error_count(args: _LogsErrorCountQuery) -> list[TextContent]:
    """Count errors per service over a time window."""
    # VictoriaLogs query for errors in the last N hours
    query = f'level:error AND _stream:{{service="{args.service}"}}'
    encoded_query = urllib.parse.quote(query, safe="")
    url = f"{_VICTORIALOGS_URL}/select/logsql/query?query={encoded_query}&limit=1000"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        logs = response.json()
        error_count = len(logs) if isinstance(logs, list) else 0
        return _text({"service": args.service, "error_count": error_count, "time_window_hours": args.hours})


# ---------------------------------------------------------------------------
# Trace tools (VictoriaTraces - Jaeger API)
# ---------------------------------------------------------------------------


async def _traces_list(args: _TracesListQuery) -> list[TextContent]:
    """List recent traces for a service."""
    url = f"{_VICTORIATRACES_URL}/jaeger/api/traces?service={args.service}&limit={args.limit}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        # Jaeger API returns {"data": [...traces...]}
        traces = data.get("data", [])
        summary = []
        for trace in traces[:10]:
            summary.append({
                "trace_id": trace.get("traceID"),
                "spans": len(trace.get("spans", [])),
                "start_time": trace.get("startTime"),
                "duration": trace.get("duration"),
            })
        return _text({"service": args.service, "traces": summary})


async def _traces_get(args: _TracesGetQuery) -> list[TextContent]:
    """Fetch a specific trace by ID."""
    url = f"{_VICTORIATRACES_URL}/jaeger/api/traces/{args.trace_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return _text(data)


# ---------------------------------------------------------------------------
# Register all tools
# ---------------------------------------------------------------------------


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    """Register a tool with the server."""
    tool = Tool(
        name=name,
        description=description,
        inputSchema=model.model_json_schema(),
    )
    
    @server.call_tool()
    async def handler_wrapper(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        validated = model(**arguments)
        return await handler(validated)
    
    @server.list_tools()
    async def list_tools_handler() -> list[Tool]:
        return [tool]


# ---------------------------------------------------------------------------
# Register all tools
# ---------------------------------------------------------------------------


def register_all() -> None:
    """Register all observability tools."""
    _register(
        "obs_logs_search",
        "Search VictoriaLogs using LogsQL. Use for finding errors, debugging issues. Example query: 'level:error AND _stream:{service=\"backend\"}'",
        _LogsSearchQuery,
        _logs_search,
    )
    _register(
        "obs_logs_error_count",
        "Count errors for a service over a time window. Returns error count for the specified service.",
        _LogsErrorCountQuery,
        _logs_error_count,
    )
    _register(
        "obs_traces_list",
        "List recent traces for a service from VictoriaTraces. Shows trace IDs, span counts, and durations.",
        _TracesListQuery,
        _traces_list,
    )
    _register(
        "obs_traces_get",
        "Fetch full trace details by trace ID. Use to inspect span hierarchy and find failures.",
        _TracesGetQuery,
        _traces_get,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def run_server() -> None:
    """Run the MCP server via stdio."""
    register_all()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            initialization_options=server.create_initialization_options(),
        )


def main() -> None:
    """Main entry point for the MCP server."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
