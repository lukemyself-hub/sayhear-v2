# SayHear v2 候选路线 2

研究日期为 2026-10-20。本文件是提供给 arena 评审的候选输入，不是已批准架构。未修改仓库、创建服务或运行下载文件。不预定 schema、SDK 版本、价格或逐 PR 方案。

建议采用 AI SDK 支撑模型调用和流式交互，应用保留上下文构造、canonical 数据和人格规则，先建立可追溯的历史检索，再加入 Reflection。Mastra 是最值得比较的整体替代候选。若其运行时、记忆和工作流能减少维护量，同时完整展示每轮上下文和来源，就可以替代应用侧编排。不要同时引入两个主编排框架，也不要先自建通用 Harness。

这项推荐依据阶段需求匹配，不是性能结论。AI SDK 提供循环控制与 Provider 抽象，但数据归属、持久化和陪伴质量仍由应用负责。Mastra 提供更完整的记忆组件，但能否符合 SayHear 的来源区分和未来遗忘要求仍需验证。[S1][S2][S3]

## 共识和结论状态

已定事项来自 `/Users/lukemyself/Projects/SayHear-v2/CONTEXT.md`。

- 产品倾听日常经历和情绪，保持非人类身份、共情和独立判断，不经营浪漫、排他或依赖关系。
- 年底交付可日常使用的文本 Agent，包含基础 Harness、canonical 数据、人格、基础记忆、Reflection、运行详情、测试数据集和 Vercel Web 部署。
- 原始表达与 AI 产物分开，产物保留依据。用户自述不等于经外部核验的事实。`fact`、`opinion`、`profile` 尚未定义为互斥类型或表。
- 测试库和真实用户库隔离，私人对话不自动进入测试集或仓库。最初用户是 Luke，但数据归属与访问兼容未来多用户。
- 复用旧 Portal 聊天交互，重新适配 v2 协议。日记、完整纠正与遗忘、Open Loop、实时语音和完整多用户后置。
- Luke 每周约 10 小时，包含讨论、阅读、体验、讲解和笔记，后台 Agent 时间另计。

已读取 `AGENTS.md` 和 `docs/decisions.md`。ADR 索引尚无决策，旧仓库 ADR 不能成为 v2 的默认约束。

| 状态 | 本候选结论 |
| --- | --- |
| 推荐 | AI SDK 优先，一个托管 Postgres 服务，合成数据先行，基础检索先于复杂记忆，Reflection 不阻塞前台回复，只选一个追踪评测平台。 |
| 待讨论 | Mastra 是否替代应用编排，数据库与身份服务组合，哪些服务可接收真实内容，成本上限和质量目标。 |
| 待实测 | Provider 协议兼容、流式取消、工具失败、中文陪伴风格、记忆增益、运行时延、Reflection 是否帮助后续交流。 |

## 分清平台层级

| 层级 | 候选与可核实能力 | 应用仍需负责 |
| --- | --- | --- |
| 模型接入 | AI SDK Provider 和厂商 Client SDK 处理请求与流式输出。[S1][S2] | 模型能力差异、具体协议、数据发送边界。 |
| Agent 编排 | AI SDK、LangGraph、Mastra、OpenAI Agents SDK 提供循环、流程或 Agent 原语。[S1][S3][S4][S5] | 人格、上下文选择、停止政策、产品语义。 |
| 自管进程 Agent | Claude Agent SDK 运行 Claude Code binary，带工具、权限、会话、hooks。[S6] | 进程托管与隔离。它不等同于普通 Claude API。 |
| 状态型 Agent 平台 | Letta 持久化 Agent 状态、memory blocks、消息和工具记录。[S9] | 是否接受平台拥有上下文和状态生命周期。 |
| 派生记忆 | Mem0、Graphiti、Zep、Mastra memory 提供抽取、检索、摘要或图。[S3][S7][S8] | 原始记录权威、推断标记、纠正删除传播、体验评测。 |
| 关系数据 | Neon 是托管 Postgres，Supabase 是围绕 Postgres 的后端平台。[S10][S11] | 数据归属、访问规则、测试隔离、恢复验证。 |
| 追踪评测 | Langfuse、LangSmith 提供 traces、数据集与实验。[S12][S13] | 什么是好回答、标签质量、真实内容流向。 |
| 持久后台任务 | Inngest、Trigger.dev、Vercel Workflow 提供任务执行与恢复机制。[S14][S15][S16] | 副作用幂等、输入版本、业务完成条件。 |

数据库不是记忆策略，向量索引不是用户画像，trace 不是 canonical 历史，checkpoint 不是长期生活记录。这是本候选的职责划分，不是供应商的统一架构。

## Harness 候选和拒绝理由

| 方案 | 官方可核实能力与限制 | 本阶段判断 |
| --- | --- | --- |
| AI SDK | `stopWhen` 控制终止，`prepareStep` 调整消息、工具、模型；统一 Provider 接口，但模型能力不统一。[S1][S2] | 推荐。适合 Web 文本和可解释上下文。采用成熟循环，不因教学重复实现流式协议。持久化、权限和产品记忆仍需设计。 |
| LangGraph | 有状态编排、持久化、恢复、人工介入；生产持久化需要 checkpointer。LangSmith Deployment 是另一个部署产品。[S4] | 暂不优先。复杂暂停恢复或多分支流程出现时重评。不是因为不能做聊天，而是当前需求不足以支付图状态学习和维护成本。 |
| Mastra | 消息历史、working memory、semantic recall、observational memory；需要 storage。工作流支持暂停恢复和步骤组合。[S3] | 次选而非陪跑。若完整运行详情、来源与退出路径可控，集成收益可能超过 AI SDK。不能把自动观察当作已验证的用户画像。 |
| OpenAI Agents SDK | Sessions 管理跨 run 历史，tracing 记录模型和工具；可通过 Model、ModelProvider 或 AI SDK adapter 接入其他模型，部分功能限定 Responses。[S5] | OpenAI 为主要 Provider 时可优先考虑。当前多 Provider 未定，暂不引入额外 session 语义和适配。不能称它只支持 OpenAI。 |
| Claude Agent SDK | Python、TypeScript SDK 运行 Claude Code agent loop 和 binary，提供内置文件、命令、MCP、权限与会话。[S6] | 暂不作为主聊天 Harness。运行环境和任务工具与当前文本陪伴需求不匹配。调用 Claude 模型不要求采用此 SDK。 |
| 按需轻量循环 | AI SDK 官方有 manual loop 示例，允许应用控制流程。[S17] | 保留退路。只有具体框架约束阻碍已验收需求时才自建局部循环，不把“理解原理”变成“重造所有边界处理”。 |

推荐先用一个合成会话贯穿候选比较，要求展示最终模型输入、一次工具往返、明确停止、取消和错误落点。Agent 可后台建立 AI SDK 与 Mastra 的有限验证，Luke 只花约两小时检查结果与解释。只有影响选型的问题才做实验，不举办六框架实现竞赛。

Provider 第一阶段只正式支持一个服务，另用第二个验证替换边界。OpenCode、WorkBuddy 等名字不自动代表标准公开 API，需要核实实际服务地址、认证、模型目录和授权用途。DeepSeek 等具体能力也以接入时文档与请求验证为准。比较项目包括文本流、工具调用、结构化输出、取消、错误格式、usage 和模型限制，不承诺“一换 key 完全等价”。[S2][S5]

## 记忆与 Reflection 的选择

| 方案 | 能力及证据限制 | 使用或拒绝条件 |
| --- | --- | --- |
| 应用历史检索加有依据摘要 | 推荐的产品设计，原始记录权威，检索和摘要可重建。并非外部效果事实。 | 年底默认基线。先比较近期历史、摘要和按需检索，避免立即叠加图、reranker 与复杂抽取。 |
| Mastra memory | 内置多种 memory，持久化依赖 storage。[S3] | 若采用 Mastra，可先复用其检索和历史组件。需验证 resource/thread 边界、证据保留、更新与清理。 |
| Mem0 | 有 OSS 库、自托管服务及托管平台，README 展示 add/search。[S7] | 可作为派生层候选，不接管原始记录。当前网页对 graph 行为与旧资料不一致，不能沿用旧 Neo4j、relations、更新算法结论。先锁定具体包与文档，再验证抽取、重复、冲突、删除。 |
| Graphiti | 开源时序图框架；Zep 文档描述增量图与时序关系。[S8] | 关系与时间查询已成为主要失败来源时才考虑。需承担图后端、实体消解、运维和重建，不因“生活有人际关系”就上图。 |
| Zep | 基于 Graphiti 的托管上下文服务，另有用户、线程、消息管理及上下文组装。[S8] | 能降低运营工作，但引入额外数据处理方与状态生命周期。Graphiti 的开源能力不代表 Zep 所有功能可自托管复现。 |
| Letta | 数据库存储 Agent 状态，核心 memory blocks 进入上下文，可由 Agent 或开发者修改，另有 archival memory。[S9] | 是整体状态型 Agent 替代路线，不是随手插入的向量库。除非愿意将运行时和记忆一起交给平台，否则暂不选。 |

任何记忆组件都需回答四个问题。它记住的内容来自哪里，表达者是谁，什么时候成立，当前回复为什么选中它。这里要求可解释来源，不提前规定表名或认识类型。

Reflection 的最低产品定义是对一段已保存历史生成带依据的观察，标出不确定性，在后续对话中验证作用。它不把 AI 早先推断反复总结成“用户事实”，不把一次情绪升级为人格标签。第一次采用用户或开发者显式触发，质量稳定后再考虑定时触发。需保留失败状态、处理范围和产物版本，以便重跑与比较。上述是推荐规格，不宣称现成组件自动满足。

全文纠正与遗忘按共识后置，但基础内容查看与清理不能后置。年底至少允许检查来源、禁用错误派生内容、清理指定测试或用户内容，并保证停用内容不继续参与上下文。精细的对话内纠正、跨所有派生产物的完整遗忘和备份删除承诺仍在后续阶段明确。若基础清理无法可信完成，就不开放长期真实数据使用。

## Postgres、可观测与后台任务

数据库推荐先在 Neon 与 Supabase 二选一，不另加图数据库或独立向量服务。

- Neon 提供独立连接的数据库分支，通常分支包含父分支数据，另有 schema-only 分支。[S10] 它适合应用服务器负责访问的路线。测试隔离不能用“从线上分支复制”替代，推荐独立测试项目或数据库与凭据，仅装载合成数据。
- Supabase 提供 Postgres、访问能力和 RLS。`service_role` 可绕过 RLS，不能把“开了 RLS”当成服务器自动安全。[S11] 若希望同时复用 Auth 和数据库控制台，推荐它作为更完整候选。应验证服务器访问路径、越权、备份恢复；数据库备份不含 Storage API 对象内容。[S11]
- 选型实际权重是区域、从 Vercel 的连接方式、身份服务组合、恢复与迁移、每月预算。现有资料不足以宣布谁最便宜或最快。开户前查当时套餐、区域和条款，不在路线里引用猜测价格。

运行详情是产品能力，追踪平台是开发工具，两者分开。产品详情至少显示模型输入的组成、实际选入的历史与记忆、工具参数结果、错误位置和耗时。这里的“模型输入”是应用实际发送内容，不声称能够展示模型内部思维过程。

推荐 Langfuse 作为独立追踪评测候选。它支持数据集、实验、分数，且可在导出前 masking。[S12] LangSmith 支持离线数据集评测和 pairwise 实验，采用 LangGraph 时更值得考虑。[S13] 二者都不能替代质量标准。真实内容默认留在产品数据边界内，第三方 trace 仅发必要元数据或获准的脱敏内容。合成数据可完整追踪。不要自动把生产 trace 一键转测试集，即使平台支持该功能。

后台首选顺序是先显式触发 Reflection，确定正确性，再引入一个可靠任务方案。若只每日处理少量待办，Vercel Cron 配合待处理扫描可以足够，但官方明确 Cron 不自动重试、可能漏发或重复、可能并发。[S18] 因而 Cron 不是可靠队列。

Inngest 提供 step 重试与已完成结果复用，去重窗口不等于外部副作用 exactly-once。[S14] Trigger.dev 支持运行和任务触发幂等键，但重试任务内部副作用仍可能重复。[S15] Vercel Workflow 使用 workflow/step 和持久执行，可作为减少平台数量的候选，仍要检验部署限制、重放与数据保留。[S16] 三者选一，避免再自建通用任务系统。无论选谁，重复 Reflection 不能生成重复画像，任务中断不能把半成品当成当前认识。

## 产品研究带来的具体约束

| 产品 | 可核实公开行为 | 借鉴与限制 |
| --- | --- | --- |
| Tolan | 官方供应商案例描述每轮重建上下文，组合人格、近期摘要、检索记忆、语气信息，以及夜间整理。[S19] | 借鉴显式上下文构造和逐轮体验评测。案例属于团队自述，不用其中留存或召回提升数值证明 SayHear 效果。 |
| Replika | 官方帮助中心区分可见 Memory tab 和更深的对话模式记忆，用户可添加、查看和移除部分记忆。[S20] | 借鉴可见控制，避免让用户误以为可见条目等于全部内部记忆。公开文档不能证明其记忆准确率或心理收益。 |
| ChatGPT | saved memories 与历史分开，删除聊天不会自动删除相应 saved memory。[S21] | 清理范围需要说清，不能只删聊天 UI 而继续用派生内容。不能据此推断其内部 schema。 |
| Rosebud | 通过以往日记连接主题、关系与情绪；官方承认精确日期召回较弱，实验性精确回忆可能更慢。[S22] | 日记价值来自时间连续性与回看，不只是一份总结。将时间变化纳入本地样例。其成长导向不应改变 SayHear 默认倾听定位。 |
| Day One | 官方有端到端加密和多格式导出，导出文件可能未加密。[S23] | 借鉴可携带与清楚的数据承诺。服务端调用模型的 SayHear 不能据此宣传同等 E2EE。 |

年底不实现 Journal Tab。未来日记的讨论应区分用户原始记录与第三人称 AI 观察，允许回到依据、纠正与再生成。Open Loop 与主动跟进需要先解决何时打扰、如何退出、过期和取消，不以“更像人”为理由直接开启通知。实时语音先等文本人格、记忆和时延诊断稳定，再引入转写误差、打断与音频保存边界。

## 五个阶段，按可验证结果推进

以下小时数是 Luke 参与预算，不是开发工期预测。总计 100 小时，约十周。每阶段先共同确认体验目标、feature spec 和学习重点。阶段结束同时检查行为、体验与理解，未通过时先修正，不机械推进。

| 阶段 | Luke 时间 | 体验目标与 feature spec | 验收证据 | 学习证据与待确认 |
| --- | --- | --- | --- | --- |
| 1. 基础对话与记录，第 1 至 2 周 | 20 小时 | 一个可运行的文本会话；持久保存原始消息与运行结果；独立测试数据；解释发送内容和归属。讨论并选择 Harness、数据库与首个 Provider。 | 合成会话刷新后可继续；错误与中断不会伪装成完整回复；测试凭据不能访问用户库；部署环境有基本访问控制。 | Luke 沿一次真实请求说明 UI、服务、模型、数据库的职责，解释为何原始消息不是 AI 产物。待确认 canonical 的语义边界，之后才设计结构。 |
| 2. 可控制的 Harness 与人格，第 3 至 4 周 | 20 小时 | 流式反馈、停止、有限工具调用、失败展示、运行详情；复用旧聊天 UI；加入倾听、非人类身份与不盲从的稳定人格。 | 一次工具成功、失败、超限与取消能追踪；至少第二 Provider 的有限兼容验证；代表性情境中不抢建议、不虚构离线经历、不用依赖话术。 | Luke 能指出一次失败属于 Provider、循环、工具还是界面，并解释停止与重试差异。待确认可接受等待和人格样例，数字不预设为实测。 |
| 3. 跨日基础记忆，第 5 至 6 周 | 20 小时 | 隔天交流能找回相关经历，区分时间变化和同名人物；查看来源；错误派生内容可停用；正式选择是否引入记忆组件。 | 同一数据集比较近期历史基线和检索方案；覆盖关系、变化、否定、无答案、无关记忆及用户隔离；来源能回到真实记录，停用后不再注入。 | Luke 根据一次错误区分“没取到”“取错”“取到了但说错”，能解释历史、摘要、画像和检索的不同。待确认记忆范围及未来纠正语义。 |
| 4. 有依据的 Reflection，第 7 至 8 周 | 20 小时 | 从限定历史形成可查看观察与画像候选，保留依据、时间和不确定性；下一轮交流有选择地使用；运行可重试。 | 在同一案例上比较启用与关闭 Reflection；不能把推断当原话，不能用自己的旧产物自证；重复运行无重复生效，失败保留旧可用状态；不拖慢正常聊天路径。 | Luke 解释一次观察为何成立、哪些证据会使其失效，并判断结果是否帮助后续回复。待确认触发频率、候选确认方式及后台服务。 |
| 5. 日常使用与收口，第 9 至 10 周 | 20 小时 | 约一半时间用于部署与日常体验复核，另一半作为前阶段返工与学习缓冲；收紧前台、运行详情和数据清理。 | 线上服务独立于开发电脑；多天真实使用记录与合成回放分别保存；验证越权、模型故障、后台失败与恢复；说明内容去向和已知限制。 | Luke 不看预写讲稿，借实际 trace 解释整条链路，并对一个新案例提出诊断。待确认是否达到年底目标；未达则明确延期范围，不把实验版宣传成完成品。 |

每周十小时的建议分配为四小时体验与共同构建、两小时看实际机制、两小时比较和决策、一小时延迟回顾、一小时零散缓冲。它是可调整的时间盒，不按学习时长认定掌握。Agent 后台研究、代码实现和合成数据运行不计入，但 Luke 审查它们的时间计入。

前两阶段就让 Luke 使用可部署文本产品，不等所有底层设计完成才展示。人格、记忆和 Reflection 按共识顺序增加，运行详情从第一阶段保留必要证据，第二阶段形成可展开界面。最后阶段不能承担所有测试，隔离、来源和错误处理随着各阶段验证。

## 评测不靠一个总分

建议建立约 20 至 30 个信息充足的合成生活片段，组成 8 至 12 条跨日故事，再从中生成代表性提问。这是初始预算提案，不是统计充分性声明。应覆盖同名人物、关系变化、暂时情绪、观点改变、日期、否定、没有证据和敏感内容。每个案例注明期望行为、依据和禁止断言。

确定性检查验证归属隔离、来源存在、停止生效、停用内容不注入、重复任务不重复生效。人工评审检查听懂、自然召回、不过度推断、不急于建议和没有监控感。模型评审可帮助筛查，不能决定唯一真值。小样本只支持发现问题与比较当前配置，不支持宣称普遍准确率。

比较记忆时保持模型、人格、输入历史和预算一致，分别看检索命中、回答依据和用户体验。比较 Reflection 时使用同一后续情境的开关对照，避免把换模型收益归给 Reflection。时延拆成首段可见、总完成、检索、工具和后台耗时，报告样本量、网络与 Provider 条件，不把流式显示当作总时延降低。质量验收阈值在取得基线后由 Luke 确认。

## 学习方式及证据边界

Dunlosky 等人的综述将分散练习和练习性提取评为较高效用；自我解释证据有价值但覆盖较有限。[S24] Chi 等人的研究观察到，较成功的学习者会把示例步骤与原理联系，并监控理解。[S25] 这些研究不是 AI 辅助开发者的直接随机试验，不能承诺十周后掌握所有 Harness 知识。

将方法转成项目中的行为。

- 先看一条真实运行示例，Agent 解释关键机制，Luke 指出自己不理解的一段。不是先读完整课程。
- 在当前任务里提出一个有用预测，例如“历史检索为空时回复应改变什么”，随后看实际 trace。不开考试，不为学习制造无意义故障。
- 一周后在新的真实问题中再次使用同一概念，例如从工具重试迁移到 Reflection 重试。让机制跨场景出现，不背定义。
- 学习记录写清“能解释”“借提示能解释”“尚不清楚”，并记录当时运行或提交。笔记完成不等于掌握，后续用实际诊断修正判断。

学习笔记仍按项目要求写入 `/Users/lukemyself/Documents/学习/AI/Agent Harness`，由主 Agent 管理。本研究不在该目录写文件。每阶段的一次解释、一次应用和后续再次使用，比阅读页数或课时更能作为理解证据。

## 百小时内的取舍与后续方向

保留年底目标中的基础记忆与最小 Reflection，不把它们全部推到明年。削减的是范围和自动化程度。只做文本、一个主 Provider、一个主 Harness、一个关系数据库服务、一个追踪平台。第二 Provider 验证替换，不要求功能完全相同。Reflection 可先显式触发，不承诺自动每日整理。画像可以少而有依据，不追求覆盖所有人生维度。

拒绝年底同时做图记忆、多 Agent 社会、长期规划器、完整管理后台、模型排行榜、语音、日记和主动消息。也拒绝以原始模型 API 自建全部编排，或仅因框架“更完整”就交出所有数据语义。已有方案不能解决的具体问题才增加复杂度。

第 4 周检查基础对话、持久化、停止与运行详情是否稳定。若不稳定，先停止记忆组件探索。第 6 周若基础记忆没有清楚增益，保留简单检索并修复证据链，不叠加图。第 8 周若 Reflection 频繁产生无依据结论，保留查看和显式触发，暂停自动进入上下文。若这样会改变已定年底交付，应与 Luke 明确讨论，而不是静默降级。

下一年度按需求推进完整纠正与遗忘、导出删除、多用户运营、第三人称日记、Open Loop 与适时跟进、语音。它们有共同前提，但不必写死总顺序。日记依赖可靠记录与产物区分，主动跟进依赖时效和用户控制，真实多用户发布依赖完整访问和数据生命周期，语音依赖稳定文本体验与打断语义。每阶段都重新确认产品目标。

## 资料冲突和研究限制

已只读参考旧仓库四份研究的摘要和主要段落。

- `/Users/lukemyself/Projects/SayHear/docs/research/ai-companion-warmth-curiosity-continuity.md`
- `/Users/lukemyself/Projects/SayHear/docs/research/companion-warmth-curiosity-continuity-research.md`
- `/Users/lukemyself/Projects/SayHear/docs/research/memory-recall-companion-ux.md`
- `/Users/lukemyself/Projects/SayHear/docs/research/memory-systems-engineering-practice.md`

前两份对 Pi 是否有可管理长期记忆的描述冲突，旧研究还含“全部产品”“没有任何一家”这类超出有限公开资料的概括。本候选不沿用这些全称结论，也不沿用旧 schema、召回数量或 ADR。下载的 `/Users/lukemyself/Downloads/SayHear 开发思考笔记.html` 已按文本读取相关段落。它提出 Mastra、canonical 自有、记忆作为派生层的思路值得比较，但其价格、基准损坏比例和“没有任何现成系统”断言没有在本次逐项验证，不作为结论依据。

本次 Mem0 搜索摘要仍描述外部图数据库和 relations 数组，而直接抓取的官方页面描述平台内置图、不同结果形式；GitHub README 又描述 add-only 新算法。这是文档或版本错配信号。未锁定版本前不宣称哪套图语义必然存在。本候选只采用能稳定确认的库、平台、add/search 定位，其余列为待实测。

尚未安装或执行任何候选，也未核实真实账户套餐、地区、最新版本和端到端表现。本研究的来源验证支持“公开提供何种能力”，不支持“哪个系统效果最好”。采用 Experience First 原则，把年底范围压到自然文本交流、可信连续性与可理解运行。采用 Prove It Works 原则，将文档事实与必须实际验证的质量明确分开。

## Sources

以下官方文档、第一方案例与学术来源均在本次搜索或抓取中查到。文档可变，接入时需对照锁定版本重新核实。来源只支撑相邻能力陈述，不支撑未测效果。

- [S1 AI SDK loop control](https://ai-sdk.dev/docs/agents/loop-control)。停止和逐步控制，不保证持久性或陪伴效果。
- [S2 AI SDK providers and models](https://ai-sdk.dev/docs/foundations/providers-and-models)。统一接口，能力表不完整且模型有差异。
- [S3 Mastra memory](https://mastra.ai/docs/memory/overview) 与 [workflows](https://mastra.ai/docs/workflows/overview)。组件与存储要求，不证明推断准确。
- [S4 LangGraph overview](https://docs.langchain.com/oss/javascript/langgraph/overview) 与 [durable execution](https://docs.langchain.com/oss/javascript/langgraph/durable-execution)。本次抓取后者主要得到持久化说明，不据此声称所有重放细节已核实。
- [S5 OpenAI Agents SDK models](https://openai.github.io/openai-agents-js/guides/models/)、[sessions](https://openai.github.io/openai-agents-js/guides/sessions/) 与 [tracing](https://openai.github.io/openai-agents-js/guides/tracing/)。支持适配其他模型，能力仍有 Provider 限制。
- [S6 Claude Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)。说明运行 Claude Code binary 的进程模式，与 Client SDK、Managed Agents 区别。
- [S7 Mem0 官方仓库](https://github.com/mem0ai/mem0) 与 [graph memory 文档入口](https://docs.mem0.ai/open-source/features/graph-memory)。当前检索和抓取有差异，不沿用旧实现假设。
- [S8 Zep vs Graphiti](https://help.getzep.com/zep-vs-graphiti) 与 [Graphiti introduction](https://help.getzep.com/graphiti/getting-started/welcome)。供应商对平台和框架的说明，非独立效果验证。
- [S9 Letta memory](https://docs.letta.com/guides/agents/memory/) 与 [agents API](https://docs.letta.com/api/resources/agents)。持久 Agent 与记忆机制，不保证产品语义。
- [S10 Neon 官方 workflow primer 源文件](https://github.com/neondatabase/website/blob/main/content/docs/get-started/workflow-primer.md) 与 [serverless pooling](https://github.com/neondatabase/website/blob/main/content/docs/guides/serverless-connection-pooling.md)。分支和连接机制，不证明隔离策略自动正确。
- [S11 Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)、[database overview](https://supabase.com/docs/guides/database/overview)、[backups](https://supabase.com/docs/guides/platform/backups)。权限绕过和备份范围需单独注意。
- [S12 Langfuse datasets](https://langfuse.com/docs/evaluation/experiments/datasets)、[scores](https://langfuse.com/docs/evaluation/scores/data-model)、[masking](https://langfuse.com/docs/observability/features/masking)。提供评测设施和脱敏入口，不自动保证脱敏完整。
- [S13 LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types)。离线、回归与实验比较，不定义 SayHear 的好坏标准。
- [S14 Inngest idempotency](https://www.inngest.com/docs/durable-execution/guides-and-advanced/idempotency) 与 [retries](https://www.inngest.com/docs/durable-execution/guides-and-advanced/error-handling/retries)。任务去重不等于外部副作用只执行一次。
- [S15 Trigger.dev idempotency](https://trigger.dev/docs/idempotency)。key 限定任务触发，不保护任务内所有 API 调用。
- [S16 Vercel Workflow 官方仓库](https://github.com/vercel/workflow) 与 [workflows and steps](https://github.com/vercel/workflow/blob/main/docs/content/docs/v5/foundations/workflows-and-steps.mdx)。部署时仍须核实版本与服务限制。
- [S17 AI SDK manual loop](https://ai-sdk.dev/cookbook/node/manual-agent-loop)。控制方式示例，不是完整生产 Harness。
- [S18 Vercel Cron 管理](https://vercel.com/docs/cron-jobs/manage-cron-jobs)。明确无失败自动重试、可能重复、漏发及并发。
- [S19 Tolan 官方供应商案例](https://openai.com/index/tolan/)。团队自述，不是独立对照试验。
- [S20 Replika memory](https://help.replika.com/hc/en-us/articles/37208679176077-How-does-Replika-s-memory-work) 与 [memory controls](https://help.replika.com/hc/en-us/articles/360000874712-What-does-my-Replika-remember-about-me)。公开交互行为，不披露完整内部机制。
- [S21 ChatGPT memory](https://help.openai.com/en/articles/8590148-memory-in-chatgpt)。产品生命周期行为，不代表所有 API 产品。
- [S22 Rosebud long-term memory](https://help.rosebud.app/ai-analysis/long-term-memory) 与 [weekly report](https://help.rosebud.app/ai-analysis/weekly-report)。官方能力与限制说明，不是疗效证据。
- [S23 Day One E2EE FAQ](https://dayoneapp.com/guides/day-one-sync/end-to-end-encryption-faq/) 与 [export](https://dayoneapp.com/guides/tips-and-tutorials/exporting-entries/)。不能迁移成 SayHear 的隐私承诺。
- [S24 Dunlosky 等，2013](https://doi.org/10.1177/1529100612453266) 与 [学会摘要](https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html)。学习方法综述，不直接证明本路线的学习成果。
- [S25 Chi 等，1989](https://doi.org/10.1207/s15516709cog1302_1)。示例学习中的自我解释研究，研究任务与软件工程不同。
