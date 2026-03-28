"""Stdio MCP server exposing LMS backend operations as typed tools."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

from mcp_lms.client import LMSClient, VictoriaLogsClient, VictoriaTracesClient

_base_url: str = ""
_victorialogs_url: str = ""
_victoriatraces_url: str = ""

# Cron job storage (in-memory for this lab)
_scheduled_jobs: dict[str, dict] = {}
_job_counter: int = 0

server = Server("lms")

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _NoArgs(BaseModel):
    """Empty input model for tools that only need server-side configuration."""


class _LabQuery(BaseModel):
    lab: str = Field(description="Lab identifier, e.g. 'lab-04'.")


class _TopLearnersQuery(_LabQuery):
    limit: int = Field(
        default=5, ge=1, description="Max learners to return (default 5)."
    )


class _LogsSearchQuery(BaseModel):
    query: str = Field(
        description="LogsQL query string. Example: '_stream:{service=\"backend\"} AND level:error'"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Max logs to return.")
    start_time: str | None = Field(
        default=None,
        description="Start time (e.g., 'now-1h', '2024-01-01T00:00:00Z'). Defaults to 1 hour ago.",
    )


class _ErrorCountQuery(BaseModel):
    service: str = Field(
        default="backend", description="Service name to check for errors."
    )
    time_range: str = Field(
        default="1h", description="Time range (e.g., '1h', '24h', '7d')."
    )


class _TracesListQuery(BaseModel):
    service: str = Field(default="backend", description="Service name.")
    limit: int = Field(default=20, ge=1, le=100, description="Max traces to return.")


class _TraceByIdQuery(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch.")


class _ScheduleJobQuery(BaseModel):
    interval_minutes: int = Field(
        ge=1, description="Interval in minutes between job runs."
    )
    task: str = Field(description="Task description. Example: 'Check backend errors and post summary'")


class _ListJobsQuery(BaseModel):
    pass


class _CancelJobQuery(BaseModel):
    job_id: str = Field(description="Job ID to cancel.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_api_key() -> str:
    for name in ("NANOBOT_LMS_API_KEY", "LMS_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    raise RuntimeError(
        "LMS API key not configured. Set NANOBOT_LMS_API_KEY or LMS_API_KEY."
    )


def _client() -> LMSClient:
    if not _base_url:
        raise RuntimeError(
            "LMS backend URL not configured. Pass it as: python -m mcp_lms <base_url>"
        )
    return LMSClient(_base_url, _resolve_api_key())


def _victorialogs_client() -> VictoriaLogsClient:
    if not _victorialogs_url:
        raise RuntimeError(
            "VictoriaLogs URL not configured. Set VICTORIALOGS_URL env var."
        )
    return VictoriaLogsClient(_victorialogs_url)


def _victoriatraces_client() -> VictoriaTracesClient:
    if not _victoriatraces_url:
        raise RuntimeError(
            "VictoriaTraces URL not configured. Set VICTORIATRACES_URL env var."
        )
    return VictoriaTracesClient(_victoriatraces_url)


def _text(data: BaseModel | Sequence[BaseModel]) -> list[TextContent]:
    """Serialize a pydantic model (or list of models) to a JSON text block."""
    if isinstance(data, BaseModel):
        payload = data.model_dump()
    else:
        payload = [item.model_dump() for item in data]
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def _health(_args: _NoArgs) -> list[TextContent]:
    return _text(await _client().health_check())


async def _labs(_args: _NoArgs) -> list[TextContent]:
    items = await _client().get_items()
    return _text([i for i in items if i.type == "lab"])


async def _learners(_args: _NoArgs) -> list[TextContent]:
    return _text(await _client().get_learners())


async def _pass_rates(args: _LabQuery) -> list[TextContent]:
    return _text(await _client().get_pass_rates(args.lab))


async def _timeline(args: _LabQuery) -> list[TextContent]:
    return _text(await _client().get_timeline(args.lab))


async def _groups(args: _LabQuery) -> list[TextContent]:
    return _text(await _client().get_groups(args.lab))


async def _top_learners(args: _TopLearnersQuery) -> list[TextContent]:
    return _text(await _client().get_top_learners(args.lab, limit=args.limit))


async def _completion_rate(args: _LabQuery) -> list[TextContent]:
    return _text(await _client().get_completion_rate(args.lab))


async def _sync_pipeline(_args: _NoArgs) -> list[TextContent]:
    return _text(await _client().sync_pipeline())


# ---------------------------------------------------------------------------
# Observability tool handlers
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchQuery) -> list[TextContent]:
    """Search logs using VictoriaLogs."""
    result = await _victorialogs_client().search(
        query=args.query, limit=args.limit, start_time=args.start_time
    )
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def _logs_error_count(args: _ErrorCountQuery) -> list[TextContent]:
    """Count errors for a service in a time range."""
    count = await _victorialogs_client().error_count(
        service=args.service, time_range=args.time_range
    )
    return [
        TextContent(
            type="text",
            text=f"Found {count} error(s) for service '{args.service}' in the last {args.time_range}",
        )
    ]


async def _traces_list(args: _TracesListQuery) -> list[TextContent]:
    """List recent traces for a service."""
    traces = await _victoriatraces_client().list_traces(
        service=args.service, limit=args.limit
    )
    return [TextContent(type="text", text=json.dumps(traces, ensure_ascii=False))]


async def _traces_get(args: _TraceByIdQuery) -> list[TextContent]:
    """Get a specific trace by ID."""
    trace = await _victoriatraces_client().get_trace(trace_id=args.trace_id)
    if trace is None:
        return [TextContent(type="text", text=f"Trace not found: {args.trace_id}")]
    return [TextContent(type="text", text=json.dumps(trace.model_dump(), ensure_ascii=False))]


# ---------------------------------------------------------------------------
# Cron tool handlers
# ---------------------------------------------------------------------------


async def _schedule_job(args: _ScheduleJobQuery) -> list[TextContent]:
    """Schedule a recurring job."""
    global _job_counter
    _job_counter += 1
    job_id = f"job_{_job_counter}"
    
    job = {
        "id": job_id,
        "interval_minutes": args.interval_minutes,
        "task": args.task,
        "created_at": datetime.now().isoformat(),
        "status": "active",
    }
    _scheduled_jobs[job_id] = job
    
    return [
        TextContent(
            type="text",
            text=f"Scheduled job '{job_id}' to run every {args.interval_minutes} minute(s).\nTask: {args.task}\n\nNote: This is a lab simulation. In production, this would integrate with a real scheduler.",
        )
    ]


async def _list_jobs(_args: _ListJobsQuery) -> list[TextContent]:
    """List all scheduled jobs."""
    if not _scheduled_jobs:
        return [TextContent(type="text", text="No scheduled jobs.")]
    
    jobs_text = "Scheduled jobs:\n\n"
    for job_id, job in _scheduled_jobs.items():
        jobs_text += f"- {job_id}: every {job['interval_minutes']} minute(s)\n"
        jobs_text += f"  Task: {job['task']}\n"
        jobs_text += f"  Status: {job['status']}\n"
        jobs_text += f"  Created: {job['created_at']}\n\n"
    
    return [TextContent(type="text", text=jobs_text)]


async def _cancel_job(args: _CancelJobQuery) -> list[TextContent]:
    """Cancel a scheduled job."""
    if args.job_id not in _scheduled_jobs:
        return [TextContent(type="text", text=f"Job not found: {args.job_id}")]
    
    job = _scheduled_jobs[args.job_id]
    job["status"] = "cancelled"
    
    return [TextContent(type="text", text=f"Cancelled job '{args.job_id}': {job['task']}")]


# ---------------------------------------------------------------------------
# Registry: tool name -> (input model, handler, Tool definition)
# ---------------------------------------------------------------------------

_Registry = tuple[type[BaseModel], Callable[..., Awaitable[list[TextContent]]], Tool]

_TOOLS: dict[str, _Registry] = {}


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    schema = model.model_json_schema()
    # Pydantic puts definitions under $defs; flatten for MCP's JSON Schema expectation.
    schema.pop("$defs", None)
    schema.pop("title", None)
    _TOOLS[name] = (
        model,
        handler,
        Tool(name=name, description=description, inputSchema=schema),
    )


_register(
    "lms_health",
    "Check if the LMS backend is healthy and report the item count.",
    _NoArgs,
    _health,
)
_register("lms_labs", "List all labs available in the LMS.", _NoArgs, _labs)
_register(
    "lms_learners", "List all learners registered in the LMS.", _NoArgs, _learners
)
_register(
    "lms_pass_rates",
    "Get pass rates (avg score and attempt count per task) for a lab.",
    _LabQuery,
    _pass_rates,
)
_register(
    "lms_timeline",
    "Get submission timeline (date + submission count) for a lab.",
    _LabQuery,
    _timeline,
)
_register(
    "lms_groups",
    "Get group performance (avg score + student count per group) for a lab.",
    _LabQuery,
    _groups,
)
_register(
    "lms_top_learners",
    "Get top learners by average score for a lab.",
    _TopLearnersQuery,
    _top_learners,
)
_register(
    "lms_completion_rate",
    "Get completion rate (passed / total) for a lab.",
    _LabQuery,
    _completion_rate,
)
_register(
    "lms_sync_pipeline",
    "Trigger the LMS sync pipeline. May take a moment.",
    _NoArgs,
    _sync_pipeline,
)

# Observability tools
_register(
    "logs_search",
    "Search VictoriaLogs using LogsQL. Use for finding errors, debugging issues. Example query: '_stream:{service=\"backend\"} AND level:error'",
    _LogsSearchQuery,
    _logs_search,
)
_register(
    "logs_error_count",
    "Count error logs for a service in a time range. Use to check if there are recent errors.",
    _ErrorCountQuery,
    _logs_error_count,
)
_register(
    "traces_list",
    "List recent traces for a service from VictoriaTraces. Shows request flows and latencies.",
    _TracesListQuery,
    _traces_list,
)
_register(
    "traces_get",
    "Fetch a specific trace by ID. Use to inspect detailed request flow after finding a trace ID in logs.",
    _TraceByIdQuery,
    _traces_get,
)

# Cron tools
_register(
    "schedule_job",
    "Schedule a recurring job to run at a specified interval. Use for periodic health checks or monitoring tasks.",
    _ScheduleJobQuery,
    _schedule_job,
)
_register(
    "list_jobs",
    "List all scheduled jobs and their status.",
    _ListJobsQuery,
    _list_jobs,
)
_register(
    "cancel_job",
    "Cancel a scheduled job by its ID.",
    _CancelJobQuery,
    _cancel_job,
)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [entry[2] for entry in _TOOLS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    entry = _TOOLS.get(name)
    if entry is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    model_cls, handler, _ = entry
    try:
        args = model_cls.model_validate(arguments or {})
        return await handler(args)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main(base_url: str | None = None) -> None:
    global _base_url, _victorialogs_url, _victoriatraces_url
    _base_url = base_url or os.environ.get("NANOBOT_LMS_BACKEND_URL", "")
    _victorialogs_url = os.environ.get("VICTORIALOGS_URL", "http://victorialogs:9428")
    _victoriatraces_url = os.environ.get(
        "VICTORIATRACES_URL", "http://victoriatraces:10428"
    )
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
