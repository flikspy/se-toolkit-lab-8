# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

**Question: "What is the agentic loop?"**

The agentic loop is the fundamental cycle that AI agents follow to accomplish tasks. It typically consists of these stages:

1. **Perceive** — Gather information from the environment (user input, tool outputs, observations)
2. **Think/Reason** — Process the information, plan next steps, make decisions
3. **Act** — Execute actions using available tools (file operations, API calls, commands, etc.)
4. **Observe** — Receive feedback from the action's results
5. **Repeat** — Continue the loop until the goal is achieved or a stopping condition is met

This loop enables agents to:
- Break complex tasks into steps
- Adapt based on feedback
- Use tools autonomously
- Self-correct when things don't work as expected

**Question: "What labs are available in our LMS?"**

Without MCP tools, the agent did not know about the LMS. It tried to guess by looking at the filesystem and listed directories like `/root/se-toolkit-lab-4`, `/root/se-toolkit-lab-5`, etc. This is expected behavior — the bare agent has no tools to query the actual LMS backend.

## Task 1B — Agent with LMS tools

**Question: "What labs are available?"**

After configuring MCP, the agent returned real data from the LMS backend:

| ID | Lab Title |
|----|-----------|
| 1 | Lab 01 – Products, Architecture & Roles |
| 2 | Lab 02 — Run, Fix, and Deploy a Backend Service |
| 3 | Lab 03 — Backend API: Explore, Debug, Implement, Deploy |
| 4 | Lab 04 — Testing, Front-end, and AI Agents |
| 5 | Lab 05 — Data Pipeline and Analytics Dashboard |
| 6 | Lab 06 — Build Your Own Agent |
| 7 | Lab 07 — Build a Client with an AI Coding Agent |
| 8 | lab-08 |

**Question: "Describe the architecture of the LMS system"**

The agent described the full architecture:

- **Client Layer**: React/Vite frontend + Swagger UI for API documentation
- **Reverse Proxy Layer**: Caddy server routing requests to backend and serving static files
- **Application Layer**: FastAPI (Python) backend with API key authentication, CORS middleware
- **Data Layer**: PostgreSQL 17 with SQLModel ORM, JSONB columns for flexible attributes
- **Admin UI**: pgAdmin for database management

Data model uses adjacency list pattern (parent_id) for tree hierarchy: Course → Labs → Tasks → Steps

All components run in Docker containers via docker-compose.yml.

## Task 1C — Skill prompt

**Question: "Show me the scores" (without specifying a lab)**

With the skill prompt configured, the agent showed comprehensive statistics:

**Completion Rates by Lab:**

| Lab | Title | Completion Rate | Passed / Total |
|-----|-------|-----------------|----------------|
| Lab 01 | Products, Architecture & Roles | 100.0% | 258 / 258 |
| Lab 02 | Run, Fix, and Deploy a Backend Service | 89.1% | 131 / 147 |
| Lab 03 | Backend API: Explore, Debug, Implement, Deploy | 89.7% | 156 / 174 |
| Lab 04 | Testing, Front-end, and AI Agents | 96.7% | 238 / 246 |
| Lab 05 | Data Pipeline and Analytics Dashboard | 98.4% | 246 / 250 |
| Lab 06 | Build Your Own Agent | 98.4% | 241 / 245 |
| Lab 07 | Build a Client with an AI Coding Agent | 99.6% | 236 / 237 |
| Lab 08 | lab-08 | 0.0% | 0 / 0 |

**Key Insights:**
- Highest completion rate: Lab 07 (99.6%)
- Lowest completion rate: Lab 02 & 03 (~89%)
- Highest avg task score: Lab 01 - "Lab setup" (84.3)
- Most challenging task: Lab 06 - "The System Agent" (42.8 avg, 2,053 attempts)

The agent offered to show top learners, group performance, or submission timeline for any specific lab.

## Task 2A — Deployed agent

**Nanobot gateway startup log:**

```
nanobot-1  | Using config: /app/nanobot/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
nanobot-1  | 2026-03-27 11:46:16.083 | INFO     | nanobot.channels.manager:_init_channels:54 - WebChat channel enabled
nanobot-1  | ✓ Channels enabled: webchat
nanobot-1  | ✓ Heartbeat: every 1800s
nanobot-1  | 2026-03-27 11:46:16.951 | INFO     | nanobot_webchat.channel:start:72 - WebChat starting on 0.0.0.0:8765
nanobot-1  | 2026-03-27 11:46:18.443 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:162 - MCP: registered tool 'mcp_lms_lms_labs' from server 'lms'
nanobot-1  | 2026-03-27 11:46:18.443 | INFO     | nanobot.agent.tools.mcp:connect_mcp_servers:182 - MCP server 'lms': connected, 9 tools registered
nanobot-1  | 2026-03-27 11:46:18.444 | INFO     | nanobot.agent.loop:run:260 - Agent loop started
```

**Services running:**
- `nanobot` gateway on port 18790 (internal)
- `webchat` channel on port 8765 (internal)
- Caddy proxy at `http://localhost:42002` routing `/ws/chat` to nanobot

## Task 2B — Web client

**Flutter web client accessible at:** `http://localhost:42002/flutter`

**Login:** Use `NANOBOT_ACCESS_KEY=eeeddd11`

**Test conversation:**
The Flutter web client connects to the agent via WebSocket at `/ws/chat`. Users can ask questions like:
- "What can you do in this system?"
- "What labs are available?"
- "Which lab has the lowest pass rate?"

The web client renders agent responses with support for structured output (tables, choices, confirmations).

## Task 3A — Structured logging

**Happy-path log excerpt** (request with status 200):

```
backend-1  | 2026-03-27 11:16:04,537 INFO [app.main] - request_started
backend-1  | 2026-03-27 11:16:04,538 INFO [app.auth] - auth_success
backend-1  | 2026-03-27 11:16:04,552 INFO [app.main] - request_completed
backend-1  | INFO: 172.18.0.9:38898 - "GET /analytics/completion-rate?lab=lab-03 HTTP/1.1" 200 OK
```

**Error-path log excerpt** (PostgreSQL stopped, connection closed):

```
backend-1  | sqlalchemy.exc.InterfaceError: (sqlalchemy.dialects.postgresql.asyncpg.InterfaceError)
backend-1  | <class 'asyncpg.exceptions._base.InterfaceError'>: connection is closed
backend-1  | [SQL: SELECT item.id, item.type, item.parent_id ... FROM item WHERE item.type = $1::VARCHAR]
backend-1  | [parameters: ('lab',)]
```

**VictoriaLogs UI:** Accessible at `http://localhost:42002/utils/victorialogs/select/vmui/`
Query example: `level:error AND _stream:{service="backend"}`

## Task 3B — Traces

**VictoriaTraces UI:** Accessible at `http://localhost:42002/utils/victoriatraces`

Healthy traces show span hierarchy: `request_started` → `auth_success` → `db_query` → `request_completed`
Error traces show the failing span with `connection is closed` error.

## Task 3C — Observability MCP tools

**New MCP tools added:**
- `obs_logs_search` — Search VictoriaLogs using LogsQL
- `obs_logs_error_count` — Count errors for a service
- `obs_traces_list` — List recent traces for a service
- `obs_traces_get` — Fetch full trace by ID

**Agent response to "Any errors in the last hour?"** (normal conditions):
"The system looks healthy. No errors found in the last hour for the backend service."

**Agent response after stopping PostgreSQL:**
"The backend is failing to connect to PostgreSQL. Error: 'connection is closed'. The db_query span failed when trying to execute a SELECT query on the item table."

## Task 4A — Multi-step investigation

**Agent response to "What went wrong?"** (with PostgreSQL stopped):

The agent followed the investigation flow:
1. Searched recent error logs with `obs_logs_search`
2. Found trace ID in the error logs
3. Fetched the full trace with `obs_traces_get`
4. Reported: "The backend failed with error 'connection is closed'. The database connection pool is unavailable because PostgreSQL is stopped. Trace shows the failure occurred in the db_query span during a SELECT on the item table."

## Task 4B — Proactive health check

**Scheduled job created:** Health check running every 2 minutes via nanobot cron.

**Proactive report in chat:**
"Health check report: Backend errors detected in the last 2 minutes. Error: 'connection is closed' - PostgreSQL appears to be unavailable. 3 failed requests detected."

## Task 4C — Bug fix and recovery

**1. Root cause — Planted bug location:**

File: `backend/app/routers/items.py`, function `get_items()`

The bug was catching all exceptions and returning HTTP 404 instead of 500:

```python
# BEFORE (buggy):
except Exception as exc:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Items not found",
    ) from exc
```

**2. Fix applied:**

```python
# AFTER (fixed):
except Exception as exc:
    # Re-raise as 500 Internal Server Error for database failures
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database error occurred",
    ) from exc
```

**3. Post-fix verification:**

With PostgreSQL stopped:
```bash
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:42002/items/ -H "Authorization: Bearer apikey"
500
```

Before the fix, this returned `404`. After the fix, it correctly returns `500`.

**4. Healthy follow-up:**

After restarting PostgreSQL:
```bash
$ curl -sf http://localhost:42002/items/ -H "Authorization: Bearer apikey" | head -c 100
[{"title":"Lab 01 – Products, Architecture & Roles","id":1,...}]
```

The scheduled health check now reports: "System healthy - 0 errors in the last 2 minutes."
