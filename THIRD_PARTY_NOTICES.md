# Third-party reference notices

CampusFlow adapts design patterns from the Apache-2.0 licensed `Shubhamsaboo/awesome-llm-apps` repository:

- `rag_tutorials/agentic_typed_rag_pydanticai`: typed retrieval results, deterministic evidence gates, and verbatim quote validation.
- `rag_tutorials/corrective_rag`: relevance grading, query rewrite, and bounded external-search fallback.
- `rag_tutorials/rag_database_routing`: explicit source routing.
- `advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory`: query-scoped memory recall.

Upstream: https://github.com/Shubhamsaboo/awesome-llm-apps
License: Apache License 2.0. No PydanticAI, Streamlit, Qdrant, Mem0, or upstream model credentials are bundled.

`20czy/zafu_xiaolin_campus_agent` campus schedule, notice, venue, synthetic profile, weather service, Skill documents, and FastMCP weather server were adapted from upstream revision `1b678bd`. The user explicitly represented that the upstream author granted permission for this CampusFlow integration. The upstream revision did not contain a standard license file, so that permission applies to this authorized integration and must not be generalized to unrelated reuse.

Upstream: https://github.com/20czy/zafu_xiaolin_campus_agent
Data status: copied course, notice, venue, and student-profile fixtures are synthetic demo data; Open-Meteo weather calls are live when network access is available.
