# Agent Flow

The main workflow preserves six stages:

1. Coreference resolution.
2. Visual understanding.
3. Intent planning.
4. Tool execution.
5. Relevance gate and replan.
6. Grounded synthesis.

The compiled LangGraph `StateGraph` exposes 13 nodes in code and trace output:

`input_guard_node`, `load_memory_node`, `coreference_resolver_node`, `visual_understanding_node`, `intent_planner_node`, `tool_executor_node`, `retrieval_gate_node`, `relevance_judge_node`, `replan_node`, `grounded_synthesis_node`, `output_guard_node`, `publish_memory_event_node`, and `persist_trace_node`.

Replan triggers on empty evidence, tool errors, or low coverage. The counter is clamped to `max_replans = 2`, and tests verify it cannot loop indefinitely.

When a real chat provider is configured, grounded synthesis requires structured claims bound to supplied evidence ids. Unknown ids, unsupported claims, malformed JSON, provider failure, or fake fallback cause deterministic grounded synthesis or an evidence-insufficient refusal.


## Dynamic planning, Tools, and procedural Skills

The planner receives one typed allowlist of executable tools. A real Chat provider may select a valid tool plan; Pydantic validation rejects malformed output, unknown tools, missing arguments, and wrong argument types before execution. Fake-provider and provider-failure paths use a deterministic planner so tests and degraded demos remain reproducible.

Procedural Skills are governed knowledge assets extracted from document sections, not aliases for tools. Each asset records executable steps, inputs, outputs, evidence quote, tags, and confidence. The retrieval Plan-Worker can return these assets alongside evidence so a later workflow can recommend or execute a documented procedure without treating document text as an instruction.
