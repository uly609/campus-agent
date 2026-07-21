# Agent Flow

The main workflow preserves six stages:

1. Coreference resolution.
2. Visual understanding.
3. Intent planning.
4. Tool execution.
5. Relevance gate and replan.
6. Grounded synthesis.

The graph exposes 13 nodes in code and trace output:

`input_guard_node`, `load_memory_node`, `coreference_resolver_node`, `visual_understanding_node`, `intent_planner_node`, `tool_executor_node`, `retrieval_gate_node`, `relevance_judge_node`, `replan_node`, `grounded_synthesis_node`, `output_guard_node`, `publish_memory_event_node`, and `persist_trace_node`.

Replan triggers on empty evidence, tool errors, or low coverage. The counter is clamped to `max_replans = 2`, and tests verify it cannot loop indefinitely.

