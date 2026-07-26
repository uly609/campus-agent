# Eval

The eval suite contains:

- 80 intent classification cases.
- 18 retrieval cases.
- 14 campus QA cases.

The `campusflow-hard-v2` suite is a development regression benchmark. The intent set includes standard utterances plus paraphrase, overlapping-intent, implicit-memory, OOD, and adversarial cases. Retrieval uses exact, human-authored graded qrels instead of source-id prefixes. QA cases include multi-fact questions, hard negatives, partial evidence, conflicts, prompt injection, and evidence-insufficient requests.

Metrics are computed from predictions and agent outputs, then written to JSON and Markdown reports with failed-case details:

- Intent: accuracy and macro precision, recall, and F1.
- Retrieval: Hit@8, Precision@8, Recall@8, MRR@8, MAP@8, nDCG@8, and hard-negative rate@5.
- QA: reference-fact recall, retrieved-context relevance, citation precision, answer faithfulness, and forbidden-content rate.
- Control flow: refusal precision/recall/F1 and replan precision/recall/F1 are measured separately.
- Operations: tool success, explicit cache-hit state, and measured p50/p95 latency.

The validated offline run `eval-8645577496` measured 76.25% intent accuracy, 71.63% nDCG@8, 71.43% answer-fact recall, 60% citation precision, 80% refusal F1, and 66.67% replan F1. These are intentionally not converted into pass/fail marketing claims. The report identifies every weak case so retrieval and planning work can be prioritized.

Offline runs use explicit fake Chat, Embedding, and VLM providers and only measure deterministic regression behavior. They do not establish production LLM quality or replace a held-out, human-reviewed real-provider evaluation. Scores are computed, never hardcoded.
