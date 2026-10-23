# SayHear v2 阶段级技术、功能搭建与学习路线

研究截点：2026-10-20。性质：候选计划，供 Luke 讨论，不是迁移批准、实现方案或验收承诺。网页功能、开源状态和套餐可能变化；选择前须按拟采用版本重查。

## 结论状态

### 已定

- SayHear v2 是为真实日常使用而受控重建的多用户 Agent 产品，学习、可理解性和用户体验都是目标。2026 年底的阶段目标是可日常使用的文本 Agent，包含基本 Harness、canonical 对话数据、稳定人格、基础记忆与 Reflection、运行详情、真实行为验证数据集和 Vercel Web 聊天。[项目共识](file:///Users/lukemyself/Projects/SayHear-v2/CONTEXT.md)
- 从基础对话与 canonical 数据逐步扩展，不在本年承诺日记、完整纠错遗忘、Open Loop、实时语音或完整多用户系统。初期数据归属和访问设计须兼容未来多用户。[项目共识](file:///Users/lukemyself/Projects/SayHear-v2/CONTEXT.md)
- 运行目标为 Vercel 上可独立于开发电脑工作的 Web 应用。Provider 可替换，需说明能力、输出与时延差异；聊天 UI 复用旧 Portal 的布局、消息、输入、流式反馈与响应式适配。[项目共识](file:///Users/lukemyself/Projects/SayHear-v2/CONTEXT.md)
- Luke 每周约十小时，包含讨论、阅读、体验、讲解和笔记。阶段验收同时看代码行为、实际体验与理解能力。[项目共识](file:///Users/lukemyself/Projects/SayHear-v2/CONTEXT.md)
- 不因研究材料或本候选计划改产品边界。产品定位、隐私与关键体验发生变化时另行讨论。

### 推荐

- 先搭一条窄而真实的端到端文本对话路径，再纵向交付记忆与 Reflection。每阶段先冻结用户体验目标和验收，再搭机制；以小型合成案例和有限、获准的真实模型样本验证。不要把“框架安装成功”“benchmark 高分”或类型检查通过当作产品效果证据。
- 工程选择先按层级分类：模型 SDK 与对话循环、持久编排/任务运行层、Memory 数据与检索层、数据库/托管平台、可观测与评测层。它们不是彼此等价的整套替代品。
- 开发者保有用户原始消息、产品语义、访问控制和删除责任。允许组件拥有可重建索引或运行状态，但须证明其职责明确且可退出。
- 评测首选 SayHear 自己的中文/英文合成对话、失败例、人工盲评和运行轨迹。论文基准用于挑出值得测的能力和补充工程冒烟，不用来宣判产品胜负。
- 学习采用短解释、看真实运行、随后间隔一段时间由 Luke 沿请求路径复述或预测，最后做一个真实小改动并观察。让学习嵌入需求，不以课时和做题数量作为掌握证明。

### 待讨论

- 第一阶段体验边界、部署访问控制是否只限 Luke、聊天保留与数据提供商范围。
- 是否选一项主要 TypeScript agent/工作流方案做小型替代性验证；是否保留手写薄循环作为可理解基线。
- 初期 PostgreSQL 提供商、备份与恢复目标、数据库区域及成本上限。
- 基础记忆的含义和输入范围，何时才值得做跨日持久记忆与 Reflection。
- Provider 首选测试矩阵、每月模型预算、需在生产日志中保留的最少数据。
- “可日常使用”的 Luke 验收标准及周投入波动时的年底范围缩减顺序。

### 待实测

- 候选 Harness 在当前应用、TypeScript 代码和目标 Provider 上是否降低维护工作，同时能否取消、报错、流式显示并把每次运行查清楚。
- 真实中文私密日常对话中，哪些记忆召回改善连续性，哪些会显得突兀、错误或像监视。
- 基础记忆工具的抽取、更新、删除和跨日召回是否可靠，是否需要额外 Memory 产品。
- 各托管 Postgres 的部署和恢复体验，以及真实使用下的成本和时延。本文未核实当前套餐的完整价格。
- Luke 是否能不看提示解释一条对话的上下文构成、一次调用的失败层和记忆证据来源。学习证据是解释和操作表现，不是读完资料。

## 分层比较与关键取舍

### 对话循环和模型 SDK

| 候选 | 官方可核实能力 | 对 SayHear 的位置与限制 |
| --- | --- | --- |
| Vercel AI SDK | 提供文本生成、流式和工具调用/agent 循环原语。其官方 Memory 页面把选择分为模型提供商定义的工具、Memory provider 和自定义工具。前两者较省接入，但控制权较少或绑定提供商；自定义工具更灵活，也要多写应用逻辑。[Agents](https://ai-sdk.dev/docs/agents/overview), [Memory](https://ai-sdk.dev/docs/agents/memory), [Tools](https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling) | 适合作为 Web 产品侧 TypeScript 原语候选，不等于完整持久工作流、用户数据模型或统一记忆治理。不要因其有 streaming 就假定离线任务重启后自动续跑。必要时以 Workflow 等独立运行层承担耐久任务。 |
| OpenAI Agents SDK (JS) | Agent、tools/handoffs、sessions、tracing、testing 均有官方文档；模型文档暴露 Model 与 ModelProvider 扩展接口。[Sessions](https://openai.github.io/openai-agents-js/guides/sessions/), [Tracing](https://openai.github.io/openai-agents-js/guides/tracing/), [Models](https://openai.github.io/openai-agents-js/guides/models/), [Testing](https://openai.github.io/openai-agents-js/guides/testing/) | 是有明晰工具循环和追踪的 SDK，不因名字等于只能调用 OpenAI 模型；自定义 provider 能力须针对具体适配器验证。Sessions 属于对话状态能力，不应当作 SayHear 的长期记忆与删除合同。 |
| Claude Agent SDK | 官方 Agent SDK 支持 TypeScript 和 Python；Claude API 的工具使用、会话/消息能力及 SDK 配置须区分于 Claude Code CLI 的本地开发代理。可研究其托管工具和运行行为，但 Agent SDK 的模型调用以 Anthropic 为核心。[Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview), [TypeScript SDK](https://platform.claude.com/docs/en/agent-sdk/typescript) | 适合评估 Claude 专属部署或 Anthropic 能力深度，不是满足 Provider 可替换目标的默认中心。不要把开发期 Claude Code 的文件/shell代理体验推导为线上产品合适。任务范围需限在文本对话所需工具。 |
| 自建轻量循环 | 可把一次模型请求、工具执行、停止条件、取消、异常和流输出写成可读的应用代码；Anthropic 工程指南建议按任务需要选择简单流程或 agentic loop，而非默认叠加框架。[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | 最容易理解与控制，但要承担 provider 协议差异、工具调用边界、取消、重试、超时、持久化和观测。只适合当阶段一的小基线；只有真实复杂度很低时保留，不把“循环只有几十行”当总维护量。 |

### 持久编排与运行平台

| 候选 | 官方可核实能力 | 对 SayHear 的位置与限制 |
| --- | --- | --- |
| LangGraph JS | 图节点状态、checkpointer 和 thread ID 可保存并恢复执行；官方示例覆盖中断后继续。[Thinking in LangGraph](https://docs.langchain.com/oss/javascript/langgraph/thinking-in-langgraph) | 是可持久执行的图运行框架，和单纯模型 SDK 不同。当前需比较 JS 生态的目标功能、接入和读写负担，不用 Python LangMem 文档推断 JS 同样可用。大图与状态协议仅在有多步骤、恢复需求时值得引入。 |
| Mastra | TypeScript 框架包含 agents/workflows；Memory 文档列出 history、working memory、semantic recall 和 observational memory。Observational Memory 由后台 Observer/Reflector 压缩旧对话；存储 provider 是前提，默认有 thread/resource 作用域约定。[Memory](https://mastra.ai/docs/memory/overview), [Workflows](https://mastra.ai/docs/workflows/overview), [Observability](https://mastra.ai/docs/observability/overview) | 覆盖面较一体，可能减少接线；同时可能与自有上下文、消息、反思工作重叠。其记忆能力不等于通过 SayHear 的中文事实归属、删除或用户控制验收。厂商评测数字不作路线证据。 |
| Vercel Workflow / Queues | Workflow 支持耐久步骤；Queues 当前官方文档称 beta、至少一次投递、失败重试、延迟投递与幂等键。消费者可由 Vercel 推送，也可外部 worker 拉取。[Workflow](https://vercel.com/docs/workflow), [Queues](https://vercel.com/docs/queues) | 这是耐久任务/消息平台，不是聊天 agent SDK 或记忆系统。至少一次投递意味着任务动作要幂等；队列的消息保留和期限要核对需求。只在 Reflection 或其他离线工作确实要跨重启恢复时引入。 |

### 记忆系统和产品

| 候选 | 官方可核实能力 | 对 SayHear 的位置与限制 |
| --- | --- | --- |
| Mem0 | 官方 OSS 文档与托管 Platform 文档分开；API 有 add/search 及 update/delete 等操作，另有上下文记忆提取方式。[OSS operations](https://github.com/mem0ai/mem0/tree/main/docs/core-concepts/memory-operations), [Platform operations](https://github.com/mem0ai/mem0/tree/main/docs/platform) | OSS 与托管平台的算法、能力、数据控制和价格不可混称。显式 delete API 不证明派生总结、异步处理和应用删除完整性。适合作为事实抽取/检索候选实测，不预设为长期记忆真源。 |
| Zep / Graphiti | Graphiti 是开源时间知识图谱框架，可摄入文本/JSON episodes、更新图，并混合使用语义、关键词和图搜索。[Graphiti docs](https://help.getzep.com/graphiti/getting-started/welcome), [Graphiti repo](https://github.com/getzep/graphiti) | 可能适合人物关系和时间变化问题；比简单向量检索增加图数据库、实体消歧和维护路径。图谱不自动解决 SayHear 的证据资格、纠错与遗忘合同。托管 Zep 产品和开源 Graphiti 必须分层评估。 |
| Letta | 官方文档说明 agent 的持久 memory blocks，可读写并可共享；另有 archival memory；sleep-time/Dreaming 可在交互间安排后台记忆更新。[Blocks](https://docs.letta.com/v1-sdk/memory/memory-blocks), [Memory](https://docs.letta.com/configuration/memory), [Stateful agents](https://docs.letta.com/v1-sdk/concepts/stateful-agents) | 是持久 agent/runtime 与记忆机制结合的方案，不是轻型记忆 API。Agent 自行编辑持久块与 SayHear 需保留清晰证据和用户控制的目标存在张力；若测试，应单独验权限、版本、删除和模型/provider 适配。 |
| 自有 PostgreSQL + 可选 pgvector | Vercel 明确不再提供 Vercel Postgres，新项目从 Marketplace 接入 Neon、Supabase 等外部 Postgres。Supabase 官方列出 pgvector 和备份/PITR 文档。[Vercel Postgres](https://vercel.com/docs/postgres), [Neon on Vercel](https://vercel.com/marketplace/neon), [Supabase database](https://supabase.com/docs/guides/database/overview), [Supabase backups](https://supabase.com/docs/guides/platform/backups) | 推荐持有原始会话和产品权限语义；先选一项托管服务并实测恢复。向量检索是可加的派生能力，不因选择 Postgres 就必须引入 pgvector。备份、地区、保留和厂商条款在上线前核对。 |

### 可观测和评测

| 平台 | 层级和可核实能力 | 限制及建议 |
| --- | --- | --- |
| Mastra Observability | 同框架 trace 可查 agent、workflow、tool 与模型步骤。[Docs](https://mastra.ai/docs/observability/overview) | 与 Mastra 集成紧密；需确认数据脱敏、存储和保留，不把 trace 存档当产品评测。 |
| OpenAI Agents tracing | SDK 记录 agent 执行轨迹；配套 testing 文档支持测试 agent 行为。[Tracing](https://openai.github.io/openai-agents-js/guides/tracing/), [Testing](https://openai.github.io/openai-agents-js/guides/testing/) | Provider/SDK 运行轨迹是工程检查证据。需核实当前 tracing 后端和脱敏开关；私人对话不能未经政策确认上传。 |
| LangSmith | 追踪与评测工具，含在线 LLM-as-judge 文档。[Online evaluations](https://docs.langchain.com/langsmith/online-evaluations-llm-as-judge) | 是独立评测/可观测产品层，不要求 LangGraph 才能理解其价值；自动 judge 是有误差的辅助判断。 |
| Vercel Observability | 平台运行日志和指标；Vercel Workflow/Queues 相关任务状态可查。[Observability](https://vercel.com/docs/observability), [Queues](https://vercel.com/docs/queues) | 更适合部署/运行层诊断，不代表能判断“被理解感”或记忆是否恰当。 |
| 自有小型回放与人工盲评 | 用匿名合成案例对比版本；按召回、越界引用、纠错/删除、人格一致性、语气和时延分类记录。外部论文可提供评测维度而非本产品结论。[LongMemEval](https://arxiv.org/abs/2410.10813), [MemoryAgentBench](https://arxiv.org/abs/2507.05257) | 推荐作为阶段主要用户体验证据。每次报告样本数、失败例、模型/提示/配置；小样本不能推导长期可靠率。外部基准数据不含 SayHear 的信任边界。 |

## 产品经验与学习依据

### 产品参考

- Pi 官方强调倾听、好奇、谦逊和承认不知道；官方 Crisis Protocol 还有风险回应说明。[Pi](https://inflection.ai/blog/pi), [Crisis protocol](https://inflection.ai/crisis-prevention-and-safety)
- Tolan 的官方博客把好奇指向用户生活，OpenAI 案例由 Portola 团队说明每轮重建上下文、检索记忆和夜间压缩。案例中的召回 miss、留存等数字是供应商发布的团队自述，不是独立实验；官网“帮助用户”的数字是营销陈述，不能当疗效证据。[Tolan design](https://www.tolans.com/relay/introducing-tolan), [OpenAI case study](https://openai.com/index/tolan/)
- Character.AI、Nomi 和 Kindroid 的官方页面展示记忆可见性控制、编辑或 pin 的不同做法，但它们产品定位和承诺不等于 SayHear 应照搬。竞品功能文档只证明公开功能存在，不证明使用效果。[Character.AI memory](https://blog.character.ai/memory/), [Nomi Mind Map](https://nomi.ai/updates/mind-map-2-0-bringing-nomi-memory-into-view/), [Kindroid memory](https://kindroid.ai/v2/docs/memory/)
- 旧资料提示公开 companion 产品行为研究薄弱，成熟产品帮助页和营销演示主要是意图证据，不是行为质量研究。关系产品的依赖风险、危机、安全细节不能凭品牌声称作结论。优先保留与 SayHear 边界一致的“温暖但诚实、向外好奇、非人类身份清楚、记忆可解释”的待测原则。[旧研究目录](file:///Users/lukemyself/Projects/SayHear/docs/research/)

### 学习证据与操作

- Dunlosky 等综述将练习测试（主动回忆）和分散练习列为高效用；自我解释等证据较有限。设计上，用阶段后的间隔复述与实际操作替代一次性读完或泛泛问“懂了吗”。[Review](https://www.psychologicalscience.org/journals/pspi/1529100612453266/)
- 2022 年综述讨论间隔与提取练习在不同年龄和材料中的效果；这支持间隔复习作为一般方法，不证明某个 SayHear 教学流程或每周时数有固定效果。[Review](https://www.nature.com/articles/s44159-022-00089-1)
- 对初学者先看带标注的运行/代码例子，再解释其中一段因果，再修改一处并观察结果；对编程 worked example 的直接研究存在，但不能把一般心理学研究等同于特定技术项目效果。[Programming worked examples](https://doi.org/10.1145/3605098.3636007)
- 每阶段设置一个“回看运行证据、闭卷讲出调用路径、实际做一个小改动”的循环。对关键术语讲错时回到当前代码或运行轨迹，而不是增加背诵任务。操作卡片不要求 Luke 看课时或做考试。
- 让 Luke 选择有意义的产品问题，并让 Agent 处理重复查资料、生成匿名合成案例和整理笔记；关键设计和体验由 Luke 参与，符合项目共识。

## 阶段候选路线

时数是阶段范围，不是必须耗尽的工时。年底截至 2026-12-31 约十周，按每周十小时约一百小时总预算。讨论、阅读、调试、体验和笔记都计入 Luke 的时数；后台 Agent 工作不计。至少保留总预算约 15 小时的缓冲，计划目标约 85 小时。

| 阶段 | 建议投入 | 用户目标与功能规格边界 | 验收证据 | 学习证据 |
| --- | ---: | --- | --- | --- |
| 0. 产品边界与运行路线决策 | 6 小时 | 确定文本聊天最小的日常使用情境、部署访问方式、数据流边界和候选方案。此阶段产物为讨论过的阶段 SPEC，不画 schema、不定 PR 清单。 | 体验目标、范围内/外、已定/未定问题、运行和数据路径清楚；候选项各自有可证伪理由。 | Luke 能区分模型 SDK、持久工作流、数据库、Memory 服务和部署平台，并说明选择依据。 |
| 1. 部署可用的基础文本对话 | 20 小时 | Vercel Web 聊天；旧 Portal 关键布局和输入/流反馈；一条 Provider 路径；停止/取消、错误态、重试策略；对话保存和再次打开。 | Luke 可在开发电脑离线时使用部署版；刷新后历史仍可读；流错误、取消和 Provider 故障可被用户识别，数据只属于预期用户。至少走一轮真实模型手动体验。 | 沿一次请求解释浏览器到模型和响应流的路径；指出超时或失败发生层。改一个可见交互并确认。 |
| 2. 基础 Harness 与运行详情 | 14 小时 | 明确工具是否属于年内必需范围；如需工具，限一个低风险只读或确定性工具。运行详情让开发者可看到模型、提示版本、上下文来源、步骤、结束原因和错误。设计日志最小化。 | 取消不会再追加陈旧响应；失败能定位调用阶段；运行详情不泄露跨用户内容，不把内部推理作为产品承诺；Provider 改动有基本对照。 | Luke 能解释一次消息的上下文来源与工具边界；用真实错误日志定位一次故障。 |
| 3. 人格和连续对话质量 | 11 小时 | 稳定的非人类人格、倾听优先、好奇且不过度追问、不迎合事实错误。保持当前 Session 连续性；暂不承诺跨日画像。 | 小型案例覆盖问候、情绪表达、直接任务、未知事实、拒绝建议、风险边界；Luke 盲评或逐例判定核心语气，保留失败样本。 | Luke 能指出人格/安全指令分别由哪层控制，并从相同输入比较行为变化。 |
| 4. Canonical 对话与基础跨日记忆 | 17 小时 | 保存原始消息并构造有限历史上下文；明确系统摘要是压缩产物还是记忆事实；从最小合成用户史测试跨会话回忆。建立只属于产品的来源链和删除预期。 | 精确事实、时间变化、相似词改写和“无证据时承认不知道”样例可查；不会把 AI 总结伪装成用户原话。纠正/删除当前处置范围须在 SPEC 里明确，不作完整用户编辑器承诺。 | Luke 能对一个回答分辨原始陈述、摘要与推断，并追踪该回忆来自何处。 |
| 5. Reflection 小闭环 | 10 小时 | 只对合成/明确允许的数据进行一项跨日总结；注明生成时间、输入范围和失败状态。是否用后台 Workflow 取决于部署恢复需要。Reflection 不自动扩张为 Open Loop 或对话外跟进。 | 固定多日样例产物忠实、明显遗漏可见，失败不会破坏对话；同一批输入重跑结果可比较；说明调用成本、延时和后台失败位置。 | Luke 能解释快请求与后台总结区别，说明摘要的限度，并判断何时重跑。 |
| 6. 体验收敛、验收和年底封存 | 7 小时 | 完成错误态、响应式检查、基本账户隔离和部署说明；记录年底后优先项及缺口。先问还有什么会让 Luke 下周继续用，再删低价值功能。 | 端到端日常使用演示；记录失效/清除测试、线上模型冒烟、语言体验、至少一轮回归案例；阶段文档标明未通过事项。 | Luke 独立讲解整体请求、保存、记忆构造和失败排查，指出三个可观察的不确定处。 |
| 弹性与复测缓冲 | 15 小时 | 吸收方案验证低估、模型故障、部署问题、恢复与体验修正。若未用完，留作年底验收和连续记忆缺陷修复，不新增范围。 | 预算燃尽情况、剩余缺陷与缩减决定有记录；未达到的阶段目标明确延期，不假装交付。 | 回头重讲阶段 1 与 4 的架构，不看笔记，之后再通过运行核对。 |

**总计计划 85 小时，另留 15 小时不预分配。** 如果一周只能投入五小时，优先保住阶段 1 的部署对话、阶段 3 的人格体验和阶段 4 的基础跨日记忆。先推迟 Reflection，再缩减运行详情，最后才增加后台复杂度。若基础聊天的失败体验和数据隔离没有过关，取消年内 Reflection 范围。

## 拒绝或暂不优先的替代方案

- **直接迁移到 OpenClaw 式个人 Agent。** 个人助理的文件和信任模型不直接给出消费级多用户 Web 的访问隔离；个人演示观感也不能证明长期体验、数据删除和部署可靠性。可借鉴其易读人格与记忆文本，但不将其作为生产底座。OpenClaw 官方安全页强调一个 Gateway 是信任边界。[Security](https://docs.openclaw.ai/gateway/security)
- **直接全量采用 Mastra，启用所有 Memory 与 Observer/Reflector。** Mastra 有多类内置 Memory，但会将多个还未定义的 SayHear 语义一起带入；如果不逐项验证便接上，可能与自有上下文及后台任务重复。保留作需有明确退出条件的运行层挑战者。
- **把 LangGraph 当普通 SDK 或默认使用 LangMem。** LangGraph 的优势是可恢复图执行，适合确有分支、暂停或恢复的流程；LangMem 的说明和生态不能推导出 TS 与 Python 能力完全相同。未有该复杂度前，读写路径和图状态会增加学习面。
- **用 Claude Agent SDK 做默认多 Provider 主路径。** 其价值是 Anthropic agent 能力；项目明确要求容易替换 Provider。除非特定用户体验证据证明 Anthropic 专属能力值得绑定，否则不做首选。
- **把 OpenAI Agents SDK 排除为“绑定 OpenAI”。** 官方 JS 文档提供 ModelProvider 抽象，所以旧笔记这一理由太强。仍不等于每个 Provider 都无差异，也不等于 SDK 本身给长期记忆。作为有 tracing/testing 文档的候选比较，不预设入选。
- **一开始就部署 Mem0、Graphiti/Zep、Letta 多个记忆系统。** 这些工具代表不同层级和存储语义。多个并行系统会使一个人难以知道哪层影响回答，且会引入同步与删除责任。到阶段 4 出现具体失败，再选一项挑战现状。
- **把图谱、向量检索或复杂 reranker 当记忆质量保证。** 它们改善特定检索路径，不能裁定证据资格、说话者、时间状态和用户是否愿意听到旧事。先建立能重现的失败案例。
- **用厂商“记忆准确率”、自报 benchmark、次日留存和营销疗效数字当选型结论。** OpenAI Tolan 案例是团队自述，不是独立对照；框架文档里的效果数也只说明厂商在特定配置下的报告。配置和题集会改变结果。
- **用 Replika/Nomi 等关系升级、离线主动消息或 streak 作为留存优化。** 这与当前愿景中不经营浪漫/排他关系、不因中断施压的产品边界冲突。[项目共识](file:///Users/lukemyself/Projects/SayHear-v2/CONTEXT.md)

## 重要事实的来源与能力限制

- AI SDK 是工具循环与模型集成原语，并列出多个记忆接入形态；其“可接入”不代表产品级用户控制已解决。[AI SDK agents](https://ai-sdk.dev/docs/agents/overview), [AI SDK memory](https://ai-sdk.dev/docs/agents/memory)
- LangGraph 官方 JS 教程展示 checkpointer 和 thread ID 恢复；教程不证明其在 SayHear 部署、TypeScript 学习或成本上优于其他选项。[LangGraph JS](https://docs.langchain.com/oss/javascript/langgraph/thinking-in-langgraph)
- Mastra 官方记忆页描述 history、working memory、semantic recall 和 observational memory；这些是产品声明的功能，不是本产品中文对话的质量结果。[Mastra memory](https://mastra.ai/docs/memory/overview)
- OpenAI Agents SDK 官方 JS 文档有 sessions、tracing、models 和 testing；这些名称不是永久记忆或跨用户访问控制的完整承诺。[SDK docs](https://openai.github.io/openai-agents-js/)
- Claude Agent SDK 官方文档属于 Anthropic 平台；线上能力与 Claude Code 交互式 CLI 的可用工具集合不能混淆。[Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
- Graphiti 自述为时间图和混合检索；无需用 Zep 厂商 benchmark 推导图结构必然优于 Postgres/FTS。[Graphiti](https://help.getzep.com/graphiti/getting-started/welcome)
- Letta 文档中的可编辑共享 memory block、archival memory 和后台 dreaming 是可用机制；自编辑块如何满足 SayHear 的证据和删除规范仍未知。[Letta](https://docs.letta.com/configuration/memory)
- Mem0 OSS 和 Platform 文档是不同部署选项；抽取、update/delete API 的存在不等于删除已覆盖缓存、异步派生和备份。[OSS docs](https://github.com/mem0ai/mem0/tree/main/docs), [Platform docs](https://docs.mem0.ai/platform/quickstart)
- Vercel Postgres 是外部托管 Postgres 接入，不是当前 Vercel 自营数据库产品；官方说明新用户应从 Marketplace 选择提供商。[Vercel Postgres](https://vercel.com/docs/postgres)
- Vercel Queues 文档说明至少一次投递、重试和 beta 状态；这要求消费端处理重复执行，且发布前应核对当前限制。[Queues](https://vercel.com/docs/queues)
- Pi、Tolan、Nomi、Kindroid 和 Character.AI 官方页面能证明公开产品定位与文档化交互，不证明陪伴感或长期记忆的因果效果。[Pi](https://inflection.ai/blog/pi), [Tolan](https://www.tolans.com/relay/introducing-tolan), [Character.AI](https://blog.character.ai/memory/), [Nomi](https://nomi.ai/updates/mind-map-2-0-bringing-nomi-memory-into-view/), [Kindroid](https://kindroid.ai/v2/docs/memory/)
- 练习测试和分散练习在跨领域综述中获得较强支持；该证据指导学习结构，不能保证个人掌握速度，也不规定必须的间隔天数。[Dunlosky et al.](https://www.psychologicalscience.org/journals/pspi/1529100612453266/), [Carpenter et al.](https://www.nature.com/articles/s44159-022-00089-1)
- LongMemEval 涵盖跨会话、时间、知识更新和拒答；MemoryAgentBench 纳入遗忘等任务。这些是研究基准，不覆盖 SayHear 对隐私、可解释和“何时自然提起”的完整验收。[LongMemEval](https://arxiv.org/abs/2410.10813), [MemoryAgentBench](https://arxiv.org/abs/2507.05257)

## 重要取舍

1. 用“先证明一条路径有用，再扩大记忆能力”处理十周、一人每周十小时的现实约束；这样避免并行学多个框架和服务，却无法判断真实收益。
2. 保留多 Provider 能力为产品需求，但不为了理论可替换而在第一阶段实现所有厂商；先定义一个实际对照点，之后再验证第二个适配器。
3. 优先由 PostgreSQL 保存产品自己的对话状态，托管平台负责数据库运维；代价是自己定义消息和来源的语义，收益是能说明数据从哪来和怎样删除。
4. 持久任务与用户可见回复分开。后台重试不应制造未请求的用户消息，也不能写回已失效数据；只有真实可靠性要求出现才加 Workflow/Queue。
5. 产品温暖与记忆技术分别验收。一个记忆系统能检索到事实，不证明它该在此刻说出来；一次语气盲评高分也不能抵消事实错误。
6. 今年的学习目标是解释并运行基础 Harness 和记忆路径，不是全面掌握所有 Agent framework。未选技术先形成比较边界和后续可验证问题。

## 待确认项

- 阶段 1 是否部署成仅 Luke 访问的线上产品，还是需要早期邀请另一位真实用户。后者会提高认证、授权和隐私验收成本。
- 是否要求第一阶段允许切换两个 Provider，还是先构造单一 Provider，随后用一个低风险端到端任务验证切换。
- Memory 的第一条跨日体验应该是什么。建议选低敏感、可验证的普通生活事实，不用健康事件或脆弱情绪作首次质量实验。
- 是否把成本与真实调用样本设硬上限，以及由谁保管线上 Provider key 和数据库恢复凭据。
- 产品记忆纠正/删除功能虽不在年底完整目标中，初期数据清理最低责任应在阶段 0/1 冻结。
- 真实模型评测是否只使用合成资料；如希望使用 Luke 私人对话，需明确同意边界、留存位置、供应商处理与事后删除方式。
- 每阶段学习复述由 Luke 口头讲解还是写入私人学习笔记；工程决策、架构和阶段结果仍应留在产品仓库的计划/ADR 位置，私人学习笔记遵循项目约定。

## 研究输入

- 项目规范：[AGENTS.md](file:///Users/lukemyself/Projects/SayHear-v2/AGENTS.md) 与 [CONTEXT.md](file:///Users/lukemyself/Projects/SayHear-v2/CONTEXT.md)。
- 旧 companion、记忆与 Reflection 研究：[研究目录](file:///Users/lukemyself/Projects/SayHear/docs/research/)。其内容有第一方产品材料，也包含推断；本文优先引用其可复查官方链接，不把结论自动升级为决定。
- Luke 的 [开发思考笔记](file:///Users/lukemyself/Downloads/SayHear%20开发思考笔记.html) 是研究输入。笔记关于 OpenAI Agents SDK 的 provider-lock-in 说法与当前官方 ModelProvider 文档不一致；对框架排名和工期数字不作为已证事实。
- 适用原则改变了这份计划的形状：Foundational Thinking 促使先定端到端 scaffold 和逐阶段增长，而不先写 schema；Experience First 使验收先锚定真实聊天感受；Minimize Reader Load 使候选分层并避免多个重叠系统；Guard the Context Window 促使只保留足以支撑选择的证据与限制。完整 skill 内容已在本会话读取。

throughput checkpoint: n/a, read-only investigation
