---
name: observability
description: Diagnose system failures using logs and traces
disable-model-invocation: false
---

# Observability Skill

When the user asks **"What went wrong?"**, **"Check system health"**, **"Any errors?"**, or similar diagnostic questions, follow this investigation flow:

## Investigation Flow

### Step 1: Search for recent errors

First, check for error logs in the backend service:

```
Call tool: logs_error_count with service="backend", time_range="1h"
```

If errors are found, proceed to Step 2. If no errors, report the system looks healthy.

### Step 2: Fetch error log details

Get the actual error log entries to understand what failed:

```
Call tool: logs_search with query='_stream:{service="backend"} AND (level:error OR level:ERROR)', limit=10, start_time="now-1h"
```

Look for:
- `event` field indicating what operation failed (e.g., `db_query`, `request_completed`)
- `error` field with the error message
- `trace_id` if present in the log entry

### Step 3: Fetch the trace if available

If you found a `trace_id` in the logs, fetch the full trace to see the complete request flow:

```
Call tool: traces_get with trace_id="<the trace id from logs>"
```

Examine the trace spans to identify:
- Which service failed
- Where in the request flow the error occurred
- How long each step took

### Step 4: Summarize findings

Provide a concise summary that combines log and trace evidence:

**Good response format:**
```
I found {N} errors in the backend in the last hour.

Most recent error:
- Time: {timestamp}
- Event: {event}
- Error: {error message}
- Trace ID: {trace_id}

The trace shows the failure occurred in {service} during {operation}. 
{Specific diagnosis based on trace spans}

Root cause: {your diagnosis}
```

**Avoid:**
- Dumping raw JSON without explanation
- Skipping the trace analysis when a trace_id is available
- Vague statements like "something went wrong"

## Tools Available

- `logs_search` — Search VictoriaLogs using LogsQL
- `logs_error_count` — Count errors for a service in a time range
- `traces_list` — List recent traces for a service
- `traces_get` — Fetch a specific trace by ID

## Example Queries

**Check for errors in the last hour:**
```
logs_error_count(service="backend", time_range="1h")
```

**Search for database errors:**
```
logs_search(query='_stream:{service="backend"} AND (db OR database) AND level:error', limit=20)
```

**List recent traces:**
```
traces_list(service="backend", limit=10)
```

**Get a specific trace:**
```
traces_get(trace_id="abc123...")
```
