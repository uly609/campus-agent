# Eval

The eval suite contains:

- 80 intent classification cases.
- 18 retrieval cases.
- 14 campus QA cases.

The intent set contains 80 distinct utterances rather than numbered copies. Retrieval relevance supports complete source-id and source-prefix judgments, and each QA case records refusal, replan, and citation provenance.

Metrics are computed from predictions and agent outputs, then written to JSON and Markdown reports with per-case results. They include intent accuracy, Hit/Precision/Recall/MRR, claim recall, citation coverage and groundedness, refusal accuracy, Relevance Judge F1, replan/tool success, exact-cache repeat hits, and measured p50/p95 latency. Scores are not hardcoded.

The validated degraded-mode run `eval-4d42b39c8f` produced 100% intent accuracy, Hit@8, Recall@8, Precision@5, citation groundedness, refusal accuracy, and Judge F1. The stricter Precision@8 is 93.75% and remains visible in the report.
