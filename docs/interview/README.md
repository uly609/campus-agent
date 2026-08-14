# AtlasHub AI 面试资料库

这套资料用于准备 `AtlasHub AI` 的项目介绍、技术面试、场景题和项目拷问。

## 使用原则

1. 先以当前仓库代码和测试为准，再吸收本地资料中的通用设计。
2. 面试回答明确区分：当前已经实现、当前的降级实现、生产环境扩展方案。
3. 不把参考资料中的技术名词直接写进简历。`LangMem`、标准 ReAct、真正的长上下文压缩、Consumer Group 等，只有代码落地后才能写成已实现。
4. 每个项目问题都按“业务动机 → 请求路径 → 状态变化 → 并发/失败 → 验证指标”回答。

## 资料全集盘点

| 来源 | 当前可读取内容 | 用途 |
|---|---:|---|
| `JavaGuide-2026年3月24日` | 157 篇 Markdown、1 个 PDF | Java、Redis、MySQL、微服务、高并发、系统设计、项目面试 |
| `Java开发核心技术面试宝典` | 25 个 PPTX、60 个视频、3 个 XMind | Java 基础、集合、IO、并发、设计模式 |
| `xfg` | 185 篇 Markdown | 知识星球（ZSXQ）导出：业务系统、优惠券、缓存、MQ、分布式、简历和面试经验；不是语雀 |
| `zafu_xiaolin_campus_agent` | 15 篇 Markdown、135 个代码文件 | 参考小林 Agent 的 Planner、ToolSelector、TaskExecutor、MCP 和校园 Skill |
| `知识星球JavaGuide面试大全` | 37 个 PDF | 后端面试和系统设计补充资料 |
| `代码随想录知识星球精华` | 10 个 PDF | 算法、C++、Go 和面经补充资料 |
| `马哥12306` | 104 篇 Markdown、8 个 PDF、10 个视频 | 12306 业务、分布式和项目实战补充 |
| `JavaGuide`/`马哥12306` 中的 Yuque 镜像 | 多篇 Markdown 含 `yuque.com` 原文链接 | 可作为本地语雀内容镜像，但需按文件标注来源，不能推断覆盖完整语雀知识库 |
| 语雀当前可见账号 | 默认知识库 1 篇欢迎文档 | 当前账号未显示用户所说的完整资料库，不能冒充已读取 |

## 文档目录

- [AtlasHub AI 面试总资料](./campusflow-interview-complete.md)
- [资料清单与核验状态](./source-inventory.md)
- [AtlasHub AI 项目总纲](./campusflow-project-master.md)
- [RAG 与 Agent 深挖稿](./rag-agent-deep-dive.md)
- [面试回答边界](./answer-boundaries.md)
- [题库索引](./question-index.md)
- [项目资料映射](./project-topic-map.md)
- [统一回答模板](./structured-answers.md)
- [故障链与验证题](./failure-and-verification.md)
- [重点资料核验矩阵](./coverage-matrix.md)
- [面试串讲话术](./interview-scripts.md)
- [学习路线与核验清单](./study-roadmap.md)
- [代码证据索引](./code-evidence-index.md)
- [本地资料库逐库导读](./source-family-guides.md)
- [第二层项目拷问](./campusflow-grilling-advanced.md)
- [本地资料逐文件清单](./source-file-manifest.md)
- [XMind 面试宝典导读](./xmind-guide.md)
- [视频资料主题映射](./video-topic-guide.md)
- [当前项目说法审计](./current-claim-audit.md)
- [本地 Yuque 镜像索引](./local-yuque-mirror-index.md)

后续题库按模块拆分为：Java/并发、MySQL/Redis、MQ/分布式、微服务/系统设计、RAG/Agent、多模态/评测、AtlasHub AI 项目拷问。
