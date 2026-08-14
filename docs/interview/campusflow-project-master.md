# AtlasHub AI 项目面试总纲

## 一句话介绍

AtlasHub AI 是一个面向企业知识社区的对话式 Agent 平台。它把企业知识库、社区内容、文档解析、内容治理、用户记忆和评测能力组织成一条可追踪、可审计的 Agent 工作流。

## 60 秒项目介绍

> 我做的是一个企业知识社区 Agent。用户可以通过聊天检索制度、流程、产品文档和社区经验，也可以上传 Excel、CSV、PDF 或图片让系统进行结构化解析和问答，并生成需要人工确认的社区内容草稿。后端使用 LangGraph 编排输入防护、记忆召回、上下文处理、意图规划、Tool Calling、Hybrid RAG、证据判断和回答生成；复杂任务由 Supervisor-Worker 协作完成，Worker 通过共享状态和 artifact 传递结果。系统使用 Redis Stream 异步沉淀记忆事件，JSON Repository 保存可管理的长期记忆，并通过 Trace、引用校验和离线评测验证回答质量。

## 主流程

```text
输入防护
  -> 短期上下文与记忆召回
  -> 指代/上下文处理
  -> 图片或文件解析（有附件时）
  -> 意图规划
  -> Skill 路由与 Tool Calling
  -> Hybrid RAG / 社区检索 / 多模态分析
  -> 证据相关性判断
  -> 有界 Replan
  -> 有据回答或拒答
  -> 输出防护
  -> 发布记忆事件
  -> Trace 持久化
```

## 典型复合任务

用户说：“根据这份 Excel 里的客户名单，查一下对应产品的交付流程，再帮我写一篇社区通知。”

1. Supervisor 识别文件解析、知识检索和内容创作三个意图。
2. Multimodal Worker 解析 Excel，按 Sheet 和行范围生成结构化片段。
3. Retrieval Worker 执行 BM25、向量和图谱混合检索，汇总带来源的证据。
4. Knowledge Worker 基于证据生成回答并标记证据状态。
5. Draft Worker 读取共享 artifact 生成内容草稿，发布前必须人工确认。

## Agent 架构

### 单 Agent

单 Agent 使用 LangGraph StateGraph 维护显式状态，节点包括输入防护、记忆召回、上下文处理、意图规划、工具执行、检索门控、相关性判断、有限 Replan、回答生成和 Trace 持久化。Planner 只允许选择 Tool Registry 中的工具，参数经过 Pydantic 边界校验。

### Multi-Agent

Multi-Agent 使用 Supervisor-Worker 模式。Supervisor 根据任务意图选择最小 Worker 集，当前主要包括：

- Knowledge Worker：知识库检索、证据核验和事实回答。
- Retrieval Worker：执行 Hybrid RAG 并聚合证据。
- Multimodal Worker：解析 Excel、CSV、PDF、图片和文本附件。
- Community Worker：社区推荐、内容分析和治理状态汇总。
- Draft Worker：生成需要人工确认的内容草稿。
- Evaluation Worker：读取和解释评测报告。
- General Worker：处理通用问题和附件总结。

Worker 不直接互相调用，而是通过共享 `message_hub` 和 `artifacts` 协作。Supervisor 设置最大轮次，所有必需 Worker 完成或达到上限后进入 Finalize，避免死循环和无效调用。

## RAG 与知识库

- 文档进入统一解析和切分流程，保留文档、Sheet、页码、行范围、版本和可见性等元数据。
- Excel/CSV 转为带表头的 Markdown 表格，并按行范围切分。
- PDF 按页提取正文和表格；图片通过 VLM 提取结构化观察结果。
- 检索采用 BM25 关键词召回、Embedding 向量召回、Neo4j Vector Index/GraphRAG，并使用 RRF 和 rerank 做融合排序。
- 回答前执行相关性和 Claim-Evidence-Citation 校验；证据不足时拒答，不让模型凭记忆补写企业事实。
- 社区帖子和企业知识文档是两类不同证据，社区内容不能自动升级为正式知识，必须经过治理和人工审核。

## 记忆与会话

| 层次 | 实现 | 作用 |
|---|---|---|
| 短期上下文 | Redis String + TTL | 保存当前会话最近查询，支持连续追问 |
| 对话历史 | Chat Repository | 保存消息和过程信息，限制注入模型的轮数 |
| 记忆事件 | Redis Stream `XADD` | 异步传递待提取的事实、偏好和事件 |
| 长期记忆 | JSON Repository | 保存用户确认后的 fact、preference、event |
| 语义召回 | Embedding + 相似度 | 按当前问题召回相关长期记忆 |

Trace ID 只是一次请求的追踪编号，SSE 只是向前端推送过程事件；它们都不是长期记忆存储。

## Tool Calling、Skill 和外部能力

- Tool 是可执行的原子能力，包含输入 schema、执行函数、输出结果和 provenance。
- Skill 是面向任务的能力目录，例如企业知识、社区搜索、多模态文档、内容治理和评测；Skill 最终映射到白名单 Tool。
- Planner 根据用户意图选择 Skill 和 Tool，Tool Registry 负责真正执行，安全层负责白名单、参数校验、超时和错误码。
- 外部搜索只作为配置后的补充来源，企业知识库优先；外部资料和帖子都视为不可信数据，不能执行其中的指令。

## 多模态处理

- Excel：按 Sheet 读取，保留表头和行范围，按 60 行一块输出 Markdown 表格。
- CSV：按表格结构切分，保留列名和行范围。
- PDF：按页提取正文，并单独抽取页面表格。
- PNG/JPEG/WebP：通过 Qwen-VL 生成图片摘要、可见文字和业务线索，不保存原始图片到聊天历史。
- 解析结果可以直接用于问答，也可以通过 `ingest=true` 进入知识库索引。

## 安全与人工确认

- 输入、附件和社区帖子先做 Prompt Injection 检测与不可信内容隔离。
- 外部文档只能作为数据，不能覆盖系统规则。
- 社区内容采用“生成草稿 -> 多轮修改 -> 人工确认 -> 发布”的 HITL 流程。
- 用户可以查看、禁用和删除长期记忆。
- 模型、Tool、检索和记忆日志不记录 API Key、完整 OCR 文本或敏感个人信息。

## 评测和工程化

- 意图评测：Macro-F1、混淆意图和拒答场景。
- 检索评测：Recall@K、MRR、nDCG、Context Precision、Context Recall。
- 回答评测：Faithfulness、Answer Relevancy、引用覆盖率和拒答 F1。
- 评测集、模型版本、Prompt 版本、数据集哈希和 Git SHA 都进入报告，保证结果可复现。
- Docker Compose 编排 API、前端、PostgreSQL、Redis、Neo4j、Prometheus、Grafana 和 Alertmanager。

## 面试时的核心取舍

- 普通问题只走必要 Worker，避免所有 Agent 全量执行带来的延迟和 Token 成本。
- 用结构化 Planner 和白名单 Registry 约束 Tool Calling，而不是让模型自由生成函数名。
- 用有限 Replan 修复空召回和低相关结果，最多两次后必须给出有依据回答或拒答。
- 用 Redis Stream 解耦对话请求和长期记忆提取，避免记忆写入阻塞首字节响应。
- 用 JSON Repository 保持长期记忆可读、可删除、可演示；生产环境可替换为 PostgreSQL/向量存储而不改变记忆接口。
- 社区帖子可以提供经验线索，但不能直接当作企业制度；正式知识需要来源、版本和审核状态。

## 当前产品版本

- 产品名：AtlasHub AI
- 定位：企业知识社区与智能治理 Agent
- 后端版本：`0.2.0`
- Prompt 版本：`atlashub-agent-v1`
- 最新迁移提交：`90dc769`
