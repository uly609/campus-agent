from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest

REQUESTS = Counter("campusflow_requests_total", "HTTP requests", ["route", "status"])
REQUEST_LATENCY = Histogram("campusflow_request_latency_seconds", "HTTP request latency", ["route"])
LLM_CALLS = Counter("campusflow_llm_calls_total", "Provider calls", ["role", "provider", "status"])
LLM_LATENCY = Histogram("campusflow_llm_latency_seconds", "Provider latency", ["role", "provider"])
LLM_FAILURES = Counter("campusflow_llm_failures_total", "Provider failures", ["role", "provider"])
TOOL_CALLS = Counter("campusflow_tool_calls_total", "Tool calls", ["tool", "status"])
TOOL_LATENCY = Histogram("campusflow_tool_latency_seconds", "Tool latency", ["tool"])
TOOL_FAILURES = Counter("campusflow_tool_failures_total", "Tool failures", ["tool"])
REPLANS = Counter("campusflow_replans_total", "Agent replans", ["reason"])
CACHE_HITS = Counter("campusflow_cache_hits_total", "Provider cache hits", ["role"])
CITATION_COVERAGE = Gauge("campusflow_citation_coverage", "Citation coverage")
RETRIEVAL_HIT_AT_K = Gauge("campusflow_retrieval_hit_at_k", "Retrieval hit at k")


def metrics_response() -> bytes:
    return generate_latest()

