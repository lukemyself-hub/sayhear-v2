# SayHear 技术路线与产品研究依据

状态为 Draft。配套主计划在 `sayhear-build-and-learning-plan.md`。本文件解释推荐理由，不替代 CONTEXT 或后续 ADR。调研于 2026-10-20 启动，机器记录核验时间跨入 2026-10-21 UTC。网页为滚动文档，阶段启动时须再核对实际采用版本。

## 用证据区分能力与效果

官方技术文档用于确认接口、职责和限制。官方产品帮助页用于确认公开交互。供应商客户案例属于团队报告，不能证明实现路线与体验提升有因果关系。论文用于提取评测与学习方法，不把公开基准排名直接迁移到 SayHear。下文的“适合”与“不优先”均为研究判断，尚非 Luke 接受的选型。

本次未运行候选框架、实际 Provider 调用、竞品应用或产品评测。本文比较的是文档证据和与项目约束的匹配程度，不能据此报告时延、可靠率或维护工时优势。

## 先区分技术层级

模型 SDK 解决请求、流式返回与工具协议。Harness 决定一次对话怎样执行、如何选上下文、何时停止。持久编排负责跨进程的任务状态与恢复。记忆组件负责抽取、存储或召回的一部分。数据库保存产品数据。可观测与评测帮助解释执行和判断行为。这些职责可以由同一框架覆盖，也可以组合，组件之间仍须有清晰归属。

| 候选 | 文档确认的能力 | 与 SayHear 的匹配和代价 |
| --- | --- | --- |
| AI SDK | 模型集成、流式、工具调用与 ToolLoopAgent。记忆可接 Provider 工具、外部服务或自定义工具。[Agent 文档](https://ai-sdk.dev/docs/agents/overview)、[记忆文档](https://ai-sdk.dev/docs/agents/memory)。 | 适合 TypeScript Web 的较薄运行路线。产品须承担 canonical 数据、上下文政策、用户控制和持久任务，采用 SDK 不等于重写 HTTP 协议。 |
| Mastra | Agents、workflows 与多类 memory。消息历史、working memory、semantic recall、observational memory 有各自作用域，需要配置存储。[记忆文档](https://mastra.ai/docs/memory/overview)。 | 一体化程度更高，适合作为主要替代路线。必须核对框架消息和产品 canonical 的归属，Observer 与 Reflector 不能自动等于 SayHear 的 Reflection。不能只凭更薄就否定它。 |
| LangGraph JS | 低层有状态图编排、持久执行、人工介入、短期与长期记忆。LangChain 不是必需依赖。[概览](https://docs.langchain.com/oss/javascript/langgraph/overview)。 | 明确需要分支、暂停恢复和复杂状态时有价值。当前以聊天为主，先验证是否确实需要这些能力；Python 生态组件不能默认在 JS 等价可用。 |
| OpenAI Agents SDK JS | 提供 Model 和 ModelProvider 扩展接口。可给 Runner 注入自定义 Provider，模型需实现非流式和流式接口。部分能力依赖 Responses API。[模型文档](https://openai.github.io/openai-agents-js/guides/models/)。 | 不能因名称判定只支持 OpenAI。实际 Provider、流式工具和追踪适配成本仍需核对。Session 状态不等于长期记忆与用户删除机制。 |
| Claude Agent SDK | 在自有进程内运行 Claude Code binary，提供工具、权限、会话、hooks、MCP 与子 Agent。Client SDK 的 Tool Runner 是不同接口。[官方概览](https://code.claude.com/docs/en/agent-sdk/overview)。 | 适合需要现成文件和命令工具的任务 Agent。SayHear 当前不需要这套工具权限，Provider 替换与 Web 运行负担须另评估。不能把开发助手的完整工具集默认暴露给聊天用户。 |
| 自建轻量循环 | 应用自行决定模型请求、工具执行、停止和失败路径。SDK 可继续负责网络与模型协议。 | 控制直接，维护责任也集中到自己。只在现成循环无法表达已确认的产品要求时增加自己的执行逻辑。学习重点是能解释机制，不要求重新实现每层。 |
| durable-harness | 以持久会话日志和队列恢复既有 Harness。中断的模型调用会重跑，工具按重放规则处理。[Vercel 文档](https://vercel.com/docs/agent-harnesses)。 | 属于执行恢复层。可用于未来确需长回合恢复的场景，不自动解决产品数据模型、用户隔离和副作用重复。文档日期元数据异常，不用它判定发布日期或成熟年限。 |

候选 3 对 Mastra 的两条拒绝理由本次未核实，只作为待实测项保留。一是它主张 Mastra 的一体封装会隐藏 loop 细节，与 SayHear 的学习目标冲突。二是它主张 Observational Memory 的 resource scope 已标记 deprecated，跨 thread 连续性只能落到默认关闭的 semantic recall。这两条都需要在阶段 0 用同一场景对照 AI SDK 与 Mastra 时验证，不能提前当作结论。候选 3 自报的 Mastra 版本、token 阈值和压缩比同样未复核。

## 记忆与用户建模服务分别补什么

| 候选 | 公开能力 | 进入 SayHear 的条件 |
| --- | --- | --- |
| Mem0 | 托管平台与 OSS 分开。托管版管理向量存储、重排和基础设施，并描述审计与工作区治理。[概览](https://docs.mem0.ai/overview)。 | 抽取与召回的实际收益能在自有场景重现。核对选定版本的来源、更新、删除、数据地区和退出方式。OSS 与托管结果不能混用。 |
| Zep 与 Graphiti | Graphiti 是时间知识图谱框架，Zep 是相关托管产品。[Graphiti 仓库](https://github.com/getzep/graphiti)。 | 人物消歧、关系和时间问题确实成为主要失败源，图的维护成本有必要。图结构不自动证明推断可信。 |
| Letta | 将持久 Agent 状态和可编辑 memory blocks、archival memory 等结合。[记忆说明](https://docs.letta.com/configuration/memory)。 | 接受其状态运行模型，并证明自编辑记忆的来源、版本、权限和删除满足产品要求。不能当作简单向量插件接入。 |
| Honcho | 开源或云托管的记忆与用户建模系统，从消息推理 peer representations。[官方文档](https://honcho.dev/docs/)。 | 值得在画像阶段比较。它的推理结论须保持 AI 观察身份，不能冒充用户表达。当前文档概览不足以确认所有保留和删除细节。 |
| Hindsight | 提供 retain、recall、reflect，可选托管、本地或自有集群。[官方文档](https://hindsight.vectorize.io/)。 | 适合作为记忆与推理组合候选。组件中的 reflect 与产品 Reflection 必须逐项对齐，不能因名称相似就认定职责相同。 |
| 产品自有基础记忆 | 从 canonical 数据构造有限历史、少量有来源的跨日可用内容。检索可从简单策略开始。 | 适合建立最先可解释的基线。并非承诺全部自研，也不是先否定服务；当失败案例证明组件能减少实际工作时替换派生层。 |

原始消息与 AI 产物应有清楚归属，任何框架的存储只能在职责明确时成为相应数据的权威来源。允许框架拥有运行日志或派生索引，但应能说明如何导出、删除、恢复与重建。具体结构在 canonical 阶段决定，不提前规定事实表、图谱、Bio 或七个内部接口。

## 配套服务按需要引入

| 领域 | 候选与事实 | 建议边界 |
| --- | --- | --- |
| 数据库 | Supabase 提供完整 Postgres，集成 Auth 和 RLS，备份能力受套餐影响。[数据库概览](https://supabase.com/docs/guides/database/overview)。Neon 是另一托管 Postgres 候选。Vercel 新项目通过 Marketplace 接外部 Postgres。[Vercel 文档](https://vercel.com/docs/postgres)。 | 推荐关系型 canonical 存储，Supabase 与 Neon 留作首阶段具体比较。两个独立实例隔离测试与真实库；不能默认用复制私人生产数据的分支充当测试集。pgvector 按召回需要添加。 |
| 后台执行 | Vercel Queues 当前文档标 Beta、至少一次投递，可重试。Workflows 是更高层耐久步骤。[Queues](https://vercel.com/docs/queues)、[Workflow SDK](https://workflow-sdk.dev/)。Inngest 提供耐久后台工作流、重试与调度。[文档](https://www.inngest.com/docs)。 | Reflection 先证明输入、产物和作用，再决定自动化。真正后台任务必须离开浏览器和开发电脑仍可运行，不能启动请求后放任无托管 Promise。重复任务不得重复写有效产物。 |
| 可观测与评测 | Langfuse 提供 traces、数据集与评测，支持 SDK、OpenTelemetry 等接入。[文档](https://langfuse.com/docs)。LangSmith 和框架自带 tracing 也可比较。 | 产品内运行详情优先。外部遥测默认只传必要元数据，原始私人内容是否发送、存哪、保留多久需明确决定。供应商默认配置不可视为符合产品边界。 |
| 工具与插件 | 各框架可能支持自定义工具、MCP 或插件。 | 初期只纳入服务体验或验证 Harness 机制的少量工具。MCP 是连接协议，不自动给出权限和数据边界；不为了“Agent 化”堆工具。 |

## 旧材料怎样使用

用户提供的五份资料均已读取。两份 companion 研究是同一议题的长短版本，不能当成独立重复证据。旧文中的 v1 ADR、schema、检索上限和发布方式不构成 v2 前提。

| 旧资料 | 主要带走的经验 | 需要重新评估的内容 |
| --- | --- | --- |
| `SayHear 开发思考笔记.html` | 买入成熟机制也要持有产品语义；比较退出成本；先定验证问题与决策规则。 | Mastra 推荐、固定接口数、工时收益阈值和基准排名均为旧语境。不能当作已测事实。 |
| `ai-companion-warmth-curiosity-continuity.md` | 人格要兼具温暖与独立判断，连续性影响信任。 | “现有架构无需改”只针对旧系统；Pi 记忆界面描述与短版冲突。 |
| `companion-warmth-curiosity-continuity-research.md` | 追问、非人身份和关系边界需要产品验收。 | 对年龄、主动消息和记忆控制的旧决定不能默认继承。 |
| `memory-recall-companion-ux.md` | 召回应自然，来源按需展开；删除对话与删除记忆可能不是一回事。 | v1 不做编辑器与 v2 用户控制方向不同；“未找到”不等于不存在。 |
| `memory-systems-engineering-practice.md` | 抽取、检索、上下文注入和回答分开定位；评测覆盖时间变化、更新与拒答。 | 各厂商基准配置不同；短历史与长历史结论不能外推到所有场景。 |

完整旧资料调查保留在本次 `.audit` 记录，工程计划只保留直接影响路线的结论。引用旧研究时区分原文报告、推断和当前官方核对结果。

原始参考文件如下。

- [开发思考笔记](</Users/lukemyself/Downloads/SayHear 开发思考笔记.html>)。
- [温暖、好奇与连续性长版](/Users/lukemyself/Projects/SayHear/docs/research/ai-companion-warmth-curiosity-continuity.md)。
- [温暖、好奇与连续性短版](/Users/lukemyself/Projects/SayHear/docs/research/companion-warmth-curiosity-continuity-research.md)。
- [记忆召回体验研究](/Users/lukemyself/Projects/SayHear/docs/research/memory-recall-companion-ux.md)。
- [记忆系统工程实践](/Users/lukemyself/Projects/SayHear/docs/research/memory-systems-engineering-practice.md)。

这些绝对路径用于当前本地工作区溯源，其他机器需要重新定位，不把私人下载文件复制进仓库。

## 旧 Portal 复用的实际边界

调查对象为旧仓库 `/Users/lukemyself/Projects/SayHear`。聊天位于 `apps/web/app/internal/`，使用 Next.js App Router 与 React。展示和部分纯逻辑可以复用，容器依赖旧 NDJSON 事件、Daily Session、鉴权闸门及 Inspector 深链，外壳还含 Journal 入口。

因此，推荐保留布局、消息呈现、输入与流式反馈、响应式和无障碍交互，按 v2 契约适配容器。会话与日期导航是产品体验问题，不因实现方便直接删掉。旧 Journal 和整套运行详情不随聊天 UI 自动迁入。

这里没有运行浏览器对比。工作量只能估算，不能宣称迁移已验证或“原样复制就能用”。主计划在首个基础闭环中为适配和验证留预算。

## 产品和市场研究的证据边界

Pi 的公开定位强调倾听、好奇和承认不确定。[官方介绍](https://inflection.ai/blog/pi)。它启发 SayHear 的回应方式，不能证明某种 prompt 可复制其体验。

Nomi 的 Mind Map 公开提供记忆图谱、表格、编辑和新增，并按聊天房间区分。[官方更新](https://nomi.ai/updates/mind-map-2-0-bringing-nomi-memory-into-view/)。这说明记忆控制可以成为用户界面的一部分，不能直接推出其删除完整性或 SayHear 应采用关系产品的定位。

Tolan 的上下文重建、召回与夜间整合经验来自供应商案例及旧材料。主 Agent 访问 [OpenAI 案例](https://openai.com/index/tolan/) 返回 403，因此这里只按团队公开报告处理，不复述效果数字作为选型证据。

Character.AI 公开 Story Memory、自动 Facts、pin、编辑与关闭部分记忆，以及记忆使用视图。[官方更新](https://blog.character.ai/memory/)。可借鉴显式内容和自动派生内容分开呈现，但角色扮演与关系产品的目标不构成 SayHear 的目标。

Rosebud 公开 AI 回应日记、回顾与模式洞察，整体偏自我反思和目标推进。[官网](https://www.rosebud.app/)。它是长期记录的邻近产品参考。SayHear 仍以未经整理的表达和倾听为入口，不因竞品功能变成训练用户的教练。Day One 的 [AI 功能说明](https://dayoneapp.com/guides/ai-features/ai-features/) 区分日记静态 E2EE 与 AI 请求时在设备解密并经 HTTPS 发送的处理过程。这提醒未来日记阶段准确解释内容去向，不能把传输加密称为全流程 E2EE。

这些参照足以说明公开产品形态，却不构成市场规模、付费意愿或用户需求验证。本次没有进行用户访谈、商业收入审计或竞品实机体验。产品适配是基于 Luke 明确需求与公开材料的判断，后续真实用户扩展前仍需验证其他用户是否有同样需求。

## 市场判断与需求风险

当前最明确的目标用户是 Luke，需求依据来自已接受的 CONTEXT 和 v1 使用教训。未来目标人群可假设为希望表达零散经历、重视被理解与跨日连续性、愿意长期保存个人内容的人。这仍是待验证人群定义，不能据现有公开产品材料推导市场规模或付费意愿。

替代选择包括通用聊天产品的历史与记忆、Pi 类倾听产品、Nomi 或 Character.AI 类角色陪伴、Rosebud 类 AI 日记，以及 Day One 类私人日记。SayHear 推荐差异是自由表达入口、非浪漫且有判断的回应、可信连续记忆与可追溯生活记录的组合。公开竞品已经分别覆盖其中多项，因此差异是否足以让用户持续使用仍是未知，不能宣称市场空白。

主要需求风险是用户未必愿意把足量私人内容交给新产品，精准召回未必自然，自动画像可能造成被监视感，而记录和整理本身也可能增加负担。年底先验证 Luke 是否愿意继续日常使用、哪些记忆真正减少重讲、哪些提起令人不适。邀请其他用户前再以访谈和有限试用检验这些需求是否具有可迁移性，并重新确认年龄、地区、价格和数据承诺。这个顺序满足当前受控重建的学习目标，但不构成商业机会验证。

## 学习与评测参考

[LongMemEval](https://arxiv.org/abs/2410.10813) 的摘要列出信息提取、多会话推理、时间推理、知识更新和拒答。可借这些维度组织 SayHear 的合成历史，另加归属错误、用户推断区分、自然提起与敏感内容边界。公开问答基准不能替代陪伴体验评测。

Carpenter、Pan、Butler 的 2022 年综述支持间隔学习和提取练习。[大学摘要记录](https://profiles.wustl.edu/en/publications/the-science-of-effective-learning-with-spacing-and-retrieval-prac/)。本次核对了摘要，Nature 正文重定向，未据此声称读过全文。对 SayHear 的应用是隔几天回到同一条真实运行，由 Luke 解释和判断，再用运行证据校对。这是教学设计建议，不保证掌握速度，也不采用考试形式。
