# 阶段 0 决策简报：路线、数据与访问边界

状态：已被决定取代（2026-10-22）。本文是决策前的讨论材料，其中“建议 Neon 起点”、地区候选、Harness 与 fallback 的待决定项均已过时。现行决定见 [ADR 0001 至 0005](../../../../decisions.md)，阶段 1 范围见 `stage-1-working-spec.md`。下文保留原样，仅作历史证据。

核验日期：2026-10-21。未调用真实 Provider、未创建数据库、未部署、未读取密钥。本地 mock 已执行，结果见 `docs/plans/stages/stage-0/evidence/stage-0-runtime-validation.md`，本文已按实测结果更新。真实 Provider、Vercel 运行时与数据库仍未验证，这些项保持 unknown，不用文档或本地 mock 代替真实运行结果。

## 证据标记

| 标记 | 含义 |
| --- | --- |
| 已定 | CONTEXT 或已确认计划中的边界，本轮不重开。 |
| 偏好 | Luke 已表达的方向，尚未形成验收。 |
| 建议 | 主 Agent 的判断，需要 Luke 同意才生效。 |
| 待决定 | 只有 Luke 能定。 |
| 待实测 | 文档无法回答，需要运行验证。 |

## 1. Harness 路线

建议 AI SDK 有条件优先。Mastra 是可行替代，支持对象形式的自定义 URL、显式 history 和可选 memory。文档较少或滚动更新不构成淘汰理由，本地 mock 也没有给出排除它的理由。

下表只比较阶段 1 实际要做的工作，证据标记对应本地 mock（`stage-0-runtime-validation.md`）、源码或判断。

| 阶段 1 工作 | AI SDK 7.0.148 | Mastra 1.79.0 | 证据 |
| --- | --- | --- | --- |
| 一次聊天请求与流式 | `streamText` 接 `messages`，无状态；系统提示必须走顶层 `system`/`instructions` | `agent.stream(messages)`，未配置 memory 时不建 thread | 文档、源码、mock |
| 自定义 OpenAI-compatible baseURL | `createOpenAICompatible({ baseURL })` | 对象形式 `{ id, url, apiKey, api }` 可用。字符串路由不携带 baseURL | 源码，mock 已通过 |
| 显式 history 与 thinking | 直接传 `messages`，`providerOptions` 透传 `thinking` | 直接传 `messages`，不传 memory，`thinking` 透传 | 源码，mock 已通过 |
| 可选 memory | 不内置会话存储 | 不配置时不读写。配置后提供 thread 与 working memory | 源码；mock 只确认工作目录无落盘，未检查全局路径 |
| 原始 HTTP 观测 | `include: { requestBody }` 或自定义 `fetch` | 模型 span 不保证 wire body。需自定义 fetch 或 gateway | 文档与源码 |
| 停止 | abort 抛 `AbortError`；`abortSignal` 加 `onAbort` | abort 不抛错，流结束并标记 `status='canceled'`、`finishReason='aborted'`；需读结果状态 | mock 已通过，两边本地连接都关闭 |
| 默认遥测 | 不注册 integration 不外发 | 源码默认开启，默认 host 为 PostHog；需设置 `MASTRA_TELEMETRY_DISABLED=1`。mock 未观测到外发，不能证明实际发送与否 | 源码，mock 有限 |
| 默认步骤与重试 | 裸 `streamText`/`generateText` 默认 1 步；`ToolLoopAgent` 默认 20 步。`maxRetries` 默认 2 | 默认 5 步。源码显示自身重试默认 2，未实测 | 源码；AI SDK 重试与步骤已 mock 实测 |
| 维护面 | 一个 provider 工厂加 messages。编排自己组织 | 集成度高。升级需重核滚动文档与默认值 | 判断 |

取消的边界要说清：本地 mock 只证明两边在 abort 后关闭了本地连接，不证明 Vercel 会传播断开，也不证明 Provider 停止计费。两边也不保证模型对象可以无条件互用；本次没有验证这一点。

阶段 1 只需要一次请求、流式、停止、失败和保存。上下文选择、canonical 保存和运行详情本来就要 SayHear 自己做，采用 Mastra 不会免除这些工作。AI SDK 的显式请求体观测直接服务运行详情和 Harness 学习，这是当前阶段的优势。

Mastra 的集成收益在阶段 2 以后才可能兑现。工具循环、working memory、workflow 与 tracing 是它的强项。若阶段 2 的工具编排、阶段 3 的记忆存储或阶段 4 的后台执行确实复用这些能力，并且不产生第二套 canonical 归属，Mastra 可以减少接线。这是条件收益，不是现在就能记账的节省。

Mastra 成为主线的条件：

- V1 已本地通过：对象形式的自定义 baseURL、thinking 与显式 history 发出正确请求。
- V3 只取得有限证据：关闭 memory 时工作目录无会话落盘，但未检查全局路径。要把它当作“无意外持久化”，需补充全局路径检查或接受这一残留风险。
- 接受显式设置 `MASTRA_TELEMETRY_DISABLED`，并在每次升级后重核 gateway、遥测和步骤默认值。
- 接受取消按结果状态处理，而不是捕获异常。
- 到阶段 2 至 4 时，它的 memory、workflow 或观测能力确实减少实际工作，而不是把状态复制到两处。

记忆与 Reflection 不锁定方案。阶段 3 与阶段 4 用同一批场景比较，四问作为判据。现在选 AI SDK 不排除以后采用 Mastra 的 memory 或 workflow。Mastra 通常能配合 AI SDK 的模型与聊天 UI，但本次没有验证模型对象互换，切换成本主要在编排层，具体兼容性需按版本核实。

本地 mock 已返回：V1 通过；V2 的 abort 形态与 AI SDK 重试通过，Mastra 默认重试仍只有源码证据；V3 有限通过。这些结果不构成任何一方的排除理由，也不足以单独宣布阶段 0 通过。不需要为此再安排额外实验；若 Luke 接受残留风险，可直接进入路线讨论。

需要 Luke 决定：路线选择。选项是接受条件推荐、现在选 Mastra，或要求补充验证。推荐 AI SDK，理由是阶段 1 需要的请求观测、取消与无默认产品遥测更直接；同时承认 Mastra 在本地 mock 中同样可行。

## 2. 数据库、地区与费用

当前只需要 Postgres 时，建议从 Neon 开始。免费层有 1 GB 存储和 6 小时恢复窗口。Launch 按用量计费，没有月最低。它提供 pooler 连接串。代价是免费实例 5 分钟无活动挂起，首请求有冷启动，恢复窗口只有 6 小时。

Supabase 的集成收益只在采用它的 Auth、RLS、Storage 等能力时成立。若只把它当 Postgres，免费层没有平台备份，暂停后需手动恢复，Pro 组织起价 25 美元每月。是否值得取决于登录方案，不取决于数据库功能。

地区候选。本文只给延迟和辖区组合，不替 Luke 决定司法辖区。

| 候选 | 函数地区 | 数据库地区 | 收益 | 代价 |
| --- | --- | --- | --- | --- |
| A | `iad1`，Vercel 默认 | Neon `us-east-1`，弗吉尼亚 | 函数与库同区，往返延迟最低 | 数据存放在美国 |
| B | `sin1` | Neon `ap-southeast-1`，新加坡 | 数据在亚洲，接近亚洲访问位置 | 延迟取决于实际用户位置。需确认套餐允许固定函数地区 |

项目创建后数据库地区不可改，迁移需要新建项目。地区同时决定司法辖区和函数到数据库的往返延迟，不能只看延迟。

费用边界：Luke 说暂不设 API 月预算，这句话只覆盖模型调用。云资源仍会产生费用或触达免费层限制。阶段 1 可能涉及 Vercel 套餐、数据库付费层、域名和备份。建议先定可接受的月度上限和超限后的处理，不现在估算总额。

需要 Luke 决定：数据库供应商、地区与司法辖区、云费用接受范围。三项可以合并成一次讨论。

## 3. 访问与体验

已定：初期真实用户只有 Luke。旧 Portal 的聊天布局、消息展示、输入、流式反馈和响应式交互复用。数据契约、鉴权、运行详情和 Journal 入口重写。

登录：应用需要自己的会话，识别 owner 并绑定数据。部署入口保护只决定能不能进来，不告诉应用是谁。GitHub 对 Luke 方便，对未来的普通用户不合适。邮箱魔法链接更通用，配置更多。Supabase Auth 只在选 Supabase 时省一步，但把身份数据绑在同一供应商。工程建议是 Auth.js 加数据库会话，先只允许 Luke 的账号。需要 Luke 决定登录体验。

部分输出：建议停止后保留只读的部分内容，标记为中断。重试创建新 run，不覆盖旧内容。需要 Luke 确认这个体验。

Fallback：方向已经明确，OpenCode Go 为主，DeepSeek 官方为备用，不需要重新授权。自动切换策略尚未同意。建议只在首个可见输出之前切换一次。已有输出后只标中断。认证、余额、请求格式错误和已经切换过一次的情况不切换。切换是否向用户提示，需要 Luke 决定。

## 4. 真实内容外送边界

首次发送真实私人内容前必须确认以下事项。Go 的 ZDR 当前有效期到 2026-10-31，是否续期未知。Go 文档面向编码 agent，非编码私人应用是否允许未知。DeepSeek 官方 API 的训练与保留条款未知。两条路线的实际错误形状和额度用尽行为未实测。

需要 Luke 决定：哪些路线可以接收真实私人内容。选项是先只用合成内容，允许真实内容并记录 unknown，或只允许其中一条路线接收真实内容。建议先用合成内容完成阶段 1 验收，首次真实内容前再核对条款。

无论选哪项，运行记录和日志的边界不变。不打印正文。不注册记录输入输出的遥测。不把私人原文复制进仓库、测试集或外部追踪。

## 5. 状态汇总

| 类别 | 内容 |
| --- | --- |
| 已定 | Vercel 部署。两库隔离。初期 Luke 自用。Portal 聊天体验复用。先对话与 canonical，再记忆与 Reflection。 |
| 偏好 | OpenCode Go 主路径，DeepSeek 官方 fallback。暂不设 API 月预算。 |
| 建议 | AI SDK 有条件优先；Mastra 本地 mock 同样可行。Neon 作为只需 PG 的起点。应用层鉴权加数据库会话。首个可见输出前最多切换一次。60 秒服务端预算与 62 秒客户端截止作为待测起点。不注册遥测集成。 |
| 未采纳 | 因 Mastra 文档较少直接排除。因 AI SDK 优先就锁定记忆与 Reflection。把无 API 预算理解为云预算无限。照搬旧 endpoint、事件协议或 Daily Session。按功能清单长短选型。把本地连接关闭当作停计费。把工作目录无落盘当作全局无存储。把遥测源码默认值写成已实际发送。 |
| 待决定 | 路线选择。数据库、地区与云费用。登录体验。部分输出与 fallback 体验。真实内容外送边界。 |
| 待实测 | 真实 Provider 调用。Vercel 断开后的取消传播与停计费。Mastra 默认重试实测。Mastra 全局路径落盘检查。部分输出落库。Portal 适配工作量。60 秒与 62 秒预算。 |

## 6. 工程侧实现建议

以下由工程侧提出，不要求 Luke 逐项拍板。Luke 可以否决或要求解释。

- 两个 Provider 身份，不做一个可换 baseURL 的配置。endpoint、模型 ID、ZDR、额度和错误形状都不同。
- 记录每次返回的 `model`，不把 alias 当成稳定快照。
- 错误映射：401 认证，422 配置，429 限流，500 与 503 不可用，超时，截断或协议不完整。402 单独显示，不归入配置错误。
- `reasoning_content` 只在同一次运行的内存中回传，不写入 canonical，不在运行详情展示。
- 阶段 1 设 `maxRetries: 0`，由应用显式控制尝试次数，避免 SDK 重试与 fallback 叠加。
- 函数使用池化连接串，迁移使用直连串。
- 应用层拒绝未认证请求。Vercel Authentication 作为可选的第二层。
- 测试库护栏与验收记录格式由工程实现，在 working spec 中写清。

## 7. 阶段 0 剩余

按主题推进，不预设固定轮次或时长。每组形成结论后记录，再进入下一组；可以合并讨论，也可以按 Luke 的时间拆开。

| 剩余事项 | 需要的结果 | 状态 |
| --- | --- | --- |
| Harness 路线共识 | 接受 AI SDK 条件推荐、选 Mastra，或说明还需哪项证据 | 待讨论，mock 已返回 |
| 数据与访问选择 | 数据库供应商、地区、云费用范围；登录身份源；部分输出与 fallback 体验；真实内容外送边界 | 待讨论 |
| 必要真实调用 | 凭据就绪后核实两条 Provider 的 endpoint、模型、错误形状与额度行为 | 待凭据，不阻塞其他事项 |
| 一小时示范 | 用一个真实或合成请求演示输入、调用、流输出与保存；保存可用一次性脚本，不做产品持久化 | 待执行 |
| ADR | 记录已采纳路线、理由、未选项与残留 unknown | 待共识后编写 |

阶段 0 的通过条件是：上述路线与边界形成共识，working spec 获认可，一小时示范完成，Luke 能用自己的话说明各层责任，且相关 ADR 已记录。验收不只看讨论完成或 mock 结果，也不因它们完成就宣布阶段 0 已通过。阶段 1 的开始时间取决于阶段 0 是否通过；阶段 2 的时机取决于阶段 1 验收，不在现在排定。

## 8. 相关文档

- 运行层证据：`docs/plans/stages/stage-0/evidence/stage-0-runtime-evidence.md`
- Provider 证据：`docs/plans/stages/stage-0/evidence/stage-0-provider-evidence.md`
- 数据与交付证据：`docs/plans/stages/stage-0/evidence/stage-0-data-and-delivery-evidence.md`
- 阶段启动清单：`.audit/stages/stage-0/sayhear-stage-0-start.todo.md`
- 阶段 1 working spec 草案：`docs/plans/stages/stage-1/spec.md`
- 计划与共识：`docs/plans/roadmap/sayhear-build-and-learning-plan.md`，`CONTEXT.md`

决定达成后写 ADR。ADR 记录选择、理由、未选项和待实测项，不把建议写成已验收结果。
