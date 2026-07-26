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
sys.path.insert(0, str(ROOT / "evals"))

from app.agent.graph import run_agent
from app.agent.planning import plan_intent
from app.llm.router import ProviderRouter
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository
from eval_metrics import (
    binary_classification,
    citation_support_rate,
    fact_group_recall,
    forbidden_term_rate,
    multiclass_classification,
    retrieval_metrics,
    safe_div,
)

DATASET_DIR = ROOT / "evals" / "datasets"
REPORT_DIR = ROOT / "evals" / "reports"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def predict_intent(text: str) -> str:
    intent, _, _ = plan_intent(text, "eval-user")
    return intent.value


def average_metrics(rows: list[dict[str, float]]) -> dict[str, float]:
    return {
        key: statistics.fmean(row[key] for row in rows)
        for key in rows[0]
    }


async def evaluate_intent(cases: list[dict[str, Any]]) -> tuple[dict[str, float], dict[str, Any], list[dict[str, Any]]]:
    results = []
    for case in cases:
        predicted = predict_intent(case["input"])
        results.append(
            {
                "id": case["id"],
                "difficulty": case.get("difficulty", "standard"),
                "input": case["input"],
                "expected": case["expected_intent"],
                "predicted": predicted,
                "correct": predicted == case["expected_intent"],
            }
        )
    detail = multiclass_classification(
        [item["expected"] for item in results],
        [item["predicted"] for item in results],
    )
    metrics = {
        "intent_accuracy": float(detail["accuracy"]),
        "intent_macro_precision": float(detail["macro_precision"]),
        "intent_macro_recall": float(detail["macro_recall"]),
        "intent_macro_f1": float(detail["macro_f1"]),
    }
    return metrics, detail, results


async def evaluate_retrieval(
    cases: list[dict[str, Any]], retrieval: RetrievalService
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    metric_rows = []
    results = []
    for case in cases:
        returned = await retrieval.search(case["query"], top_k=8)
        ids = [item.source_id for item in returned]
        qrels = {str(key): int(value) for key, value in case["qrels"].items()}
        scores = retrieval_metrics(ids, qrels, k=8)
        metric_rows.append(scores)
        hard_negatives = set(case.get("hard_negative_source_ids", []))
        results.append(
            {
                "id": case["id"],
                "difficulty": case.get("difficulty", "standard"),
                "query": case["query"],
                "returned_source_ids": ids,
                "qrels": qrels,
                "hard_negative_hits": [source_id for source_id in ids[:5] if source_id in hard_negatives],
                **scores,
            }
        )
    averaged = average_metrics(metric_rows)
    metrics = {f"retrieval_{key}": value for key, value in averaged.items()}
    metrics["retrieval_hard_negative_rate_at_5"] = safe_div(
        sum(bool(item["hard_negative_hits"]) for item in results), len(results)
    )
    return metrics, results


def is_refusal(answer: str, citations: list[dict[str, Any]]) -> bool:
    refusal_markers = ("证据不足", "不能可靠回答", "不能执行", "无法回答")
    return any(marker in answer for marker in refusal_markers) or not citations


async def evaluate_qa(cases: list[dict[str, Any]]) -> tuple[dict[str, float], list[dict[str, Any]], dict[str, Any]]:
    results = []
    latencies_ms: list[float] = []
    tool_calls = 0
    tool_successes = 0
    for case in cases:
        started = time.perf_counter()
        state = await run_agent(case["question"], f"eval-{case['id']}", "eval-user")
        latencies_ms.append((time.perf_counter() - started) * 1000)
        answer = str(state.get("final_answer", ""))
        citations = list(state.get("citations", []))
        evidence = list(state.get("retrieved_evidence", []))
        expected_sources = set(case.get("allowed_source_ids", []))
        cited_sources = [str(item.get("source_id", "")) for item in citations]
        citation_precision = safe_div(
            sum(source_id in expected_sources for source_id in cited_sources), len(cited_sources)
        )
        context_relevance = safe_div(
            sum(str(item.get("source_id", "")) in expected_sources for item in evidence), len(evidence)
        )
        expected_refusal = bool(case["should_refuse"])
        predicted_refusal = is_refusal(answer, citations)
        expected_replan = bool(case["should_replan"])
        predicted_replan = int(state.get("replan_count", 0)) > 0
        fact_recall = 1.0 if expected_refusal and predicted_refusal else fact_group_recall(
            answer, case.get("required_fact_groups", [])
        )
        for result in state.get("tool_results", []):
            tool_calls += 1
            tool_successes += int(bool(result.get("success")))
        results.append(
            {
                "id": case["id"],
                "difficulty": case.get("difficulty", "standard"),
                "question": case["question"],
                "answer": answer,
                "answer_fact_recall": fact_recall,
                "context_relevance": context_relevance,
                "citation_precision": citation_precision,
                "citation_faithfulness": citation_support_rate(answer, citations, evidence),
                "forbidden_term_rate": forbidden_term_rate(answer, case.get("forbidden_terms", [])),
                "expected_refusal": expected_refusal,
                "predicted_refusal": predicted_refusal,
                "expected_replan": expected_replan,
                "predicted_replan": predicted_replan,
                "replan_count": state.get("replan_count", 0),
                "citation_source_ids": cited_sources,
            }
        )

    refusal = binary_classification(
        [item["expected_refusal"] for item in results],
        [item["predicted_refusal"] for item in results],
    )
    replan = binary_classification(
        [item["expected_replan"] for item in results],
        [item["predicted_replan"] for item in results],
    )
    ordered = sorted(latencies_ms)
    p95_index = min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))
    answerable = [item for item in results if not item["expected_refusal"]]
    metrics = {
        "qa_answer_fact_recall": statistics.fmean(item["answer_fact_recall"] for item in results),
        "qa_context_relevance": statistics.fmean(item["context_relevance"] for item in answerable),
        "qa_citation_precision": statistics.fmean(item["citation_precision"] for item in answerable),
        "qa_citation_faithfulness": statistics.fmean(item["citation_faithfulness"] for item in answerable),
        "qa_forbidden_content_rate": statistics.fmean(item["forbidden_term_rate"] for item in results),
        "refusal_precision": refusal["precision"],
        "refusal_recall": refusal["recall"],
        "refusal_f1": refusal["f1"],
        "replan_precision": replan["precision"],
        "replan_recall": replan["recall"],
        "replan_f1": replan["f1"],
        "tool_success_rate": safe_div(tool_successes, tool_calls),
        "p50_latency_ms": statistics.median(ordered),
        "p95_latency_ms": ordered[p95_index],
    }
    return metrics, results, {"refusal": refusal, "replan": replan}


async def run() -> dict[str, Any]:
    intent_cases = read_jsonl(DATASET_DIR / "intent_80.jsonl")
    retrieval_cases = read_jsonl(DATASET_DIR / "retrieval_18.jsonl")
    qa_cases = read_jsonl(DATASET_DIR / "qa_14.jsonl")
    if (len(intent_cases), len(retrieval_cases), len(qa_cases)) != (80, 18, 14):
        raise ValueError("Evaluation datasets must contain exactly 80 intent, 18 retrieval, and 14 QA cases")

    repo = JsonRepository()
    if not repo.load_posts() or not repo.load_documents():
        from scripts.seed import main as seed_main  # type: ignore[import-not-found]

        seed_main()
    retrieval = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    intent_metrics, intent_detail, intent_results = await evaluate_intent(intent_cases)
    retrieval_metrics_result, retrieval_results = await evaluate_retrieval(retrieval_cases, retrieval)
    qa_metrics, qa_results, qa_detail = await evaluate_qa(qa_cases)

    router = ProviderRouter()
    cache_probe = f"eval-cache-probe-{uuid.uuid4().hex}"
    await router.embed(cache_probe)
    cached_result = await router.embed(cache_probe)
    metrics = {
        **intent_metrics,
        **retrieval_metrics_result,
        **qa_metrics,
        "cache_repeat_hit_rate": float(cached_result.cache_hit),
    }
    degraded_modes = router.degraded_modes
    profile = "offline_deterministic_regression" if degraded_modes else "configured_provider_regression"
    return {
        "run_id": f"eval-{uuid.uuid4().hex[:10]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_version": "campusflow-hard-v2",
        "evaluation_profile": profile,
        "prompt_version": "campusflow-agent-v1",
        "model_version": ",".join(degraded_modes) if degraded_modes else "configured-real-providers",
        "case_counts": {"intent": len(intent_cases), "retrieval": len(retrieval_cases), "qa": len(qa_cases)},
        "methodology": {
            "intent": "Accuracy plus macro precision, recall, and F1 over paraphrase, overlap, OOD, and adversarial cases.",
            "retrieval": "Human-authored exact graded qrels with Hit@8, Precision@8, Recall@8, MRR@8, MAP@8, nDCG@8, and hard-negative rate.",
            "qa": "Reference fact groups, retrieved-context relevance, claim-evidence citation support, refusal F1, and replan F1.",
        },
        "limitations": [
            "Offline fake providers measure deterministic regression behavior, not production LLM quality.",
            "The 112-case suite is a development benchmark and must not be presented as an external or human-blind benchmark.",
            "Conversational quality still requires periodic human review and a held-out real-provider evaluation.",
        ],
        "metrics": metrics,
        "details": {"intent": intent_detail, "qa": qa_detail},
        "case_results": {"intent": intent_results, "retrieval": retrieval_results, "qa": qa_results},
    }


def write_report(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(report, ensure_ascii=False, indent=2)
    (REPORT_DIR / f"{report['run_id']}.json").write_text(json_text, encoding="utf-8")
    (REPORT_DIR / "latest.json").write_text(json_text, encoding="utf-8")
    lines = [
        f"# Eval Report {report['run_id']}",
        "",
        f"- Profile: `{report['evaluation_profile']}`",
        f"- Dataset: `{report['dataset_version']}`",
        "- Scores are measured, not hardcoded. Offline fake-provider scores are regression signals only.",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in report["metrics"].items():
        lines.append(f"| {key} | {value:.4f} |")
    lines.extend(["", "## Failed Cases", ""])
    failures = []
    failures.extend(
        f"- Intent `{item['id']}`: expected `{item['expected']}`, got `{item['predicted']}` - {item['input']}"
        for item in report["case_results"]["intent"] if not item["correct"]
    )
    failures.extend(
        f"- Retrieval `{item['id']}`: nDCG@8={item['ndcg_at_8']:.3f} - {item['query']}"
        for item in report["case_results"]["retrieval"] if item["ndcg_at_8"] < 0.8
    )
    failures.extend(
        f"- QA `{item['id']}`: fact={item['answer_fact_recall']:.3f}, citation={item['citation_precision']:.3f} - {item['question']}"
        for item in report["case_results"]["qa"]
        if item["answer_fact_recall"] < 1.0 or item["citation_precision"] < 1.0 and not item["expected_refusal"]
    )
    lines.extend(failures or ["- No failures in this development set."])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    markdown = "\n".join(lines) + "\n"
    (REPORT_DIR / f"{report['run_id']}.md").write_text(markdown, encoding="utf-8")
    (REPORT_DIR / "latest.md").write_text(markdown, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run())
    if args.write_report:
        write_report(report)
    selected = report if args.verbose else {
        key: report[key]
        for key in ["run_id", "evaluation_profile", "model_version", "case_counts", "metrics"]
    }
    print(json.dumps(selected, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
