from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, evals, health, ingest, memory, posts, search
from app.core.logging import configure_logging
from app.observability.metrics import REQUEST_LATENCY, REQUESTS, metrics_response

configure_logging()

app = FastAPI(title="CampusFlow AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    route = request.url.path
    REQUESTS.labels(route=route, status=str(response.status_code)).inc()
    REQUEST_LATENCY.labels(route=route).observe(time.perf_counter() - start)
    return response


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(posts.router)
app.include_router(ingest.router)
app.include_router(memory.router)
app.include_router(evals.router)
app.include_router(search.router)


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=metrics_response(), media_type="text/plain; version=0.0.4")

