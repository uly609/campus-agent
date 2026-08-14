# AtlasHub AI 面试总资料

这份总资料已从校园版更新为 **AtlasHub AI｜企业知识社区与智能治理 Agent**。

完整的当前版本以 [`campusflow-project-master.md`](./campusflow-project-master.md) 为准，避免项目代码、简历和面试回答出现两套口径。

## 当前口径

- 产品定位：企业知识社区与智能治理 Agent
- 核心链路：LangGraph、Planner/Executor、Tool Calling、Hybrid RAG、Multi-Agent、长期记忆、多模态解析和评测
- 文件能力：Excel、CSV、PDF、图片和文本解析；结果可以用于对话，也可以进入知识库
- 社区能力：内容检索、推荐、草稿生成、人工审核、举报处理和审计
- 可靠性：证据相关性判断、引用约束、有限 Replan、Prompt Injection 防护和 Trace
- 当前版本：后端 `0.2.0`，Prompt `atlashub-agent-v1`，提交 `90dc769`

## 面试回答顺序

所有问题按以下顺序回答：

```text
业务动机 -> 请求路径 -> 状态变化 -> 关键取舍 -> 失败边界 -> 验证指标
```

旧的校园课表、校园天气、校园通知、学生画像和小林适配内容不再属于当前项目实现，面试时不要再作为 AtlasHub AI 的功能描述。
