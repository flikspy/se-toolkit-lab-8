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

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
