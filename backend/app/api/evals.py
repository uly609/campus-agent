from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.eval_service import run_eval_and_load
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()


@router.post("/evals/run")
def run_evals() -> dict[str, object]:
    report = run_eval_and_load()
    repo.save_eval(report)
    return report


@router.get("/evals/{run_id}")
def get_eval(run_id: str) -> dict[str, object]:
    for run in reversed(repo.eval_runs()):
        if run.get("run_id") == run_id or run_id == "latest":
            return run
    raise HTTPException(status_code=404, detail={"code": "EVAL_RUN_NOT_FOUND"})


@router.get("/traces")
def list_traces() -> dict[str, object]:
    return {"traces": repo.traces()[-50:]}
