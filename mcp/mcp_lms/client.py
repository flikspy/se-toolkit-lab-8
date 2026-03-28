"""Async HTTP client, models, and formatters for the LMS backend API."""

import httpx
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class HealthResult(BaseModel):
    status: str
    item_count: int | str = "unknown"
    error: str = ""


class LogEntry(BaseModel):
    timestamp: str = ""
    level: str = ""
    service: str = ""
    event: str = ""
    message: str = ""
    trace_id: str = ""


class TraceSpan(BaseModel):
    trace_id: str = ""
    span_id: str = ""
    operation_name: str = ""
    service_name: str = ""
    start_time: int = 0
    duration: int = 0
    tags: list[dict] = []
    logs: list[dict] = []


class Trace(BaseModel):
    trace_id: str = ""
    spans: list[TraceSpan] = []


class Item(BaseModel):
    id: int | None = None
    type: str = "step"
    parent_id: int | None = None
    title: str = ""
    description: str = ""


class Learner(BaseModel):
    id: int | None = None
    external_id: str = ""
    student_group: str = ""


class PassRate(BaseModel):
    task: str
    avg_score: float
    attempts: int


class TimelineEntry(BaseModel):
    date: str
    submissions: int


class GroupPerformance(BaseModel):
    group: str
    avg_score: float
    students: int


class TopLearner(BaseModel):
    learner_id: int
    avg_score: float
    attempts: int


class CompletionRate(BaseModel):
    lab: str
    completion_rate: float
    passed: int
    total: int


class SyncResult(BaseModel):
    new_records: int
    total_records: int


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


class LMSClient:
    """Client for the LMS backend API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(headers=self._headers, timeout=10.0)

    async def health_check(self) -> HealthResult:
        async with self._client() as c:
            try:
                r = await c.get(f"{self.base_url}/items/")
                r.raise_for_status()
                items = [Item.model_validate(i) for i in r.json()]
                return HealthResult(status="healthy", item_count=len(items))
            except httpx.ConnectError:
                return HealthResult(
                    status="unhealthy", error=f"connection refused ({self.base_url})"
                )
            except httpx.HTTPStatusError as e:
                return HealthResult(
                    status="unhealthy", error=f"HTTP {e.response.status_code}"
                )
            except Exception as e:
                return HealthResult(status="unhealthy", error=str(e))

    async def get_items(self) -> list[Item]:
        async with self._client() as c:
            r = await c.get(f"{self.base_url}/items/")
            r.raise_for_status()
            return [Item.model_validate(i) for i in r.json()]

    async def get_learners(self) -> list[Learner]:
        async with self._client() as c:
            r = await c.get(f"{self.base_url}/learners/")
            r.raise_for_status()
            return [Learner.model_validate(i) for i in r.json()]

    async def get_pass_rates(self, lab: str) -> list[PassRate]:
        async with self._client() as c:
            r = await c.get(
                f"{self.base_url}/analytics/pass-rates", params={"lab": lab}
            )
            r.raise_for_status()
            return [PassRate.model_validate(i) for i in r.json()]

    async def get_timeline(self, lab: str) -> list[TimelineEntry]:
        async with self._client() as c:
            r = await c.get(f"{self.base_url}/analytics/timeline", params={"lab": lab})
            r.raise_for_status()
            return [TimelineEntry.model_validate(i) for i in r.json()]

    async def get_groups(self, lab: str) -> list[GroupPerformance]:
        async with self._client() as c:
            r = await c.get(f"{self.base_url}/analytics/groups", params={"lab": lab})
            r.raise_for_status()
            return [GroupPerformance.model_validate(i) for i in r.json()]

    async def get_top_learners(self, lab: str, limit: int = 5) -> list[TopLearner]:
        async with self._client() as c:
            r = await c.get(
                f"{self.base_url}/analytics/top-learners",
                params={"lab": lab, "limit": limit},
            )
            r.raise_for_status()
            return [TopLearner.model_validate(i) for i in r.json()]

    async def get_completion_rate(self, lab: str) -> CompletionRate:
        async with self._client() as c:
            r = await c.get(
                f"{self.base_url}/analytics/completion-rate", params={"lab": lab}
            )
            r.raise_for_status()
            return CompletionRate.model_validate(r.json())

    async def sync_pipeline(self) -> SyncResult:
        async with self._client() as c:
            r = await c.post(f"{self.base_url}/pipeline/sync")
            r.raise_for_status()
            return SyncResult.model_validate(r.json())


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def format_health(result: HealthResult) -> str:
    if result.status == "healthy":
        return f"\u2705 Backend is healthy. {result.item_count} items available."
    return f"\u274c Backend error: {result.error or 'Unknown'}"


def format_labs(items: list[Item]) -> str:
    labs = sorted(
        [i for i in items if i.type == "lab"],
        key=lambda x: str(x.id),
    )
    if not labs:
        return "\U0001f4ed No labs available."
    text = "\U0001f4da Available labs:\n\n"
    text += "\n".join(f"\u2022 {lab.title}" for lab in labs)
    return text


def format_scores(lab: str, rates: list[PassRate]) -> str:
    if not rates:
        return f"\U0001f4ed No scores found for {lab}."
    text = f"\U0001f4ca Pass rates for {lab}:\n\n"
    text += "\n".join(
        f"\u2022 {r.task}: {r.avg_score:.1f}% ({r.attempts} attempts)" for r in rates
    )
    return text


# ---------------------------------------------------------------------------
# VictoriaLogs client
# ---------------------------------------------------------------------------


class VictoriaLogsClient:
    """Client for VictoriaLogs HTTP API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=10.0)

    async def search(
        self, query: str, limit: int = 50, start_time: str | None = None
    ) -> list[dict]:
        """Search logs using LogsQL query."""
        async with self._client() as c:
            params = {"query": query, "limit": limit}
            if start_time:
                params["start"] = start_time
            r = await c.get(f"{self.base_url}/select/logsql/query", params=params)
            r.raise_for_status()
            return r.json()

    async def error_count(
        self, service: str = "backend", time_range: str = "1h"
    ) -> int:
        """Count errors for a service in a time range."""
        query = f'_stream:{{service="{service}"}} AND (level:error OR level:ERROR)'
        async with self._client() as c:
            params = {"query": query, "start": f"now-{time_range}"}
            r = await c.get(f"{self.base_url}/select/logsql/query", params=params)
            r.raise_for_status()
            result = r.json()
            if isinstance(result, list):
                return len(result)
            return 0


# ---------------------------------------------------------------------------
# VictoriaTraces client (Jaeger-compatible API)
# ---------------------------------------------------------------------------


class VictoriaTracesClient:
    """Client for VictoriaTraces HTTP API (Jaeger-compatible)."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=10.0)

    async def list_traces(
        self, service: str = "backend", limit: int = 20
    ) -> list[dict]:
        """List recent traces for a service."""
        async with self._client() as c:
            params = {"service": service, "limit": limit}
            r = await c.get(f"{self.base_url}/jaeger/api/traces", params=params)
            r.raise_for_status()
            data = r.json()
            return data.get("data", [])

    async def get_trace(self, trace_id: str) -> Trace | None:
        """Get a specific trace by ID."""
        async with self._client() as c:
            r = await c.get(f"{self.base_url}/jaeger/api/traces/{trace_id}")
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = r.json()
            trace_data = data.get("data", [])
            if not trace_data:
                return None
            spans_data = trace_data[0].get("spans", [])
            spans = [
                TraceSpan(
                    trace_id=s.get("traceID", ""),
                    span_id=s.get("spanID", ""),
                    operation_name=s.get("operationName", ""),
                    service_name=s.get("process", {}).get("serviceName", ""),
                    start_time=s.get("startTime", 0),
                    duration=s.get("duration", 0),
                    tags=s.get("tags", []),
                    logs=s.get("logs", []),
                )
                for s in spans_data
            ]
            return Trace(trace_id=trace_id, spans=spans)
