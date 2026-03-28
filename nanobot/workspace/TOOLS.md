# Tool Usage Notes

Tool signatures are provided automatically via function calling.
This file documents non-obvious constraints and usage patterns.

## exec — Safety Limits

- Commands have a configurable timeout (default 60s)
- Dangerous commands are blocked (rm -rf, format, dd, shutdown, etc.)
- Output is truncated at 10,000 characters
- `restrictToWorkspace` config can limit file access to the workspace

## cron — Scheduled Reminders

- Please refer to cron skill for usage.

## Observability Tools

You have MCP tools for querying VictoriaLogs and VictoriaTraces:

- `logs_search` — Search logs using LogsQL query
- `logs_error_count` — Count errors for a service over time window
- `traces_list` — List recent traces for a service
- `traces_get` — Fetch full trace details by ID

See `skills/observability/SKILL.md` for when and how to use these tools.