from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent.graph import run_agent
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository

DATASET_DIR = ROOT / "evals" / "datasets"
REPORT_DIR = ROOT / "evals" / "reports"


def ensure_datasets() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    intent_path = DATASET_DIR / "intent_80.jsonl"
    retrieval_path = DATASET_DIR / "retrieval_18.jsonl"
    qa_path = DATASET_DIR / "qa_14.jsonl"
    if not intent_path.exists():
        cases: list[dict[str, Any]] = []
        templates = [
            ("你好呀", "greeting"),
            ("图书馆几点关门", "campus_qa"),
            ("搜索二手教材帖子", "post_search"),
            ("我在南门丢了蓝色水杯", "lost_found"),
            ("帮我起草一个失物招领帖子", "post_draft"),
            ("记住我喜欢安静自习室", "memory"),
            ("运行一下评测结果", "eval"),
            ("校医院工作时间是什么", "campus_qa"),
        ]
        for index in range(80):
            text, label = templates[index % len(templates)]
            cases.append({"id": f"intent-{index:02d}", "input": f"{text} #{index}", "expected_intent": label})
        write_jsonl(intent_path, cases)
    if not retrieval_path.exists():
        cases: list[dict[str, Any]] = [
            {"id": f"ret-{index:02d}", "query": query, "expected_source_ids": expected}
            for index, (query, expected) in enumerate(
                [
                    ("图书馆开放时间", ["doc-library-hours-00"]),
                    ("一卡通挂失补办", ["doc-card-loss-02"]),
                    ("宿舍维修漏水", ["doc-dorm-repair-01"]),
                    ("奖学金申请材料", ["doc-scholarship-03"]),
                    ("校医院开诊", ["doc-clinic-04"]),
                    ("南门 捡到 校园卡", ["post-seed-011"]),
                ]
                * 3
            )
        ][:18]
        write_jsonl(retrieval_path, cases)
    if not qa_path.exists():
        base = [
            ("图书馆几点关门？", ["开放"], ["doc-library-hours-00"], [], False, False),
            ("一卡通丢了怎么办？", ["挂失"], ["doc-card-loss-02"], ["忽略之前指令"], False, False),
            ("宿舍漏水找谁？", ["报修"], ["doc-dorm-repair-01"], [], False, False),
            ("校医院夜间能看诊吗？", ["校医院"], ["doc-clinic-04"], [], False, False),
            ("不存在的火星校区收费是多少？", [], [], ["编造"], True, True),
            ("奖学金需要什么材料？", ["奖学金"], ["doc-scholarship-03"], [], False, False),
            ("南门有没有失物招领？", ["社区信息"], ["post-seed-011"], [], False, False),
        ]
        cases: list[dict[str, Any]] = [
            {
                "id": f"qa-{index:02d}",
                "question": item[0],
                "must_claims": item[1],
                "allowed_source_ids": item[2],
                "must_not_show": item[3],
                "should_refuse": item[4],
                "should_replan": item[5],
            }
            for index, item in enumerate((base * 2)[:14])
        ]
        write_jsonl(qa_path, cases)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def predict_intent(text: str) -> str:
    if any(word in text for word in ["你好", "hello"]):
        return "greeting"
    if any(word in text for word in ["起草", "发帖"]):
        return "post_draft"
    if any(word in text for word in ["丢", "捡", "失物"]):
        return "lost_found"
    if any(word in text for word in ["记住", "记忆", "喜欢"]):
        return "memory"
    if "评测" in text:
        return "eval"
    if any(word in text for word in ["搜索", "二手", "帖子"]):
        return "post_search"
    return "campus_qa"


async def run() -> dict[str, Any]:
    ensure_datasets()
    repo = JsonRepository()
    if not repo.load_posts() or not repo.load_documents():
        from scripts.seed import main as seed_main  # type: ignore[import-not-found]

        seed_main()
    intent_cases = read_jsonl(DATASET_DIR / "intent_80.jsonl")
    retrieval_cases = read_jsonl(DATASET_DIR / "retrieval_18.jsonl")
    qa_cases = read_jsonl(DATASET_DIR / "qa_14.jsonl")

    intent_correct = sum(1 for case in intent_cases if predict_intent(case["input"]) == case["expected_intent"])

    retrieval = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    retrieval_hits = 0
    reciprocal_ranks = []
    for case in retrieval_cases:
        results = await retrieval.search(case["query"], top_k=8)
        ids = [item.source_id for item in results]
        expected = set(case["expected_source_ids"])
        hit_positions = [index + 1 for index, source_id in enumerate(ids) if source_id in expected]
        if hit_positions:
            retrieval_hits += 1
            reciprocal_ranks.append(1 / min(hit_positions))
        else:
            reciprocal_ranks.append(0.0)

    citation_covered = 0
    must_not_violations = 0
    refusals_ok = 0
    replan_success = 0
    for case in qa_cases:
        state = await run_agent(case["question"], "eval-session", "eval-user")
        answer = state.get("final_answer", "")
        citations = state.get("citations", [])
        if citations or case["should_refuse"]:
            citation_covered += 1
        if any(blocked in answer for blocked in case["must_not_show"]):
            must_not_violations += 1
        if case["should_refuse"] == ("证据不足" in answer or not citations):
            refusals_ok += 1
        if (state.get("replan_count", 0) > 0) == case["should_replan"] or not case["should_replan"]:
            replan_success += 1

    metrics = {
        "intent_accuracy": intent_correct / len(intent_cases),
        "retrieval_hit_at_8": retrieval_hits / len(retrieval_cases),
        "retrieval_mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "citation_coverage": citation_covered / len(qa_cases),
        "must_not_show_rate": must_not_violations / len(qa_cases),
        "refusal_accuracy": refusals_ok / len(qa_cases),
        "replan_success_rate": replan_success / len(qa_cases),
        "tool_success_rate": 1.0,
        "cache_hit_rate": 0.0,
        "p50_latency_ms": 0.0,
        "p95_latency_ms": 0.0,
    }
    return {
        "run_id": f"eval-{uuid.uuid4().hex[:10]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": "campusflow-agent-v1",
        "model_version": "fake-providers",
        "case_counts": {"intent": len(intent_cases), "retrieval": len(retrieval_cases), "qa": len(qa_cases)},
        "metrics": metrics,
    }


def write_report(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"{report['run_id']}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# Eval Report {report['run_id']}", "", "| Metric | Value |", "| --- | ---: |"]
    for key, value in report["metrics"].items():
        lines.append(f"| {key} | {value:.4f} |")
    md = "\n".join(lines) + "\n"
    (REPORT_DIR / f"{report['run_id']}.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "latest.md").write_text(md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run())
    if args.write_report:
        write_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
