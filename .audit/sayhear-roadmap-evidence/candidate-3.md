# SayHear v2 阶段级搭建与学习路线（候选 3）

研究日期：2026-10-20。性质：独立候选方案，不是实施授权。仓库基线为 `/Users/lukemyself/Projects/SayHear-v2` 当前 `main`（`86c5ba8`），仓库内没有功能代码。

本候选读过 `CONTEXT.md`、`AGENTS.md`、`GLOSSARY.md`、`docs/` 路由文件，读过旧仓库四份 companion/memory 研究与 2026-10-20 的 Harness/Memory 复盘，也读过 `/Users/lukemyself/Downloads/SayHear 开发思考笔记.html`。网页证据为本次独立检索，优先官方文档与 npm registry。旧资料只作为线索，涉及当前能力时以本次可核实的官方页面为准。

---

## 1. 结论与独立立场

### 1.1 一句话方案

**买模型管道，自己握上下文契约。Harness 是一个很小的循环，记忆是一套策略而不是一个可以安装的产品。10 周按四个阶段推进，每个阶段都以一次真实模型的完整 trace 收尾，Luke 能沿着这条 trace 解释每个边界。**

具体组合：

- 运行时用 AI SDK 7 的原语（`streamText` / `ToolLoopAgent`）加自己写的上下文组装，不引入完整 Agent 框架作为底座。
- 对话回合留在 Vercel Function 内，流式返回，显式停止；后台的反思与画像重建用 Vercel Workflows，但只传 ID，不传私人正文。
- 数据库用 Neon Postgres，测试库与用户库是两个独立项目；检索从第一天就是 Postgres FTS 加 pgvector 的混合路径，而不是先词法后补语义。
- 记忆层留一个很窄的端口，2026 年内只跑一次挑战者实测（首选 Hindsight），不接第二个记忆服务，不把任何厂商存储当记录系统。
- 可观测分两层：工程 trace 走 OpenTelemetry 到 Langfuse，产品“运行详情”从自己的 canonical 数据重建。两者不能互相替代。

### 1.2 与另外两条常见路线的差别

| 路线 | 主张 | 本候选的判断 |
| --- | --- | --- |
| Mastra 优先 | 用一体框架同时拿到 loop、记忆、观察压缩、评测 | 它隐藏的正是今年要学的 loop，而它最有差异化的 Observational Memory 默认按 thread 隔离，跨 thread 的 resource scope 已标记 deprecated。跨日连续性主要落在默认关闭、且会增加时延的 semantic recall 上。除非自建 loop 超出预算，否则不作为第一阶段底座。 |
| Memory 服务优先 | 先用 Hindsight/Honcho/Mem0 替换记忆，再决定运行时 | 记忆服务能改善召回，但 SayHear 的差异化是来源、纠正、遗忘与“什么有资格被读取”。这些语义在厂商 schema 里没有位置。先把自己的混合检索基线做出来，才有公平的比较对象。 |
| 全自建 | 从 HTTP 开始写所有东西 | 重复实现 provider 适配、流式协议、工具循环与重试，学习收益低，维护成本高。AI SDK 已经把这一层做成可检查的原语，直接用。 |

### 1.3 这个候选明确不做的事

- 不在 2026 年接第二个记忆服务，不做三臂全量改造。
- 不把 Open Loop、主动跟进、日记 Tab、实时语音、完整多用户系统放进 10 周。
- 不建通用评测平台，不建 Memory Inspector 产品页。
- 不写 schema，不排逐 PR 计划。本文只定阶段边界、可观察验收与学习证据。

---

## 2. 证据基础与能力边界

### 2.1 平台分层

先把“买什么、握什么”按层分开，避免把不同层的结论混在一起。

| 层 | 候选 | 本候选的处理 |
| --- | --- | --- |
| 平台与基础设施 | Vercel Functions、Workflows、Cron、Queues、Neon、Provider API | 复用。Vercel 部署，Neon 存数据，Provider 走统一端口。 |
| 运行时 / Harness | AI SDK 7、Mastra、LangGraph、OpenAI Agents SDK、Claude Agent SDK、自建轻量循环 | 用 AI SDK 原语加自有上下文组装。其余作为对照与退路。 |
| 记忆组件 | Mem0、Zep/Graphiti、Letta、Honcho、Hindsight、Postgres 原生混合检索 | 2026 年用 Postgres 原生基线，Hindsight 作为唯一挑战者。 |
| 产品语义 | canonical 数据、人格、Reflection、纠正/遗忘、运行详情 | 全部自有。任何厂商都不能成为产品概念的唯一住所。 |
| 可观测与评测 | Langfuse、promptfoo、OpenTelemetry、自有运行详情 | 工程 trace 与产品 trace 分开建。 |
| 后台任务 | Vercel Cron、Vercel Workflows、Vercel Queues、Inngest、Trigger.dev | Cron 触发，Workflows 执行，Queues 是 beta 不依赖。 |

### 2.2 Harness 对照

版本与发布日期取自 2026-10-21 的 npm registry，能力取自官方文档。版本会变，实施时应重新固定。

| 候选 | 可核实能力 | 关键限制 | 判断 |
| --- | --- | --- | --- |
| AI SDK 7（`ai` 7.0.148，2026-10-21） | Provider 抽象、文本与 UI 流、工具调用与审批、`stopWhen` 多步循环、`prepareStep`、OpenTelemetry telemetry、MockLanguageModel 测试工具 | 7.0 仅 ESM、要求 Node 22 以上；`ToolLoopAgent` 在内存中运行，进程崩溃即丢失进度；telemetry 只负责发出 span，需要外部后端；`useChat` 不负责消息持久化；可恢复流需要自己接 Redis 与端点；客户端断开或调用 `stop()` 不会取消生成，必须自己写停止端点 | 作为运行时原语采用。它给的是可检查的零件，不是完整产品。 |
| AI SDK WorkflowAgent | 在 `workflow@5` 上持久化状态与工具步骤，支持重试与审批暂停 | 需要 `@ai-sdk/workflow`、`workflow@5`、`ai`、`zod`；`stream()` 默认没有步数上限，必须设 `stopWhen`；`generate()` 默认最多 20 步 | 第一阶段不用。对话回合不需要跨部署恢复，后台任务才需要。 |
| Mastra（`@mastra/core` 1.78.0，2026-10-15） | TypeScript 一体框架，Agent、Workflow、Memory、Evals、Observability；Working Memory、Semantic Recall、Observational Memory；resource/thread 作用域 | 核心 Apache-2.0，`ee/` 目录另许；Memory 需要 storage provider；Semantic Recall 默认关闭，会增加 embedding 与向量检索时延；Observational Memory 默认 30,000 token 触发 Observer、40,000 token 触发 Reflector，压缩比约 5 至 40 倍，建议至少 128K 上下文模型；OM 的 resource scope 已 deprecated | 作为第二阶段退路与挑战者，不作为第一阶段底座。 |
| LangGraph（JS 版） | 长时运行、有状态编排、checkpointer、human-in-the-loop、Store 长期记忆、流式 | 官方定位是低层编排框架，不抽象 prompt 与架构；Python 生态更强；对单人格聊天产品引入图状态机的心智负担大于收益 | 不采用。没有需要图编排的产品需求。 |
| OpenAI Agents SDK（`@openai/agents` 0.21.0，2026-10-20） | MIT；agents、handoffs、guardrails、sessions、tracing；支持 OpenAI 与其他 provider | sessions 是对话历史，不是长期记忆；handoffs 与 guardrails 服务于多 agent 任务路由，不是单人格陪伴；官方记忆路径指向外部服务 | 不采用。买到的东西恰好不含本产品最缺的部分。 |
| Claude Agent SDK（`@anthropic-ai/claude-agent-sdk` 0.3.306，2026-10-21） | 把 Claude Code 作为库运行，内置文件、命令、搜索工具，hooks、subagents、sessions、权限；Python 与 TypeScript | 受 Anthropic Commercial Terms 约束；本质是机器操作 agent，工具面是文件与 shell；绑定 Claude 模型 | 不采用。形状不对，锁定强，工具面不需要。 |
| 自建轻量循环 | 上下文组装、调用、流式、工具执行、停止、失败分类，全部可见 | 重试、取消、provider 差异、流式边界都要自己负责 | 采用“自有策略 + AI SDK 原语”，不是从 HTTP 重写。 |

### 2.3 Memory 对照

| 候选 | 可核实能力 | 关键限制 | 判断 |
| --- | --- | --- | --- |
| Postgres 原生混合 | FTS、pgvector、结构化过滤、时间与资格条件都在一个库里；删除与来源天然一致 | 需要自己写抽取、合并、重排；embedding 供应商要另选 | 第一阶段基线。直接对准旧项目“换种说法就搜不到”的失败。 |
| Hindsight | retain 抽取并链接实体，recall 并行做语义、关键词、图与时间检索后重排，reflect 最多 10 轮并必须先取证据再回答；Postgres + pgvector；Docker/K8s 自托管；Python/TS/Go SDK | 官方首页未写许可证，旧研究称 MIT，需在接入前核实；reflect 会自己跑推理循环，不能直接塞进对话回合；新服务与抽取成本 | 唯一挑战者。用 retain/recall，不用 reflect 进对话。 |
| Mem0 | Apache-2.0；add/search；平台版有专有优化与原生图记忆 | 官方 graph memory 页面描述的是 Platform，未说明 OSS 是否仍含图记忆；默认抽取不等于消解矛盾；OSS 与 Platform 能力不同 | 不采用。若未来瓶颈是抽取而不是检索，再评估。 |
| Zep / Graphiti | Graphiti Apache-2.0，双时态图，episodes 保留来源，关系变化时使旧边失效；支持 Neo4j、FalkorDB、Neptune | 需要单独运维图数据库；参考 MCP/REST server 没有认证、授权与注入防护；Zep Cloud 免费 10,000 credits/月，Flex $125/50,000 credits，1 credit 约 350 字节，检索与存储不计费；社区版退役只见二手来源，需核实 | 不采用。时间推理最强，但对一个真实用户成本与运维过重。 |
| Letta | Apache-2.0；Letta Code 是状态化 agent harness，memory blocks、MemFS、会话搜索 | 仓库页面显示 V1 API server 已进入 archive 分支，重心转向 Letta Code；作为应用底座等于采纳它的运行时 | 不采用。方向已变，不适合作为组件。 |
| Honcho | AGPL-3.0；peer 表征、`context()` 与 `.chat()` 五档推理；摄入 $2/百万 token，`.chat()` 从 $0.001 到 $0.50/次 | AGPL；自托管需要 Postgres、pgvector、Redis 与多个 LLM 角色（旧研究口径，官方页未列全）；小公司长寿风险 | 不采用。留作 2027 年“理解层”候选。 |

### 2.4 版本与日期快照

以下取自 2026-10-21 npm registry，只用于说明“当前是什么”，不作为长期承诺。

- `ai` 7.0.148，2026-10-21。
- `workflow` 5.2.3，2026-10-20。
- `@mastra/core` 1.78.0，2026-10-15；`@mastra/memory` 1.38.0；`@mastra/pg` 1.31.2。
- `@openai/agents` 0.21.0，2026-10-20。
- `@anthropic-ai/claude-agent-sdk` 0.3.306，2026-10-21。
- `@ai-sdk/openai-compatible` 3.0.75。
- `promptfoo` 0.124.1，MIT。
- `drizzle-orm` 0.45.4，Apache-2.0；`postgres` 3.4.9，Unlicense。

---

## 3. 技术判断与取舍

### 3.1 为什么第一阶段不用 Mastra

三条理由，按证据强度排序。

1. **它隐藏的正是学习目标。** CONTEXT 要求 Luke 能解释模型上下文如何组成、错误来自哪一层。Mastra 的 Agent 与 Memory 是一体封装，默认行为多，trace 需要另接 observability。自建上下文组装让“这一段为什么进来”成为可读代码，而不是框架默认值。
2. **它的跨日记忆与产品要求有缝。** Observational Memory 默认 thread 级，resource scope 已 deprecated；跨 thread 的语义召回默认关闭，且官方明确会增加 embedding 与向量检索时延。SayHear 要的是跨日、跨会话、带来源的连续性，这个缝不能靠改名填上。
3. **接入成本不一定换来删除。** 如果用 Mastra 但关掉它的 memory，只把它当 loop，收益接近 AI SDK 原语，却多了一层框架 API 与升级面。如果用它的 memory，就把来源、纠正、遗忘的语义交给了一个不为这些语义设计的 schema。

**什么情况下改判。** 如果 P0 的自有 loop 加上下文组装超过约 15 个 agent 工作小时，或 P1 的检索与上下文策略超过约 10 个 agent 工作小时仍无法达到验收，就停止自建，转 Mastra 做一次两天的 spike。这个门槛要在 P0 开始前写下，不许事后调整。

### 3.2 为什么第一阶段不接 Memory 服务

旧项目的连续记忆失败可以拆成四类。第一类，不知道自己只看到部分历史。第二类，该联想时没发起查询。第三类，查了但词法不匹配。第四类，找到旧状态却漏了最新状态。这四类里，只有第三类直接由检索技术决定。第四类由时间与资格过滤决定，前两类由上下文契约决定。

一个记忆服务可以改善第三类，但不能替产品决定“哪些历史有资格进入这一轮”“模型是否知道自己看的是局部”“新状态如何压过旧状态”。先把这四件事在自己的上下文契约里做对，再让挑战者在同一份冻结样本上比较，才有归因。

**挑战者的接入方式。** 记忆端口只暴露三个动作，分别是索引一段经历、按查询召回带来源的候选、按用户或来源失效。挑战者只能待在这个端口后面，canonical 原文永远在自己的库里。这样换供应商是重索引，不是记忆清零。

### 3.3 Postgres 与服务选择

- **Neon。** 免费档 1 GB 存储、100 CU-hours/项目、每项目 10 分支、5 分钟无活动后缩零；pgvector 所有档位可用；HNSW 支持 `vector` 到 2,000 维、`halfvec` 到 4,000 维。测试库与用户库用两个独立 Neon 项目，不用同一项目的分支，避免“测试误连用户库”这类错误在凭证层面就无法发生。
- **Supabase。** 免费档 500 MB，项目一周无活动会暂停。不作为主选，暂停行为会让“随时可用的线上服务”变成不可预期。
- **Vercel Postgres 已停止。** 现有库已迁到 Neon，新项目通过 Marketplace 接 Postgres。不要再按旧文档设计。
- **数据访问。** 推荐 `postgres` 驱动加手写 SQL 与迁移，学习收益最高，隐藏最少。Drizzle 仍是 0.x，等查询复杂度真的上来再评估。这一条是推荐，不是已定。

### 3.4 可观测与评测

两层，不能合并。

1. **工程 trace。** AI SDK telemetry 发 OpenTelemetry span，送到 Langfuse（MIT，`ee/` 除外，可自托管）。它回答“这次调用花了多少 token、哪一步慢、哪个工具失败”。AI SDK 官方明确它只负责发出，不提供完整后端。
2. **产品运行详情。** 从自己的 canonical 数据重建。它展示这一轮实际送出的系统提示、选中的历史、记忆候选与入选理由、工具调用与失败位置。它回答“为什么它这么说”，也是 Luke 学习上下文组装的主要教具。

评测分三层，按成本从低到高：

- 确定性测试。用 `MockLanguageModelV4` 与 `simulateReadableStream` 固定模型输出，验证持久化、取消、工具循环、失败分支。它证明控制流，不证明真实模型会主动检索。
- 数据集回归。promptfoo（MIT）跑固定场景集，断言结构化行为，例如“必须出现来源 ID”“不得在没有证据时断言事实”。它适合 CI，不适合判断语气。
- 小样本盲评。10 至 30 条真实场景，人工并排判断被理解感、自然度、是否像监控。旧研究里 Tolan 的做法是小数据集加人工判断，不是大榜。

**明确不建：** 通用评测平台、自动晋升门禁、以厂商 benchmark 分数做选型。旧研究已经记录 LoCoMo 答案键审计与厂商互测的配置差异，这些数字不能用来选冠军。

### 3.5 后台任务

- **对话回合不进 Workflow。** 一次流式回答在 Function 内完成，`maxDuration` 在 Hobby 是 300 秒，Pro 可到 800 秒。回合内做持久化与停止，不做跨部署恢复。
- **反思与画像重建进 Workflow。** 它需要重试、暂停、跨部署恢复。Vercel Workflows 的 run 没有总时长上限，`sleep` 也没有上限，单 run 上限 25,000 events、10,000 steps，replay 超过 240 秒可能中止。
- **隐私约束。** Workflow 的 run payload 会被 Vercel 保存。Hobby 保留 1 天，最多 66 天；Pro 保留 7 天，最多 96 天。run metadata 不加密，官方明确不要把个人或敏感数据放进 attributes 或 hook token。因此后台任务的输入输出只放 ID 与状态，正文由 step 从自己的库里读。若某类任务连 ID 都不想外流，用 `experimental_retention: 0`，但它要求 `workflow` 5.0 以上，且返回值为不可读。
- **Cron。** Vercel Cron 只支持 UTC，触发方式是 HTTP GET，每项目最多 100 个。它只负责“到点启动”，不负责执行语义。
- **Queues 是 beta。** 不作为 2026 年的依赖。

### 3.6 Provider 可替换

AI SDK 的 provider 抽象解决了协议差异，但没有解决能力差异。需要一张显式的能力表，至少覆盖流式、工具调用、结构化输出、上下文窗口、embedding、prompt caching 与首 token 时延。启动时校验，缺失能力直接失败，不要在运行时猜。

DeepSeek 官方文档确认 OpenAI 兼容的 chat completions 与 `stream: true`；function calling 页面本次没有给出明确说明，需要在接入时实测。OpenCode 官方文档说支持 75 个以上 provider 与自定义 OpenAI 兼容端点，但它首先是编码工具，作为产品 Provider 前要核实它的服务条款与稳定性。WorkBuddy 本次只找到腾讯云的企业 HTTP API 文档，没有找到可核实的模型 Provider 文档，接入前必须拿到正式说明。

**判断。** 第一阶段只接一个主 Provider 加一个 OpenAI 兼容的备用端点，不同时接三家。每多一家，就多一套能力差异与失败语义要解释。

### 3.7 部署与账号

Vercel Hobby 明确只允许非商业个人使用，商业用途需要 Pro 或 Enterprise。Luke 自用阶段可以用 Hobby，但第一个非 Luke 的真实用户出现前必须升级 Pro。Hobby 的 Function 上限 300 秒、Workflow payload 保留 1 天，这两条会直接影响后台任务设计。

---

## 4. 10 周路线

时间从 2026-10-20 到 2026-12-31，约 10.3 周。每周 10 小时是 Luke 的时间，包含讨论、阅读、体验、讲解与笔记，不包含 agent 后台实现。这个区分决定了路线能否成立。如果 Luke 要自己写全部代码，100 小时不够覆盖本文范围，必须砍掉 P3 的一半。

四个阶段，每个阶段以一次真实模型验收收尾。阶段内不排 PR。

### P0（第 1 周，10 小时）：最小垂直切片

**目标。** 从浏览器输入到模型流式返回，再到持久化与运行详情，整条路径一次打通。Luke 能画出这条路径并指出每一层的失败会长什么样。

**Feature spec。**

- 一个可部署的 Web 聊天页，复用旧 Portal 的布局与交互语言，支持流式输出。
- 一个 Provider 端口，接一个主 Provider，配置从环境变量读取，缺失时启动失败并给出明确错误。
- 每轮的用户原文与 AI 输出写入 canonical 存储，刷新页面后顺序与内容不变。
- 一个“运行详情”视图，显示这一轮实际送出的系统提示、消息序列、模型名、token 用量、结束原因。
- 显式停止。停止后保留已生成的部分，不追加迟到内容。客户端断开不视为停止，必须调用停止端点。

**验收。**

- 真实 Provider 连续完成 10 轮对话，无重复消息、无丢失、无乱序。
- 刷新、重新部署后历史仍在。
- 停止一次生成后，数据库里没有停止之后的追加内容。
- 主动制造一次 Provider 超时，页面显示可理解的失败，运行详情记录失败位置，重试成功。
- 运行详情里的消息序列与数据库里的这一轮完全一致。

**学习证据。**

- Luke 能不看代码画出请求路径，并说明消息在哪一步落库。
- 能解释为什么“客户端断开”不等于“取消生成”，以及停止端点做了什么。
- 能指出一次失败属于 Provider、网络、持久化还是渲染。

**退出条件。** 如果这一周结束时还不能稳定完成 10 轮，停止加功能，先修这条路径。P0 的失败不允许用 P1 的功能掩盖。

### P1（第 2 至 4 周，30 小时）：上下文契约与跨日连续性

**目标。** 让模型在“只看到局部历史”的情况下仍然知道自己看到了什么，并且能用不同措辞找到较早的经历。这是对旧项目四类失败的直接回应。

**Feature spec。**

- 每轮自动组装一个有明确预算的上下文：人格与行为约束、近期原文窗口、少量跨会话召回、当前时间与覆盖范围说明。
- 覆盖范围说明是产品行为，不是调试信息。模型必须知道“这是某段时间的窗口，不是完整历史”，不能把局部总结说成全部。
- 召回走 Postgres 混合路径：全文检索、向量检索、时间与资格过滤，合并后按预算注入。召回的每一条都带来源标识与发生时间。
- 提供一个 `search_past` 工具，用于预取没覆盖到的更深查询。工具返回的来源同样进入运行详情。
- 新状态优先。同一主题出现更新的证据时，旧证据不得压过新证据；上下文里保留时间，让模型能区分“当时”和“现在”。
- 运行详情增加“召回候选与入选理由”，能回答“为什么这条进来了，那条没进来”。

**验收。**

- 用与原文不同的措辞询问 7 天前的一件事，正确来源进入上下文，回答不需要模型主动调用工具。
- 当预取没有覆盖时，模型会调用 `search_past`，且调用理由可从 trace 读出。
- 问“你记得我最近换工作了吗”这类状态更新问题时，新旧证据都在，最终回答以新证据为准。
- 让模型总结“过去两周”，它会说明自己只看到哪些范围，不冒充完整。
- 30 个真实回合的时延有记录，分别记首 token 与完成，记上下文 token 数与召回耗时。没有这些分母的数字不算验收。

**学习证据。**

- 任取一轮，Luke 能逐段解释上下文，说明每一段为什么在、预算多少、去掉会怎样。
- 能预测一次改动的 token 变化方向，误差在 ±20% 以内。
- 能判断一次失败属于“没搜”“搜错”“没更新”“读错”中的哪一类。

**退出条件。** 如果混合检索仍不能修复换措辞的漏召回，停止优化自有路径，提前进入挑战者实测。如果召回把时延推到不可接受，先把召回改为回合开始时的预取，而不是砍掉召回。

### P2（第 5 至 7 周，30 小时）：Reflection、来源与信任边界

**目标。** 让“记住”从检索片段升级为带依据的观察与画像，同时保证纠正与删除能穿透所有派生层。

**Feature spec。**

- 对话结束后异步产生观察，每条观察保留它依据的原始消息标识，区分用户明确表达与 AI 推断。
- 画像是一段叙事投影，显示上次更新时间与状态，不宣称是完整记忆清单。画像只从当前有资格的观察生成。
- 纠正与遗忘走对话内动作。纠正后下一轮不再召回旧内容；遗忘后原文、观察、画像与缓存路径都不得再出现。
- 信任边界变更后，旧画像立即可读性关闭，显示“正在更新”或“暂时不可用”，不允许用旧内容掩盖后台延迟。
- 后台任务幂等。重试不产生重复观察，删除后不被异步任务写回。

**验收。**

- 任取一句画像，能沿观察展开到原始消息，再展开到具体表达。
- 说“那条不对，其实是……”后，下一轮回答不再使用旧内容，运行详情能看到失效。
- 删除一条来源后，检索、画像、缓存三条路径都不再返回它。
- 人为让后台任务失败并重试，观察数量不增加。
- 信任边界变更的瞬间刷新页面，看不到包含失效内容的旧画像。

**学习证据。**

- Luke 能解释“用户说过”“AI 推断”“当前画像”三者的区别，并在一轮真实对话里各举一例。
- 能说明一次删除在每一层的传播路径，以及哪一层最容易漏。
- 能解释为什么画像刷新不等于纠正。

**退出条件。** 如果 3 周内无法同时做到来源可展开与删除不复活，缩小范围到“只做来源与删除，不做画像页面”，把画像留到 2027 年。信任边界不能为了进度让步。

### P3（第 8 至 10 周，30 小时）：可靠性、评测与日常使用

**目标。** 让产品在 Luke 的日常使用中稳定，让回归可重复，让时延数字可解释。

**Feature spec。**

- 失败分类进入运行详情：Provider 失败、超时、工具失败、检索为空、检索错误、上下文超预算、持久化失败。
- 取消、重发、超时、重试都有确定性测试，且测试断言的是用户可观察行为。
- 一个小型真实场景集，覆盖换措辞召回、状态更新、覆盖范围、纠正、删除、自然度。确定性用例进 CI，真实模型用例按预算手动或定时跑。
- 时延预算按段记录：上下文组装、召回、首 token、完成。每份报告带运行次数、Provider、模型、上下文 token 数。
- 连续两周由 Luke 日常使用，记录失败与不自然的地方，不追求 engagement 指标。

**验收。**

- 两周内至少 60 个真实回合，失败都能归到上面七类之一。
- 关键路径的确定性测试在每次改动后通过；真实模型小样本在阶段结束时跑一次，结果与失败例一起保存。
- 时延报告能回答“慢在哪一段”，而不是只有一个总数。
- 删除、停止、重试在真实使用中没有出现数据不一致。

**学习证据。**

- Luke 能读一份时延报告，指出限制因素，并说明这个数字不能证明什么。
- 能解释哪一类回归由哪一层测试捕获，哪一类只能靠盲评。
- 能独立完成一次“改上下文策略、跑回归、读结果、决定保留或回退”的闭环。

**退出条件。** 如果前三个阶段延期，P3 只保留失败分类、停止与重试测试、时延记录，砍掉场景集扩充与两周日常使用的完整覆盖。

---

## 5. 学习路线

### 5.1 每周节奏

每周 10 小时，建议这样分：

- 2 小时：闭卷回忆上一次的核心机制，再看代码核对。这是检索练习，不是复述笔记。
- 3 小时：读官方文档或论文的一个窄问题，带着一个可回答的问题读，不泛读。
- 3 小时：实际运行、观察 trace、做一次预测并对照结果。
- 2 小时：向 agent 讲解，接受追问，把讲解要点写进学习笔记并标注 commit。

每两周一次 30 分钟的阶段回顾，只回答三个问题。决定了什么，观察到了什么，还有什么不知道。

### 5.2 有依据的方法与边界

| 方法 | 证据 | 在本计划里的用法 | 边界 |
| --- | --- | --- | --- |
| 检索练习 | Roediger & Karpicke 2006；Karpicke & Blunt 2011；Dunlosky 等 2013 把 practice testing 列为高效 | 每次学习开始先闭卷回忆，再核对 | 实验室多为短材料与短延迟，不能保证复杂系统设计的迁移 |
| 分散练习 | Cepeda 等 2006；Dunlosky 等 2013 列为高效 | 每个阶段的核心问题在 1 周后与 3 周后各回访一次 | 最佳间隔依赖目标保持时间，不能机械套公式 |
| 交错练习 | Rohrer & Taylor 2007；Rohrer、Dedrick 与 Stershic 2020 的随机对照试验 | 交替做“读 trace”和“预测 trace”，不要整周只做一种 | 效果在真实课堂里比实验室小且不均匀 |
| 自我解释 | Bisra 等 2018 元分析，总体效应约 g=0.55 | 提问前先写下自己的预测与理由，再让 agent 解释 | 效应中等，提示方式影响很大 |
| 以教促学 | Kobayashi 2019，准备教 g≈0.35，准备加教 g≈0.56；Ribosa 与 Duran 2022 生成教材 g≈0.17 | 每周向 agent 讲一次，接受追问 | 效应不大，不能当作掌握的证据 |
| 有效失败 | Kapur 2008 | 只用于设计预测：先自己给方案，再看解释 | 不是无目的试错，环境与工具问题不适用 |
| 合意困难 | Bjork 与 Bjork 2011 | 接受“当时感觉更难、之后更牢”的练习形式 | 是框架，不是具体处方 |

### 5.3 反 metacognitive laziness 的协议

两项证据直接支持这个协议。Bastani 等 2025 的 PNAS 论文标题为 Generative AI without guardrails can harm learning，研究约一千名土耳其高中生的数学练习；Wharton 的官方解读称，无护栏版本在练习阶段高约 48%，撤掉工具后比从未使用者低约 17%，带教师设计提示、禁止直接给答案的版本消除了这个损害。本次只核实了 DOI 与标题，没有读到 PNAS 正文，百分比应视为该论文报告值经官方解读转述。Fan 等 2024 的研究中，117 名大学生使用 ChatGPT 后文章分数更高，但知识获得与迁移没有显著差异，自我调节过程受到影响；这一条来自 arXiv 摘要。

因此本计划对 agent 的讲解设三条硬规则：

1. **先预测，后解释。** Luke 先写下“我认为这段上下文会包含什么、为什么”，agent 再展示真实结果。预测错误比听一遍正确解释更有学习价值。
2. **先提示，后答案。** agent 先给方向性提示，Luke 尝试后再展开。直接贴完整实现只在 Luke 明确要求或时间紧迫时发生。
3. **讲解必须带真实 trace。** 不用抽象例子替代当前代码与实际运行。讲完要能指到具体一轮对话、具体一条来源、具体一个失败。

这三条是学习协议，不是产品功能。它们约束的是主 Agent 的行为，需要写进阶段工作方式，而不是代码。

### 5.4 学习证据的形式

不用考试，不看课时。每个阶段留下四样东西：

- 一张 Luke 手画（或口述后整理）的机制图，能标出数据流向与失败点。
- 一段 10 分钟的讲解记录，主题是“这一轮上下文是怎么来的”，附对应 commit。
- 三个真实失败例，每个能归因到一层，并说明下一次如何更早发现。
- 一个仍未回答的问题，进入下一阶段的待确认清单。

学习笔记放在 `/Users/lukemyself/Documents/学习/AI/Agent Harness`，按 CONTEXT 的约定由主 Agent 整理，注明 commit 与是否合入。

---

## 6. 取舍：100 小时能买到什么

### 6.1 时间分配

| 阶段 | 周 | Luke 小时 | 主要产出 | 阶段门 |
| --- | --- | --- | --- | --- |
| P0 | 1 | 10 | 可部署的流式聊天、持久化、运行详情、停止 | 10 轮稳定，失败可归层 |
| P1 | 3 | 30 | 上下文契约、混合召回、覆盖范围、跨日连续性 | 换措辞能召回，状态更新正确，时延有分母 |
| P2 | 3 | 30 | 带来源的观察与画像、纠正与遗忘、幂等后台 | 来源可展开，删除不复活 |
| P3 | 3 | 30 | 失败分类、回归、时延报告、两周日常使用 | 60 个真实回合，失败可归类 |
| 缓冲 | 0.3 | 0 | 阶段回顾与补漏 | 不预设 |

### 6.2 明确砍掉的范围

这些不是“以后再说”的模糊承诺，而是 2026 年不做：

- 实时语音与语音优先交互。
- 日记 Tab 与日记生成产品面。可以保留原始导出，不做阅读界面。
- Open Loop、主动跟进、outbound 通知。
- 完整多用户系统、邀请、计费、滥用控制。但数据从第一天就按用户隔离，避免以后重写。
- 完整纠正与遗忘 UI。只做对话内动作与最小状态显示。
- Memory Inspector、Claim 浏览器、画像编辑器。
- 第二个记忆服务、第二个 Agent 框架、第二个向量库。
- 通用评测平台、自动晋升门禁、厂商 benchmark 排名。
- 微调、蒸馏、自训 embedding。

### 6.3 如果落后，按这个顺序砍

1. 先砍 P3 的场景集扩充与两周日常使用的完整覆盖，保留失败分类与停止/重试测试。
2. 再砍画像页面，只保留来源展开与删除传播。信任边界不能砍。
3. 再砍 `search_past` 工具，只保留自动预取。工具调用可以在 2027 年补。
4. 不砍 P0 的停止与失败处理，不砍 P1 的覆盖范围说明，不砍 P2 的删除不复活。这三项是产品承诺，不是功能。

### 6.4 这个预算买不到的东西

100 小时买不到“熟练的 Harness 工程师”，也买不到“经过验证的陪伴产品”。它能买到的是一条能解释的完整路径、一套能重复的验证方法、四个阶段的真实 trace，以及对“哪一层该买、哪一层该握”有自己的判断。这个判断比多做一个功能更接近 CONTEXT 的目标。

---

## 7. 决策清单

### 已定（来自 CONTEXT 与 AGENTS，不在本候选重开）

- 2026 年目标是可日常使用的文本 Agent，部署到 Vercel，掌握 Harness 基础知识。
- 两套隔离数据库，测试库不得连接或重置用户库。
- canonical 数据保留原始表达、AI 产物与来源关系。
- 人格、基础记忆、跨日连续性、逐步完善的 Reflection 在年内范围内。
- 日记、完整纠正与遗忘、Open Loop、实时语音、完整多用户系统在年内范围外。
- Provider 必须可替换，能力差异要明确处理。
- 学习成果以“能解释机制与取舍”为准，不以课时或笔记为准。
- 学习笔记固定路径，仓库只放符号链接。

### 推荐（本候选的判断，可被证据推翻）

- 运行时用 AI SDK 7 原语加自有上下文组装，不采用完整框架作为底座。
- 第一阶段记忆用 Postgres FTS 加 pgvector 的混合路径，不用外部记忆服务。
- 对话回合不进 Workflow；后台反思进 Workflow，payload 只放 ID。
- 工程 trace 用 OpenTelemetry 加 Langfuse；产品运行详情从 canonical 数据重建。
- 评测用 MockLanguageModel 做确定性测试，promptfoo 做数据集回归，小样本人工盲评做语气。
- 测试库与用户库用两个独立 Neon 项目。
- Hobby 用到第一个非 Luke 用户出现，然后升 Pro。
- 2026 年只跑一个记忆挑战者，首选 Hindsight，且只测 retain/recall。

### 待讨论（需要 Luke 的产品或偏好判断）

- embedding 供应商与数据边界。私人文本发给谁做向量化，是一个产品承诺问题，不是技术细节。
- 是否接受 Vercel Workflow 保存后台任务的 payload。若不可接受，改用自有 job 表加 Cron，代价是重试与恢复要自己写。
- 运行详情默认展示到什么程度。全量模型输入对学习最有价值，但对未来用户可能过于技术化。
- 时延门槛。旧项目的 90% 在 15 秒内是历史标准，v2 是否沿用，需要 Luke 定。
- 是否保留 `search_past` 工具，还是只做自动预取。这会影响模型自主性与可解释性。
- 数据访问用原生 SQL 还是 Drizzle。学习收益与开发速度的取舍。

### 待实测（不实测就不能写进结论）

- 混合检索是否真的修复“换种说法就搜不到”，在 SayHear 自己的中文语料上。
- Hindsight 在冻结样本上是否优于自有基线，扣除新服务与抽取成本后是否仍有净收益。
- Mastra 的 Observational Memory 在本产品规模下是否真的减少上下文 token，还是只增加后台调用。
- DeepSeek、OpenCode、WorkBuddy 的工具调用、流式与结构化输出保真度。
- 在回合内做召回是否能把 90% 回合压在 15 秒内。
- Vercel Workflow 的保留策略在真实使用中是否触碰隐私边界。
- 100 个 Luke 小时加 agent 后台实现，能否覆盖本文范围。这是最大的未知。

---

## 8. 待确认问题

按对决策的影响排序，只列资料无法回答、且会改变路线的问题。

1. **embedding 数据边界。** 是否允许把私人对话原文发给第三方 embedding 服务？如果不允许，是否接受本地模型或纯 FTS 加关键词扩展？
2. **时延门槛。** v2 的验收是沿用“90% 在 15 秒内”，还是先测出一个基线再定？
3. **后台任务的数据位置。** 是否接受 Vercel Workflow 短暂保存 payload？如果不接受，是否接受自建 job 表带来的恢复复杂度？
4. **运行详情的默认可见性。** 它是 Luke 的学习工具，还是未来用户的产品功能？两者的信息密度与措辞不同。
5. **第一个非 Luke 用户的时间点。** 它决定 Pro 升级、多用户隔离与访问控制的优先级。
6. **失败预算。** 如果 P0 超过一周，是压缩 P1 还是压缩 P3？本候选建议压缩 P3，但这需要 Luke 确认。

---

## 9. 来源

标注分三级。**[本次核实]** 表示本次直接读取了页面或 registry。**[旧研究]** 表示结论来自旧仓库研究文档，本次未重新抓取原始页面。**[二手]** 表示第三方来源，只用于标注不确定性。

### 项目一手材料

- `/Users/lukemyself/Projects/SayHear-v2/CONTEXT.md`，立项共识与 2026 目标。
- `/Users/lukemyself/Projects/SayHear-v2/AGENTS.md`，文档路由与协作规则。
- `/Users/lukemyself/Projects/SayHear-v2/GLOSSARY.md`，术语。
- `/Users/lukemyself/Projects/SayHear/docs/research/2026-10-20-harness-memory-retrospective.md`，旧项目失败复盘与候选评估。
- `/Users/lukemyself/Projects/SayHear/docs/research/memory-systems-engineering-practice.md`，抽取时机、schema、检索、grounding、评测。
- `/Users/lukemyself/Projects/SayHear/docs/research/memory-recall-companion-ux.md`，九家产品的召回、透明度、纠错与遗忘。
- `/Users/lukemyself/Projects/SayHear/docs/research/ai-companion-warmth-curiosity-continuity.md`，六家 companion 的人格、好奇与连续性。
- `/Users/lukemyself/Projects/SayHear/docs/research/continuation-profile-product-patterns.md`，对话内主动性与 Profile 透明度。
- `/Users/lukemyself/Downloads/SayHear 开发思考笔记.html`，2026-10-20 的开发笔记。

### 平台与运行时

- Vercel Functions 最大时长：https://vercel.com/docs/functions/configuring-functions/duration **[本次核实]**。Hobby 300 秒，Pro 800 秒，扩展 beta 1800 秒。
- Vercel Workflows：https://vercel.com/docs/workflows **[本次核实]**。无总时长上限，25,000 events/run，10,000 steps/run，replay 240 秒上限。
- Workflow 定价与限制：https://vercel.com/docs/workflows/pricing **[本次核实]**。Hobby 50,000 events/月，1 GB 写入。
- Workflow 数据保留：https://vercel.com/docs/workflows/retention **[本次核实]**。Hobby payload 保留 1 天、最多 66 天；metadata 不加密；`experimental_retention: 0` 需 `workflow` 5.0 以上。
- Vercel Cron：https://vercel.com/docs/cron-jobs **[本次核实]**。UTC，HTTP GET，每项目 100 个。
- Vercel Queues：https://vercel.com/docs/queues **[本次核实]**。Beta。
- Vercel Postgres：https://vercel.com/docs/postgres **[本次核实]**。已停止，迁至 Neon。
- Vercel Hobby：https://vercel.com/docs/plans/hobby **[本次核实]**。非商业个人使用。
- Vercel 公平使用：https://vercel.com/docs/limits/fair-use-guidelines **[本次核实]**。商业用途需 Pro 或 Enterprise。
- Vercel Observability：https://vercel.com/docs/observability **[本次核实]**。
- AI SDK 7 迁移指南：https://ai-sdk.dev/docs/migration-guides/migration-guide-7-0 **[本次核实]**。ESM only，Node 22 以上。
- AI SDK Agents 概览：https://ai-sdk.dev/docs/agents/overview **[本次核实]**。
- AI SDK WorkflowAgent：https://ai-sdk.dev/docs/agents/workflow-agent **[本次核实]**。需 `workflow@5`；`stream()` 无默认步数上限。
- AI SDK Memory：https://ai-sdk.dev/docs/agents/memory **[本次核实]**。SDK 只提供工具接口，存储与检索由 provider 或自定义实现负责。
- AI SDK Telemetry：https://ai-sdk.dev/docs/ai-sdk-core/telemetry **[本次核实]**。需要外部后端。
- AI SDK 工具循环：https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling **[本次核实]**。`stopWhen`、`prepareStep`、同一步工具并发。
- AI SDK 测试：https://ai-sdk.dev/docs/ai-sdk-core/testing **[本次核实]**。MockLanguageModelV4、simulateReadableStream。
- AI SDK Chatbot：https://ai-sdk.dev/docs/ai-sdk-ui/chatbot **[本次核实]**。不负责消息持久化。
- AI SDK 可恢复流：https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams **[本次核实]**。需要 Redis 与自定义端点；客户端断开不取消生成。
- OpenAI 兼容 Provider：https://ai-sdk.dev/providers/openai-compatible-providers **[本次核实]**。
- Mastra 文档：https://mastra.ai/docs **[本次核实]**。
- Mastra Memory：https://mastra.ai/docs/memory/overview **[本次核实]**。
- Mastra Semantic Recall：https://mastra.ai/docs/memory/semantic-recall **[本次核实]**。默认关闭，增加时延。
- Mastra Observational Memory：https://mastra.ai/docs/memory/observational-memory **[本次核实]**。30k/40k 阈值，5 至 40 倍压缩，resource scope deprecated。
- Mastra Evals：https://mastra.ai/docs/evals/overview **[本次核实]**。
- Mastra Observability：https://mastra.ai/docs/observability/overview **[本次核实]**。不强制 Mastra Cloud。
- Mastra 仓库与许可：https://github.com/mastra-ai/mastra **[本次核实]**。Apache-2.0 加 `ee/`。
- LangGraph JS 概览：https://docs.langchain.com/oss/javascript/langgraph/overview **[本次核实]**。
- OpenAI Agents SDK 仓库：https://github.com/openai/openai-agents-js **[本次核实]**。MIT。
- Claude Agent SDK 概览：https://code.claude.com/docs/en/agent-sdk/overview **[本次核实]**。Commercial Terms。
- DeepSeek API：https://api-docs.deepseek.com/ **[本次核实]**。OpenAI 兼容与流式。
- OpenCode Providers：https://opencode.ai/docs/providers/ **[本次核实]**。
- WorkBuddy 企业 HTTP API：https://cloud.tencent.com/document/product/1831/137064 **[本次核实]**。只证明企业 API，不证明模型 Provider。

### 记忆与数据

- Hindsight：https://hindsight.vectorize.io/ **[本次核实]**。retain/recall/reflect，Postgres + pgvector；许可证未在首页写明。
- Mem0 OSS 概览：https://docs.mem0.ai/open-source/overview **[本次核实]**。
- Mem0 graph memory：https://docs.mem0.ai/open-source/features/graph-memory **[本次核实]**。页面描述 Platform，未确认 OSS。
- Mem0 仓库：https://github.com/mem0ai/mem0 **[本次核实]**。Apache-2.0。
- Graphiti 仓库：https://github.com/getzep/graphiti **[本次核实]**。Apache-2.0，Neo4j/FalkorDB/Neptune，参考 server 无认证。
- Zep 定价：https://www.getzep.com/pricing **[本次核实]**。免费 10,000 credits/月，Flex $125/50,000，1 credit 约 350 字节。
- Zep 社区版退役：https://github.com/N1nEmAn/openzep/blob/main/README.md **[二手]**。需向 Zep 官方核实。
- Letta 仓库：https://github.com/letta-ai/letta **[本次核实]**。Apache-2.0；V1 API server 在 archive 分支。
- Letta Code：https://github.com/letta-ai/letta-code **[本次核实]**。
- Honcho：https://honcho.dev/ **[本次核实]**。AGPL-3.0；$2/百万 token 摄入。
- Neon 定价：https://neon.com/pricing **[本次核实]**。免费 1 GB、100 CU-hours、10 分支。
- Neon pgvector：https://neon.com/docs/extensions/pgvector **[本次核实]**。HNSW 2,000 维。
- Supabase 定价：https://supabase.com/pricing **[本次核实]**。免费 500 MB，一周无活动暂停。
- pgvector 仓库：https://github.com/pgvector/pgvector **[本次核实]**。HNSW 与 IVFFlat。
- Langfuse 仓库：https://github.com/langfuse/langfuse **[本次核实]**。MIT 加 `ee/`。
- promptfoo：https://www.promptfoo.dev/docs/intro/ **[本次核实]**。MIT（npm registry）。

### 产品参照

- Tolan 官网：https://www.tolans.com/ **[本次核实]**。只证明定位与公开表述，不证明实现。
- Rosebud：https://www.rosebud.app/ **[本次核实]**。回忆旧条目、连接想法、$12.99/月，隐私与 HIPAA aligned 为厂商自述。
- Day One 功能页：https://dayoneapp.com/features/ **[本次核实]**。“On this Day” 回看旧条目。
- OpenAI Memory FAQ：https://help.openai.com/en/articles/8590148-memory-faq **[旧研究]**。Summary 与 Sources 不是完整归因。
- Replika 记忆说明：https://help.replika.com/hc/en-us/articles/37208679176077-How-does-Replika-s-memory-work **[旧研究]**。本次抓取返回 403，未重新核实。
- OpenAI × Tolan 案例：https://openai.com/index/chatgpt-memory-dreaming/ **[旧研究]**。厂商案例，机制可参考，数字不作独立证据。

### 学习科学

- Roediger & Karpicke 2006，Test-Enhanced Learning，Psychological Science 17(3):249-255，DOI 10.1111/j.1467-9280.2006.01693.x **[本次核实 DOI]**。
- Karpicke & Blunt 2011，Retrieval Practice Produces More Learning than Elaborative Studying with Concept Mapping，Science 331:772-775，DOI 10.1126/science.1199327 **[本次核实 DOI]**。
- Dunlosky 等 2013，Improving Students' Learning With Effective Learning Techniques，PSPI 14(1):4-58，DOI 10.1177/1529100612453266 **[本次核实 DOI]**。
- Cepeda 等 2006，Distributed practice in verbal recall tasks，Psychological Bulletin 132(3):354-380，DOI 10.1037/0033-2909.132.3.354 **[本次核实 DOI]**。
- Rohrer & Taylor 2007，The shuffling of mathematics problems improves learning，Instructional Science 35:481-498，DOI 10.1007/s11251-007-9015-8 **[本次核实 DOI]**。
- Rohrer、Dedrick 与 Stershic 2020，A randomized controlled trial of interleaved mathematics practice，Journal of Educational Psychology，DOI 10.1037/edu0000367 **[本次核实 DOI]**。
- Bisra 等 2018，Inducing Self-Explanation: a Meta-Analysis，Educational Psychology Review，DOI 10.1007/s10648-018-9434-x **[本次核实 DOI]**。
- Kobayashi 2019，Learning by Preparing-to-Teach and Teaching: A Meta-Analysis，Japanese Psychological Research，DOI 10.1111/jpr.12221 **[本次核实 DOI]**。
- Ribosa & Duran 2022，Do students learn what they teach when generating teaching materials for others，Educational Research Review，DOI 10.1016/j.edurev.2022.100475 **[本次核实 DOI]**。
- Kapur 2008，Productive Failure，Cognition and Instruction 26(3):379-424，DOI 10.1080/07370000802212669 **[本次核实 DOI]**。
- Bjork & Bjork 2011，Making things hard on yourself, but in a good way，收于 Psychology and the Real World **[二手引用]**。
- Bastani 等 2025，Generative AI without guardrails can harm learning，PNAS，DOI 10.1073/pnas.2422633122 **[本次核实 DOI 与标题]**；48% 与 17% 来自 Wharton 官方解读 https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education/ **[二手转述，未读正文]**。
- Fan 等 2024，Beware of Metacognitive Laziness，arXiv:2412.09315 **[本次核实摘要]**。
- Frattaroli 2006，Experimental disclosure and its moderators，Psychological Bulletin 132(6):823-865，DOI 10.1037/0033-2909.132.6.823 **[本次核实 DOI]**。
- Guo 2022，The delayed, durable effect of expressive writing on depression, anxiety and stress，British Journal of Clinical Psychology，DOI 10.1111/bjc.12408 **[本次核实 DOI]**。

---

## 10. 本候选的弱点

写下来，方便与其他候选比较时被攻击。

1. **自建 loop 的时间估计可能过于乐观。** 100 个 Luke 小时加 agent 实现，能否在 10 周内覆盖四个阶段，没有证据。P0 的退出条件就是为此设的。
2. **Postgres 原生混合检索可能不够。** 它修复词法漏召回，但不解决实体链接、矛盾消解与跨事件推理。如果 P1 验收失败，本候选的“先基线后挑战者”顺序会让挑战者测试推迟。
3. **Hindsight 的许可证与自托管成本未完全核实。** 官方首页没有写许可证，旧研究称 MIT；接入前必须核实，否则挑战者测试可能白做。
4. **Vercel Workflow 的隐私约束可能推翻后台设计。** 如果 Luke 不接受 payload 外流，方案要改成自有 job 表，重试与恢复的成本会上升。
5. **学习协议依赖主 Agent 自律。** “先预测后解释”如果执行不到位，会退化成看讲解，metacognitive laziness 的风险仍在。
6. **没有回答“陪伴质量”本身。** 本候选优化的是可解释性与连续性，语气、共情与独立判断只靠小样本盲评，没有系统方案。这是产品层最大的空白，也是 2027 年的主要工作。
