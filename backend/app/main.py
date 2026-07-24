from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, evals, health, ingest, memory, posts, providers, search, sessions
from app.core.logging import configure_logging
from app.observability.metrics import REQUEST_LATENCY, REQUESTS, metrics_response
from app.security.rate_limit import RateLimiter

configure_logging()

app = FastAPI(title="CampusFlow AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
rate_limiter = RateLimiter()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    rate_headers: tuple[int, int, int] | None = None
    if request.url.path.startswith("/api/") and request.url.path not in {"/api/v1/health"}:
        allowed, limit, remaining, reset = rate_limiter.check(request)
        rate_headers = (limit, remaining, reset)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": {"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后重试"}},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                },
            )
    response = await call_next(request)
    route = request.url.path
    REQUESTS.labels(route=route, status=str(response.status_code)).inc()
    REQUEST_LATENCY.labels(route=route).observe(time.perf_counter() - start)
    if rate_headers:
        limit, remaining, reset = rate_headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
    return response


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(posts.router)
app.include_router(ingest.router)
app.include_router(memory.router)
app.include_router(evals.router)
app.include_router(search.router)
app.include_router(providers.router)
app.include_router(sessions.router)


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=metrics_response(), media_type="text/plain; version=0.0.4")
