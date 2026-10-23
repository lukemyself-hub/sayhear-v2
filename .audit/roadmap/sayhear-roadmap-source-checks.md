# SayHear 路线调研的一手来源复核

状态为工作记录。最终结论在主计划与研究依据中维护。

## 主 Agent 已核对

| 来源 | 支持的事实 | 不支持的外推 |
| --- | --- | --- |
| https://ai-sdk.dev/docs/agents/overview | ToolLoopAgent 提供工具循环、上下文与停止控制。 | 不证明跨函数重启恢复或产品记忆质量。 |
| https://ai-sdk.dev/docs/agents/memory | 可用 Provider 工具、Memory provider 或自定义工具。控制权和接入成本不同。 | 不等于完整隐私、删除与证据治理。 |
| https://openai.github.io/openai-agents-js/guides/models/ | ModelProvider 返回 Model，自定义 Model 实现 getResponse 和 getStreamedResponse，可传入 Runner。部分能力依赖 Responses API。 | 不保证所有 Provider 能力等价。 |
| https://docs.langchain.com/oss/javascript/langgraph/overview | 低层有状态编排，支持持久执行、人工介入与记忆，LangChain 非必需。 | 不证明是当前简单文本产品最省维护的路线。 |
| https://mastra.ai/docs/memory/overview | 消息历史、working memory、semantic recall、observational memory，支持 resource 与 thread 作用域，需要存储。 | 不承诺满足 SayHear 的逐条来源、画像解释和完整遗忘。 |
| https://vercel.com/docs/queues | Beta，至少一次投递，可重试，提供发布去重，Workflows 是更高层编排。 | 不代表消费端副作用恰好一次。 |
| https://vercel.com/docs/agent-harnesses | durable-harness 把会话和运行中回合写入日志，通过队列恢复。中断中的模型调用会重跑，工具按重放规则处理。 | 不等于完整多用户产品，亦不消除重复副作用。页面日期元数据异常，不作为发布日期。 |
| https://inflection.ai/blog/pi | 官方定位强调倾听、好奇、友好和承认不确定。 | 不能证明真实体验始终符合定位。 |
| https://nomi.ai/updates/mind-map-2-0-bringing-nomi-memory-into-view/ | 官方公开记忆图谱与表格，允许编辑和新增；按聊天房间隔离。 | 未在所读正文确认完整删除保证，不能套用旧文冲突结论。 |
| https://profiles.wustl.edu/en/publications/the-science-of-effective-learning-with-spacing-and-retrieval-prac/ | 2022 年综述支持间隔学习和提取练习，讨论元认知与学习者误判。 | 不规定 SayHear 学习时数，也不直接验证软件项目教学流程。 |

## 补充核对

- https://honcho.dev/docs/ 将 Honcho 定位为开放的记忆与用户建模系统，可自托管或云托管。representations 来自系统推理，不能自动当作用户自述。不是完整聊天框架。
- https://hindsight.vectorize.io/ 公开 retain、recall、reflect 和托管、本地、连接自有集群选项。其 reflect 不自动等于 SayHear 对 Reflection 的产品定义。
- https://docs.mem0.ai/overview 区分托管平台与 OSS，托管文档说明审计与工作区治理。具体地区、保留、删除和价格仍需专项核实。
- https://vercel.com/docs/postgres 明确旧 Vercel Postgres 不再提供，新项目使用 Marketplace 的外部 Postgres。
- https://code.claude.com/docs/en/agent-sdk/overview 明确 Agent SDK 以库方式运行 Claude Code binary，提供内置工具、权限、会话、MCP 与 hooks。Client SDK 的 beta Tool Runner 是不同接口。第三方产品的登录与速率限制使用有独立要求，不能默认把开发订阅额度当线上产品凭据。
- https://arxiv.org/abs/2410.10813 摘要列出信息提取、多会话推理、时间推理、知识更新和拒答五类能力。只借鉴评测维度，不据摘要排列记忆产品名次。

## 获取限制

- https://openai.com/index/tolan/ 返回 HTTP 403。其实现细节只能暂按旧资料或候选复核来源中的供应商案例报告处理，不据此声明主 Agent 直接读取正文。
- Nature DOI 页面重定向到身份 cookie 页面。改用大学的论文摘要记录，摘要不充当完整论文的复核。
- OpenAI Agents JS 页面导航很长，首次提取仅含导航。第二次读取 offset 100000 后核对正文，才确认 ModelProvider 能力。

## 预算计算

2026-10-20 至 2026-12-31 含首尾共 73 天，约 10.43 周。按每周约 10 小时，理论约 104.3 小时。主计划以约 100 小时封顶规划，预留缓冲；这属于排期估算，不是已测开发工时。
