# AtlasHub AI 面试资料

## 一句话介绍

AtlasHub AI 是一个面向企业知识社区的对话式 Agent 平台，融合企业知识库、社区内容治理、文档智能、多 Agent 协作、长期记忆和可追踪评测。

## 60 秒项目介绍

我做的是一个企业知识社区 Agent。用户可以通过聊天检索制度、流程、产品文档和社区经验，也可以上传 Excel、CSV、PDF 或图片进行结构化解析和问答，并生成需要人工确认的社区内容草稿。

后端使用 LangGraph 编排输入防护、记忆召回、上下文处理、意图规划、Tool Calling、Hybrid RAG、证据判断和回答生成。复杂任务通过 Supervisor-Worker 选择必要的 Worker，并使用共享 State、message_hub 和 artifacts 传递结果。系统还使用 Redis Stream 异步沉淀记忆事件，JSON Repository 保存长期记忆，并通过 Trace、引用校验和离线评测验证回答质量。

## 请求流程

```text
用户输入
 -> Prompt Injection 检测
 -> 短期上下文和长期记忆召回
 -> 图片/文件解析
 -> Planner 生成结构化计划
 -> Tool Registry 查找和 Tool Calling
 -> Hybrid RAG 或社区检索
 -> 证据相关性判断
 -> 有界 Replan
 -> 有据回答或拒答
 -> 输出防护
 -> 发布记忆事件
 -> Trace 持久化
```

## Multi-Agent 架构

系统采用集中式 Supervisor-Worker 模式：

- Supervisor：识别意图、选择最小 Worker 集、控制执行轮数和终止条件。
- Retrieval Worker：执行 BM25、向量、图谱检索和结果融合。
- Knowledge Worker：根据检索证据生成企业知识回答。
- Multimodal Worker：解析 Excel、CSV、PDF、图片和文本附件。
- Community Worker：分析帖子、推荐内容和治理状态。
- Draft Worker：生成需要人工确认的社区内容草稿。
- Evaluation Worker：读取并解释评测指标。
- General Worker：处理通用问答和附件总结。

Worker 不直接互相调用，而是通过共享状态协作：

```python
state["message_hub"]  # 记录 Agent 过程
state["artifacts"]    # 保存证据、解析片段、草稿和评测结果
```

系统设置最大执行轮数；当所有必要 Worker 完成或达到上限后，进入 Finalize，避免死循环和无效调用。

## Tool Calling、Skill 和 MCP

- Tool 是可执行的原子能力，包含输入参数、执行函数、结果和来源信息。
- Skill 是从受治理文档中抽取的可复用 SOP 知识资产，包含步骤、输入、输出、证据片段和置信度，不是第二套工具目录。
- Planner 只从 Tool Registry 的白名单中选择可执行工具；Skill 作为流程知识被相关 Worker 检索和参考，Pydantic 负责工具参数校验。
- MCP 是外部工具的标准接入协议；Skill 负责能力组织，MCP 负责工具通信。

## RAG 全链路

1. 解析文档并清洗内容。
2. 按文档结构、Sheet、页码和行范围切分。
3. 建立 BM25、Embedding、Neo4j Vector Index 和 GraphRAG 索引。
4. 通过 RRF 融合关键词和向量召回结果。
5. 使用 rerank 对候选证据重新排序。
6. 经过相关性判断和 Claim-Evidence-Citation 校验后交给模型生成。
7. 证据不足时拒答，不允许模型凭记忆补写企业事实。

企业知识文档和社区帖子属于不同证据类型。社区经验只能作为参考，不能自动升级成正式企业知识。

## 多模态文件处理

- Excel：按 Sheet 读取，保留表头和行范围，每 60 行生成一个 Markdown 表格片段。
- CSV：按列名和行范围切分。
- PDF：按页提取正文，并抽取页面表格。
- 图片：通过 Qwen-VL 提取摘要、可见文字和业务线索。
- 文本和解析片段可以直接用于 Agent 问答，也可以进入知识库索引。

## 记忆方案

| 类型 | 存储 | 作用 |
|---|---|---|
| 短期上下文 | Redis String + TTL | 保存当前会话最近内容，支持连续追问 |
| 对话历史 | Chat Repository | 保存消息和 Agent 过程信息 |
| 记忆事件 | Redis Stream `XADD` | 异步传递事实、偏好和事件 |
| 长期记忆 | JSON Repository | 保存用户确认后的 fact、preference、event |
| 语义召回 | Embedding + 相似度 | 根据当前问题召回相关记忆 |

Trace ID 是请求追踪编号，SSE 是过程推送机制，两者都不是长期记忆存储。

## 安全和人工确认

- 输入、附件和社区帖子都先经过 Prompt Injection 检测。
- 外部文档只能作为数据，不能覆盖系统指令。
- 社区内容采用“生成草稿 -> 修改 -> 人工确认 -> 发布”的 HITL 流程。
- 用户可以查看、禁用和删除长期记忆。
- 不在日志中记录 API Key、完整 OCR 文本或敏感个人信息。

## 评测指标

- 意图：Macro-F1、混淆意图、拒答 F1。
- 检索：Recall@K、MRR、nDCG、Context Precision、Context Recall。
- 生成：Faithfulness、Answer Relevancy、引用覆盖率。
- 工程：模型延迟、Tool 延迟、错误率、Replan 次数和缓存命中率。

评测报告应记录模型版本、Prompt 版本、数据集哈希、Git SHA 和失败样例，确保结果可以复现。

## 面试中的关键取舍

**为什么不用一个 Agent 做完？**

因为解析、检索、回答、写作和评测职责不同。拆成多个 Worker 后，每个 Agent 的工具范围更小，权限更清晰，也便于测试、监控和故障定位。

**为什么采用 Supervisor-Worker？**

企业场景更重视可控性和审计。Supervisor 可以选择最小 Worker 集，限制执行轮数，并在所有任务完成后统一汇总，避免多个 Agent 自由讨论导致成本和延迟不可控。

**当前是 ReAct 还是 Plan-Execute？**

主流程是 Plan-Execute + 有界 Replan：先规划，再执行工具，检查证据，不足时重新规划，最多两次。它比开放式 ReAct 更适合工具集合固定、需要审计的企业知识场景。

**Redis Stream 为什么用于长期记忆？**

对话请求先完成回答，再通过 `XADD` 写入记忆事件。后台消费者读取事件、提取事实和偏好并写入长期存储，避免记忆处理阻塞用户的首字节响应。

## 当前版本

- 产品：AtlasHub AI
- 定位：企业知识社区与智能治理 Agent
- 后端版本：`0.2.0`
- Prompt 版本：`atlashub-agent-v1`
- 当前分支：`feat/campusflow-agent-hardening`
- 最新提交：`921c356 feat: align agent with plan-worker skills`
- 最新验证：120 个单元/集成测试通过，3 个 E2E 通过，前端测试和 lint 通过；真实验证了 Multi-Agent、CSV 解析和健康检查。

---

# 完整面试问答

## 一、项目定位与业务价值

### 1. 这个系统主要解决什么问题？

企业里的制度、产品文档、交付流程、FAQ 和社区经验通常分散在不同地方。普通大模型不知道企业内部事实，即使回答出来也很难说明来源。

AtlasHub AI 把知识库检索、社区内容、文件解析和 Agent 工作流放在一个统一入口里，解决三个问题：

1. 企业资料能不能被准确检索。
2. 模型回答能不能追溯到证据。
3. 复杂任务能不能自动拆解并受控执行。

### 2. 为什么不是简单的聊天机器人？

简单聊天通常只有一次模型调用，适合润色和通用问答。但企业问题可能需要：

```text
识别意图 -> 查知识库 -> 解析附件 -> 调用工具
-> 判断证据 -> 生成回答 -> 人工确认 -> 审计
```

因此系统核心不是“调用一次大模型”，而是把多个步骤编排成有状态、可观察、可终止的工作流。

### 3. 为什么选择企业知识社区这个场景？

单纯 RAG 只能回答文档问题，单纯社区系统又缺少知识核验。企业知识社区同时具备：

- 正式知识：制度、流程、产品文档。
- 非正式知识：经验分享、问题讨论、案例帖子。
- 内容生产：通知、经验文章、FAQ 草稿。
- 内容治理：举报、审核、来源和版本管理。

这能体现 Agent 不只是问答，而是完整业务闭环。

## 二、完整请求链路

### 1. 用户输入

系统接收：

- 文本问题。
- 图片附件。
- Excel/CSV/PDF/TXT/Markdown 文档。
- 多轮会话上下文。

请求首先生成 `request_id` 和 `trace`，后续所有节点和 Tool Calling 都关联到这次请求。

### 2. 输入安全检查

系统检测：

- “忽略之前指令”等 Prompt Injection。
- 附件中隐藏的恶意指令。
- 用户输入中的手机号、身份证号等敏感信息。

附件和社区帖子只被当作数据，不能改变 Agent 的系统规则。

### 3. 记忆召回

系统先读取用户可用记忆，再根据当前问题做相关性召回。记忆只用于个性化，不作为企业正式事实证据。

例如用户偏好写成“喜欢简洁回答”，可以影响表达方式，但不能用来证明“公司的退款流程是什么”。

### 4. 上下文处理

如果用户说“那它呢”“这个流程下一步是什么”，系统结合上一轮问题进行指代消解，形成完整查询，再交给 Planner。

### 5. 文件和图片解析

有附件时，Multimodal Worker 先处理文件，生成结构化 chunk。解析结果进入共享 artifacts，后续检索和回答 Worker 可以继续使用。

### 6. 意图规划

Planner 输出结构化计划：

```json
{
  "intent": "knowledge_qa",
  "tool_calls": [
    {
      "tool_name": "search_knowledge_base",
      "arguments": {"query": "产品交付流程"}
    }
  ],
  "confidence": 0.94,
  "source": "model"
}
```

模型生成的计划不会直接执行，必须通过注册表和参数校验。

### 7. 工具执行

Tool Registry 根据工具名称找到真实函数，校验参数、执行、记录结果和延迟，并把结果加入 `tool_results` 和 `retrieved_evidence`。

### 8. 检索门控

如果没有证据，或者证据数量太少，系统不会直接让模型回答，而是记录低证据状态并触发有限 Replan。

### 9. 相关性判断

系统判断检索结果是否真正回答了当前问题，包括：

- 关键词是否相关。
- 证据是否覆盖问题中的关键实体。
- 证据是否来自允许的数据源。
- 社区经验是否被误当成正式制度。

### 10. Replan

第一次不足时进行查询改写或扩大本地检索；第二次可以调用配置好的外部官方搜索。最多两次，超过后必须拒答或明确说明证据不足。

### 11. 回答生成

回答生成器根据证据生成 claim，并为 claim 绑定 citation。无法绑定来源的事实不会被当成确定答案输出。

### 12. 输出与持久化

最终输出还会经过安全检查，同时保存：

- 请求 Trace。
- Tool Calling 结果。
- 检索证据和引用。
- 模型提供商和降级状态。
- 异步记忆事件。

## 三、Multi-Agent 深度问答

### 1. 什么是 Multi-Agent？

Multi-Agent 不是简单地调用多个模型，而是把复杂任务拆成多个职责独立、权限不同、可以协作的 Agent。

当前采用集中式 Supervisor-Worker：

```text
Supervisor
  -> Retrieval Worker
  -> Knowledge Worker
  -> Multimodal Worker
  -> Community Worker
  -> Draft Worker
  -> Evaluation Worker
  -> General Worker
```

### 2. 为什么单个 Agent 不够？

一个 Agent 同时拥有解析、检索、写作、审核和评测工具，会导致：

- 工具目录过大。
- Prompt 复杂。
- 权限边界模糊。
- 任务失败后很难定位。
- 上下文里混入大量无关结果。
- 成本和延迟不可控。

拆分后，每个 Worker 只关注一个职责，测试和监控更容易。

### 3. Supervisor 怎么选择 Worker？

Supervisor 先做意图判断：

- 出现 Excel、PDF、图片、拆分、识别：选择 Multimodal Worker。
- 出现知识库、制度、流程、产品文档：选择 Retrieval/Knowledge Worker。
- 出现帖子、推荐、举报、审核：选择 Community Worker。
- 出现生成、起草、通知：选择 Draft Worker。
- 出现评测、指标、报告：选择 Evaluation Worker。
- 无明确业务意图：选择 General Worker。

它只选择完成任务所需的最小集合，而不是每次都调用全部 Agent。

### 4. Multi-Agent 怎么共享状态？

共享状态包含：

```python
{
    "query": "...",
    "required_workers": [...],
    "message_hub": [...],
    "artifacts": {...},
    "worker_results": [...],
    "trace": [...],
    "degraded_mode": [...]
}
```

`message_hub` 负责过程消息；`artifacts` 负责结构化业务结果；`worker_results` 负责状态和成功失败记录。

### 5. Agent 之间为什么不直接传自然语言？

自然语言容易丢字段、产生歧义，也不利于校验。结构化 artifact 可以保留：

- source_id。
- 页码、Sheet、行范围。
- score。
- citation。
- 解析模式。
- degraded 状态。

后续 Agent 只读取必要字段，避免上下文膨胀。

### 6. 怎么避免模型跑偏？

系统有多层约束：

1. Worker 白名单。
2. Tool Registry 白名单。
3. Pydantic 参数校验。
4. 外部内容不可信隔离。
5. 证据门控。
6. 输出引用校验。
7. 最大 Worker 轮数。
8. Prompt Injection 检测。

### 7. 怎么避免死循环？

- `max_turns` 限制 Multi-Agent 最大执行轮数。
- Replan 最多两次。
- 已执行 Worker 写入 `worker_results`，不会重复调度。
- 所有 Worker 完成后直接进入 Finalize。
- Supervisor 遇到安全标记直接终止。

### 8. 这是并行 Multi-Agent 吗？

当前主要是有序的 Supervisor-Worker 协作，不应该夸大成所有 Worker 并行执行。这样做的优点是依赖关系清晰，例如先解析文件，再检索，再生成草稿。

未来对于没有依赖关系的任务，例如同时做社区推荐和评测查询，可以在 LangGraph 中增加并行分支和汇聚节点。

## 四、RAG 深度问答

### 1. 数据处理流程是什么？

```text
上传文件
 -> 文件类型识别
 -> 内容解析
 -> 清洗和标准化
 -> 结构化元数据
 -> 业务切块
 -> Embedding/BM25 建索引
 -> 版本化入库
```

元数据包括文档 ID、来源、标题、页码、Sheet、行范围、版本、部门、可见性和更新时间。

### 2. Excel 怎么处理？

使用 `openpyxl` 读取工作簿：

1. 遍历每个 Sheet。
2. 读取第一行作为表头。
3. 过滤空行。
4. 转换为 Markdown 表格。
5. 每 60 行生成一个 chunk。
6. 在 metadata 中保存 Sheet 名和行起止范围。

这样回答“某个客户在哪一行”时，可以定位到具体 Sheet 和行范围。

### 3. PDF 怎么处理？

使用 `pdfplumber`：

- 每页提取正文。
- 每页单独提取表格。
- 正文和表格分别生成 chunk。
- 保存页码、表格编号和文件名。

对于扫描 PDF，当前系统依赖配置的 VLM/OCR 能力；没有视觉模型时必须明确返回降级状态。

### 4. 分块策略是什么？

当前不是所有文件都使用同一套固定长度：

- TXT/Markdown：按段落切分。
- Excel/CSV：按表头和行范围切分。
- PDF：按页和表格切分。
- 图片：先提取结构化观察结果，再作为视觉 chunk。

生产环境可以继续扩展标题层级切分、父子 chunk、语义切分和业务记录切分。

### 5. 为什么要 Hybrid RAG？

BM25 对产品编号、合同号、错误码和专有名词更可靠；向量检索对同义表达和自然语言问题更好；图谱检索适合实体关系问题。

组合后：

```text
关键词召回 + 向量召回 + 图关系扩展
 -> RRF 融合
 -> Rerank
 -> 相关性门控
```

### 6. Recall 不高怎么优化？

- 改善 PDF、表格和扫描件解析。
- 增加查询改写和同义词扩展。
- 优化 chunk 边界，避免一个事实被切开。
- 调整 BM25 和向量召回比例。
- 增加父子 chunk 或标题路径。
- 用 rerank 处理召回候选。
- 构造 hard negative，避免模型只记住关键词。
- 对 Recall@K、MRR、nDCG 分层评估。

## 五、记忆、上下文和会话

### 1. 短期记忆和短上下文的区别

- 短期记忆：系统保留的最近对话或会话状态。
- 短上下文：本次调用实际拼给模型的有限内容。

短期记忆可以比单次模型上下文保存更多，但每次只选相关部分放入短上下文。

### 2. 长期记忆和长上下文的区别

- 长期记忆：跨会话、结构化、可管理的用户事实和偏好。
- 长上下文：一次模型调用允许携带的大量文本窗口。

长上下文不是长期记忆。长期记忆需要抽取、去重、冲突替换、过期和删除；长上下文只是模型输入容量。

### 3. Redis Stream 的作用

请求完成后使用 `XADD` 写入记忆事件：

```text
XADD memory_events * user_id u1 session_id s1 content "用户偏好简洁回答"
```

后台消费者读取事件，抽取 fact、preference 或 event，再写入 JSON Repository。这样记忆抽取不会阻塞聊天响应。

### 4. 为什么不用普通 Redis String？

String 适合保存当前值或缓存；Stream 更适合追加事件：

- 有顺序 ID。
- 支持按范围读取。
- 可以保留事件历史。
- 后台消费者可以异步处理。
- 发生故障后可以重新读取。

它不是“传递双向记忆”，而是把对话产生的记忆事件从在线请求链路传给异步提取链路。

## 六、Tool Calling、Plan-Worker 与 Skill

### 1. Tool Calling 的完整过程

```text
用户问题
 -> Supervisor 判断是否需要拆分
 -> Plan-Worker 生成有界子问题
 -> Tool Registry 查找函数
 -> Schema 校验
 -> 并行执行检索/解析工具
 -> 合并证据与流程知识
 -> Agent 生成回答
```

模型只提出结构化调用请求，真正执行权在后端。

### 2. Skill 和 Tool 的区别

Tool 是原子执行动作，例如搜索知识库、检索社区、解析附件或读取评测报告。

Skill 不是工具分组，而是从受治理文档中抽取的可复用流程知识资产，例如：

```text
名称：版本发布流程
步骤：执行测试 -> 构建镜像 -> 人工确认 -> 发布
输入：版本号、代码仓库
输出：已发布版本
证据：原文中的流程片段
```

因此面试时要说：Agent 负责编排，Plan-Worker 负责拆分和执行子问题，Tool 负责真实动作，Skill 负责沉淀有证据的 SOP 知识。

## 七、普通模式和 Agent 模式

### 普通模式

适合：

- 通用概念解释。
- 文本润色。
- 用户提供内容的总结。
- 简单闲聊。

特点是延迟低、成本低，不主动确认企业内部事实。

### Agent 模式

适合：

- 查询企业知识库。
- 读取 Excel/PDF/图片。
- 搜索社区内容。
- 生成内容草稿。
- 查看评测和执行过程。

特点是会显示计划、Worker、Tool、证据、引用和降级状态。

## 八、评测系统

### 1. 为什么要做评测？

Agent 不是能回答一次就代表质量好。需要知道是意图识别错、检索漏召回、重排错误、证据不足，还是生成阶段幻觉。

### 2. 评测集怎么构建？

每条样本包含：

```json
{
  "query": "产品退款流程是什么？",
  "expected_intent": "knowledge_qa",
  "relevant_sources": ["doc-refund-v2"],
  "reference_answer": "...",
  "should_refuse": false
}
```

还要加入：

- 同义表达。
- 多意图问题。
- 缺少证据问题。
- 冲突文档。
- Prompt Injection。
- 社区帖子与正式文档冲突。

### 3. 指标解释

- Macro-F1：不同意图平均表现，避免大类掩盖小类。
- Recall@K：相关证据是否进入前 K 个结果。
- MRR：第一个正确结果排得多靠前。
- nDCG：多个相关结果的排序质量。
- Faithfulness：回答是否被证据支持。
- Answer Relevancy：回答是否真正回应问题。
- Citation Coverage：事实 claim 是否有引用。
- Refusal F1：证据不足时该拒答是否拒答。

## 九、并发、缓存和成本

### 1. 如何处理并发？

- FastAPI 异步接口。
- Redis 缓存相同模型请求。
- Tool 调用设置超时。
- 非核心能力失败时降级。
- Multi-Agent 限制 Worker 数量和轮次。
- 文档入库通过 Redis Stream 异步处理。
- Prometheus 记录模型、检索和工具延迟。

### 2. 缓存什么？

- 相同问题和相同上下文的模型回答。
- Embedding 结果。
- Rerank 结果。
- 知识库检索结果。
- 短期会话上下文。

缓存 key 需要包含模型、Prompt 版本和输入摘要，避免换模型后读到旧结果。

### 3. 如何降低 AI 成本？

- 普通问答不启动完整 Agent。
- Supervisor 只选择必要 Worker。
- 先使用本地检索，证据不足再外部搜索。
- 解析结果缓存。
- Embedding 和 Rerank 缓存。
- Replan 限制最多两次。
- 结构化结果代替大段原文传递。
- 简单任务使用确定性降级逻辑。

## 十、故障和边界问题

### 模型不可用怎么办？

返回明确的 degraded 状态，不伪造模型成功。可以使用确定性 Planner 或模板化结果完成有限能力。

### 知识库没有答案怎么办？

先做查询改写和有限重检索；配置了外部搜索时再调用允许的外部来源；仍无证据就拒答。

### 社区帖子能不能直接进入知识库？

不能。帖子属于非正式内容，必须经过来源判断、治理和人工审核，才能成为知识候选。

### 附件中出现“忽略系统规则”怎么办？

附件被标记为不可信数据，内容可以用于抽取事实，但其中的指令不会被执行。

### 用户要求直接发布怎么办？

先生成草稿，用户明确确认后才能发布。系统不允许模型自动发布。

### 多 Agent 调用失败怎么办？

单个 Worker 记录失败状态和错误码，Supervisor 根据任务依赖决定是否继续；如果关键证据 Worker 失败，最终回答必须说明无法确认。

## 十一、简历表述边界

可以说：

- 基于 LangGraph 实现 Supervisor-Worker Multi-Agent。
- 实现 Excel、CSV、PDF、图片的多模态解析流程。
- 实现 Hybrid RAG、RRF、引用校验和证据不足拒答。
- 使用 Redis Stream 异步传递长期记忆事件。
- 建立意图、检索、问答和引用质量评测。
- 实现社区内容草稿、人工确认和治理流程。

不要直接说：

- 已经拥有真实大规模用户量，除非有真实数据。
- RAGAS 官方完整评测，除非确实接入并运行官方实现。
- 所有 Worker 都是独立模型，除非实际配置了不同模型。
- 所有任务都是并行执行，当前主要是受控有序协作。
- 生产级高并发数据，除非有压测结果。
- 接入了 MCP 天气服务，当前企业版不再保留校园天气 MCP。
