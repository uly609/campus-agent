from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent.graph import run_agent
from app.agent.planning import plan_intent
from app.llm.router import ProviderRouter
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
    intent, _, _ = plan_intent(text, "eval-user")
    return intent.value


async def run() -> dict[str, Any]:
    ensure_datasets()
    repo = JsonRepository()
    if not repo.load_posts() or not repo.load_documents():
        from scripts.seed import main as seed_main  # type: ignore[import-not-found]

        seed_main()
    intent_cases = read_jsonl(DATASET_DIR / "intent_80.jsonl")
    retrieval_cases = read_jsonl(DATASET_DIR / "retrieval_18.jsonl")
    qa_cases = read_jsonl(DATASET_DIR / "qa_14.jsonl")

    intent_results = []
    for case in intent_cases:
        predicted = predict_intent(case["input"])
        intent_results.append({"id": case["id"], "expected": case["expected_intent"], "predicted": predicted, "correct": predicted == case["expected_intent"]})
    intent_correct = sum(1 for result in intent_results if result["correct"])

    retrieval = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    retrieval_hits = 0
    reciprocal_ranks: list[float] = []
    retrieval_precisions: list[float] = []
    retrieval_precisions_at_5: list[float] = []
    retrieval_recalls: list[float] = []
    retrieval_results = []

    def source_matches(case: dict[str, Any], source_id: str) -> bool:
        exact = set(case.get("expected_source_ids", []))
        prefixes = [*case.get("expected_source_prefixes", []), *case.get("allowed_source_prefixes", [])]
        return source_id in exact or any(source_id.startswith(prefix) for prefix in prefixes)

    corpus_source_ids = {chunk.source_id for chunk in retrieval.chunks}
    for case in retrieval_cases:
        results = await retrieval.search(case["query"], top_k=8)
        ids = [item.source_id for item in results]
        relevant_ids = {source_id for source_id in corpus_source_ids if source_matches(case, source_id)}
        hit_positions = [index + 1 for index, source_id in enumerate(ids) if source_id in relevant_ids]
        if hit_positions:
            retrieval_hits += 1
            reciprocal_ranks.append(1 / min(hit_positions))
        else:
            reciprocal_ranks.append(0.0)
        retrieved_relevant = len(set(ids).intersection(relevant_ids))
        retrieval_precisions.append(retrieved_relevant / max(len(set(ids)), 1))
        top_five = set(ids[:5])
        retrieval_precisions_at_5.append(len(top_five.intersection(relevant_ids)) / max(len(top_five), 1))
        retrieval_recalls.append(retrieved_relevant / max(len(relevant_ids), 1))
        retrieval_results.append({"id": case["id"], "query": case["query"], "returned_source_ids": ids, "relevant_source_ids": sorted(relevant_ids), "hit": bool(hit_positions)})

    citation_covered = 0
    factual_cases = 0
    grounded_citations = 0
    total_citations = 0
    claims_satisfied = 0
    claims_expected = 0
    must_not_violations = 0
    refusals_ok = 0
    replan_success = 0
    judge_tp = 0
    judge_fp = 0
    judge_fn = 0
    tool_calls = 0
    tool_successes = 0
    latencies_ms: list[float] = []
    qa_results = []
    for case in qa_cases:
        started = time.perf_counter()
        state = await run_agent(case["question"], "eval-session", "eval-user")
        latencies_ms.append((time.perf_counter() - started) * 1000)
        answer = state.get("final_answer", "")
        citations = state.get("citations", [])
        if not case["should_refuse"]:
            factual_cases += 1
            if citations:
                citation_covered += 1
        for claim in case.get("must_claims", []):
            claims_expected += 1
            if claim in answer:
                claims_satisfied += 1
        for citation in citations:
            total_citations += 1
            if source_matches(case, str(citation.get("source_id", ""))):
                grounded_citations += 1
        if any(blocked in answer for blocked in case["must_not_show"]):
            must_not_violations += 1
        predicted_refusal = "证据不足" in answer or not citations
        if case["should_refuse"] == predicted_refusal:
            refusals_ok += 1
        if predicted_refusal and case["should_refuse"]:
            judge_tp += 1
        elif predicted_refusal:
            judge_fp += 1
        elif case["should_refuse"]:
            judge_fn += 1
        if (state.get("replan_count", 0) > 0) == case["should_replan"] or not case["should_replan"]:
            replan_success += 1
        for result in state.get("tool_results", []):
            tool_calls += 1
            tool_successes += int(bool(result.get("success")))
        qa_results.append({"id": case["id"], "refused": predicted_refusal, "expected_refusal": case["should_refuse"], "replan_count": state.get("replan_count", 0), "citation_source_ids": [citation.get("source_id") for citation in citations]})

    judge_precision = judge_tp / max(judge_tp + judge_fp, 1)
    judge_recall = judge_tp / max(judge_tp + judge_fn, 1)
    judge_f1 = 2 * judge_precision * judge_recall / max(judge_precision + judge_recall, 1e-9)
    ordered_latencies = sorted(latencies_ms)
    p95_index = min(len(ordered_latencies) - 1, max(0, int(len(ordered_latencies) * 0.95)))

    cache_router = ProviderRouter()
    cache_probe = f"eval-cache-probe-{uuid.uuid4().hex}"
    await cache_router.embed(cache_probe)
    cached_result = await cache_router.embed(cache_probe)
    cache_repeat_hit = float(cached_result.latency_ms == 0)

    metrics = {
        "intent_accuracy": intent_correct / len(intent_cases),
        "retrieval_hit_at_8": retrieval_hits / len(retrieval_cases),
        "retrieval_precision_at_5": statistics.fmean(retrieval_precisions_at_5),
        "retrieval_precision_at_8": statistics.fmean(retrieval_precisions),
        "retrieval_recall_at_8": statistics.fmean(retrieval_recalls),
        "retrieval_mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "claim_recall": claims_satisfied / max(claims_expected, 1),
        "citation_coverage": citation_covered / max(factual_cases, 1),
        "citation_groundedness": grounded_citations / max(total_citations, 1),
        "must_not_show_rate": must_not_violations / len(qa_cases),
        "refusal_accuracy": refusals_ok / len(qa_cases),
        "judge_f1": judge_f1,
        "replan_success_rate": replan_success / len(qa_cases),
        "tool_success_rate": tool_successes / max(tool_calls, 1),
        "cache_repeat_hit_rate": cache_repeat_hit,
        "p50_latency_ms": statistics.median(ordered_latencies),
        "p95_latency_ms": ordered_latencies[p95_index],
    }
    degraded_modes = ProviderRouter().degraded_modes
    return {
        "run_id": f"eval-{uuid.uuid4().hex[:10]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": "campusflow-agent-v1",
        "model_version": ",".join(degraded_modes) if degraded_modes else "configured-real-providers",
        "case_counts": {"intent": len(intent_cases), "retrieval": len(retrieval_cases), "qa": len(qa_cases)},
        "metrics": metrics,
        "case_results": {"intent": intent_results, "retrieval": retrieval_results, "qa": qa_results},
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
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run())
    if args.write_report:
        write_report(report)
    output = report if args.verbose else {key: report[key] for key in ["run_id", "model_version", "case_counts", "metrics"]}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
