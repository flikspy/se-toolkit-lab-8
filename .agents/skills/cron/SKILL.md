---
name: cron
description: Schedule and manage recurring jobs
disable-model-invocation: false
---

# Cron / Scheduling Skill

When the user asks to **create a scheduled task**, **set up a periodic check**, or **schedule a health check**, use the cron tools.

## Available Tools

- `schedule_job` — Schedule a recurring job with a specified interval
- `list_jobs` — List all scheduled jobs and their status
- `cancel_job` — Cancel a scheduled job by ID

## Creating a Health Check

When the user asks for a periodic health check, follow this pattern:

### Step 1: Schedule the job

```
Call tool: schedule_job with:
  - interval_minutes: <user's requested interval, default 15>
  - task: "Check backend errors in the last <interval> minutes, inspect traces if found, and post a health summary"
```

### Step 2: Confirm the schedule

Tell the user:
```
I've scheduled a health check to run every {interval} minute(s).
Job ID: {job_id}
Task: {task description}

The job will:
1. Check for backend errors in the last {interval} minutes
2. Fetch trace details if errors are found
3. Post a summary to this chat

You can ask me to "list scheduled jobs" anytime to see active jobs.
```

### Step 3: What the health check does

When the scheduled job runs (in a real implementation), it should:

1. **Check for errors:**
   ```
   Call tool: logs_error_count with service="backend", time_range="<interval>m"
   ```

2. **If errors found, get details:**
   ```
   Call tool: logs_search with query='_stream:{service="backend"} AND level:error', limit=10, start_time="now-<interval>m"
   ```

3. **If trace_id found in logs, fetch trace:**
   ```
   Call tool: traces_get with trace_id="<id>"
   ```

4. **Post summary to chat:**
   - If errors: "⚠️ Found {N} errors in the last {interval} minutes. {Details}"
   - If no errors: "✅ System looks healthy. No errors in the last {interval} minutes."

## Listing Jobs

When the user asks **"What jobs are scheduled?"** or **"List scheduled jobs"**:

```
Call tool: list_jobs
```

Then present the results in a readable format.

## Cancelling Jobs

When the user asks to **remove** or **cancel** a job:

```
Call tool: cancel_job with job_id="<the job id>"
```

Then confirm the cancellation to the user.

## Example Interaction

**User:** "Create a health check that runs every 15 minutes."

**Agent:** 
1. Calls `schedule_job(interval_minutes=15, task="Check backend errors...")`
2. Receives job_id: "job_1"
3. Responds: "I've scheduled a health check to run every 15 minutes. Job ID: job_1. Each run will check for backend errors and post a summary here."

**User:** "List scheduled jobs."

**Agent:**
1. Calls `list_jobs()`
2. Responds: "You have 1 scheduled job: job_1 - runs every 15 minutes to check backend errors."

**User:** "Remove the health check."

**Agent:**
1. Calls `cancel_job(job_id="job_1")`
2. Responds: "Cancelled job 'job_1'. The health check will no longer run."
