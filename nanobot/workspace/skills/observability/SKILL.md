# Observability Skill

You have access to observability tools that let you see logs and traces from the LMS system.

## Available Tools

### Logs (VictoriaLogs)
- **`logs_search`** — Search logs using LogsQL query
  - `query`: LogsQL query string (e.g., `"service:backend"`, `"level:error"`, `"_stream:{service=\"backend\"} AND level:error"`)
  - `limit`: Max entries to return (default 10, max 100)

- **`logs_error_count`** — Count errors for a service
  - `service`: Service name (e.g., `"backend"`)
  - `minutes`: Time window in minutes (default 60)

### Traces (VictoriaTraces)
- **`traces_list`** — List recent traces for a service
  - `service`: Service name (e.g., `"Learning Management Service"`)
  - `limit`: Max traces to return (default 5, max 20)

- **`traces_get`** — Fetch full trace details by ID
  - `trace_id`: The trace ID to fetch

## When to Use

### User asks "What went wrong?" or "Check system health"
**Follow this investigation flow:**

1. **Check for recent errors** — Call `logs_error_count(service="backend", minutes=5)` to see if there are errors in the last 5 minutes

2. **If errors exist (count > 0)**:
   - Call `logs_search(query="level:error AND service:backend", limit=10)` to get error details
   - Look for trace IDs in error messages (field: `trace_id`)
   - If you find a trace ID, call `traces_get(trace_id="...")` to see the full failure context
   - Analyze the span hierarchy to identify where the failure occurred

3. **If no errors found**:
   - Call `logs_search(query="service:backend", limit=5)` to see recent activity
   - Check if the system is operating normally

4. **Summarize findings** — Report:
   - What failed (specific error message)
   - Where it failed (which service, which operation)
   - Why it failed (root cause from logs/traces)
   - Impact (how many errors, over what time period)

### User asks "Any errors in the last hour?"
1. Call `logs_error_count(service="backend", minutes=60)`
2. If count > 0, call `logs_search(query="level:error", limit=5)` for details
3. Summarize findings concisely

### User asks to investigate a specific failure
1. Search logs for the time window: `logs_search(query="service:backend AND level:error", limit=20)`
2. Look for trace IDs in error messages
3. Fetch the trace: `traces_get(trace_id="...")`
4. Analyze the span hierarchy to find where the failure occurred
5. Report the root cause

## Response Style

- **Be concise** — summarize findings, don't dump raw JSON
- **Mention specific error messages** — quote the actual exception text
- **Identify the root cause** — e.g., "PostgreSQL connection refused", "database is locked"
- **Include evidence** — reference log entries and trace spans that support your conclusion
- **Use markdown formatting** — bold key findings, use code blocks for error messages

## Examples

**Query:** "What went wrong?"
**Response:** 
"I investigated the recent failure. Here's what I found:

**Logs:** Found 3 errors in the backend service in the last 5 minutes. Error message: `(sqlalchemy.dialects.postgresql.asyncpg.InterfaceError) connection is closed`

**Traces:** Trace `abc123...` shows the failure occurred at the `db_query` span. The request started successfully, authentication passed, but the database query failed because PostgreSQL was unavailable.

**Root cause:** PostgreSQL database is stopped or unreachable. The backend cannot establish a database connection."

**Query:** "Any errors in the last hour?"
**Response:** "No errors detected in the last hour. The backend service has been running cleanly with **0 errors** in the past 60 minutes."

**Query:** "Check system health"
**Response:** 
"System health check:

✅ **Backend:** Running, no errors in last 5 minutes
✅ **Database:** PostgreSQL reachable
✅ **Recent activity:** All requests completing successfully

System looks healthy."