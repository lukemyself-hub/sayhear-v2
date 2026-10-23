# 阶段 0：数据、部署与 Portal 证据

状态为 Draft，供主会话集中决策。核验日期：2026-10-21。本文只记录证据、条件与建议，不表示阶段 0 已通过，也不表示任何路线已被采纳。

## 范围与限制

本文回答四组问题：托管 Postgres 的候选差异，Vercel 的运行时与访问约束，旧 Portal 哪些能复用，以及合成数据与阶段 1 working spec 的责任和提纲。

本次没有创建云资源、连接任何数据库、读取凭据、部署、调用 Provider 或联系外部人员。所有平台事实来自官方文档，价格与额度以核验日期为准，采用前需按实际套餐再核对。旧 Portal 只做只读定位，没有运行浏览器对比，也没有迁移代码。

研究问题与既有路线研究重叠时，本文以官方页面重新核对，并在表格中标注日期。旧仓库的调查结论只在 Portal 一节复用。

## 证据分级

全文使用五个标签，避免把建议读成决定。

| 标签 | 含义 |
| --- | --- |
| 已定 | `CONTEXT.md` 与已确认计划中的产品边界，本轮不重开。 |
| 偏好 | Luke 已表达的方向，但未形成验收或 ADR。 |
| 建议 | 本文基于证据的判断，需要 Luke 同意才生效。 |
| 待决定 | 只有 Luke 能定，主要是地区、费用与访问方式。 |
| 待实测 | 文档无法回答，需要在阶段 1 用真实运行验证。 |

已定边界中与本文直接相关的有五条：Web 部署到 Vercel；测试库与用户库是两个隔离实例；最初用户是 Luke；初期具备基本访问控制、内容查看与清理，并兼容未来多用户；复用旧 Portal 的聊天布局与交互。是否邀请 Luke 以外的人访问留到后续阶段，不是阶段 0 的当前问题。

## 托管 Postgres：Supabase 与 Neon

### 免费与最低收费边界

| 项目 | Supabase | Neon |
| --- | --- | --- |
| 免费库容量 | 500 MB 每项目 | 1 GB 每项目，账户合计 20 GB |
| 免费计算 | 未在定价页单列 | 100 CU-hours 每项目，自动扩缩上限 2 CU |
| 免费实例空闲行为 | 1 周无活动后暂停，免费额度允许 2 个活跃项目 | 5 分钟无活动后挂起，免费计划不能关闭 |
| 免费备份 | 不包含，官方建议用 CLI 导出并另存 | 6 小时恢复窗口，单次恢复上限 1 GB |
| 最低付费 | 组织 Pro 起价 $25/月，含组织合计 $10 计算额度，可覆盖一个 Micro 实例；两个 Pro Micro 的基线约 $35/月，第二个实例不免费 | Launch 按用量计费，无月最低；计算 $0.106/CU-hour |
| 付费备份 | Pro 每日备份保留 7 天；PITR 为附加项，7 天约 $100/月，且需至少 Small 计算 | Launch 恢复窗口最长 7 天，Scale 最长 30 天；快照存储 $0.09/GB-month |

来源：Supabase 定价页与备份文档、Neon 定价页与备份文档，均核验于 2026-10-21。

两家的免费层含义不同。Supabase 免费层在暂停后需要手动恢复，且没有平台备份。Neon 免费层会频繁挂起，但有 6 小时恢复窗口，代价是冷启动。若初期只由 Luke 使用，两者的免费额度都够存文本对话；差别在恢复能力和暂停后的体验。

Supabase 的费用按组织计算，不按单个项目。免费测试项目能否与付费用户项目放在同一组织，取决于账户当时的套餐规则，本文不假设同一组织可以混用免费与 Pro 项目。是否单独建免费组织，需要按实际账户确认。

### 地区

Neon 固定八个 AWS 地区：弗吉尼亚、俄亥俄、俄勒冈、法兰克福、伦敦、新加坡、悉尼、圣保罗。项目创建后地区不可改，迁移需要新建项目。

Supabase 分为“通用地区”和“具体地区”。通用地区只有三个选项：East US（北弗吉尼亚）、Central EU（法兰克福）、Southeast Asia（新加坡），官方说明其实际落点可能超出名称范围，例如通用欧洲可能落在伦敦或苏黎世。需要明确司法辖区时应选具体地区，具体地区包括北加州、俄勒冈、弗吉尼亚、俄亥俄、加拿大中部、爱尔兰、伦敦、巴黎、法兰克福、苏黎世、斯德哥尔摩、孟买、新加坡、东京、首尔、悉尼、圣保罗。

地区影响两件事：数据存放的司法辖区，以及函数到数据库的往返延迟。Vercel 函数默认在 `iad1`，可改单一地区；Pro 才可配置多地区。建议让数据库地区与函数地区一致，但这需要 Luke 先定地区。

### 连接方式

Supabase 有三条路径。直连走 5432，默认 IPv6，IPv4 需要附加项。Supavisor 会话模式走 5432，适合 IPv4 网络并保留会话状态。Supavisor 事务模式走 6543，官方推荐给 Serverless 和 Edge，但不支持预处理语句与会话状态，并建议客户端连接池设为 1。

Neon 提供直连与带 `-pooler` 的连接串，池化使用 PgBouncer 事务模式。迁移、`pg_dump`、`pg_restore` 和逻辑复制应走直连。事务池不支持 `SET`、`LISTEN`、`NOTIFY` 和 SQL 级 `PREPARE`。

两家的共同结论是：Serverless 函数使用池化连接串，应用侧保持小连接池，迁移脚本使用直连串。这属于实现细节，不改变产品定义。

### Vercel 连接

Vercel Postgres 已停止提供，旧库在 2024 年 12 月迁到 Neon。新项目通过 Marketplace 安装 Postgres 集成，由集成向项目注入连接环境变量。两家都可用这种方式接入，也可以手动配置环境变量。

旧仓库使用的是 Neon，`.env.neon` 作为独立 profile，备份策略版本记录为 `neon-free-6h-pitr-1gb-limit`。这说明旧项目实际跑过免费层的恢复边界，但不构成 v2 的选择理由。

### 建议与条件

建议一：两家都能满足阶段 1。选择条件不取决于功能清单，而取决于三件事。

- 若优先“免费层也能恢复”，选 Neon。6 小时恢复窗口让一次误删可以在当天回滚，代价是频繁挂起带来的首请求延迟。
- 若优先“少配一个认证系统、未来可能用托管 Auth”，选 Supabase。代价是免费层无备份、暂停后需手动恢复，且完整 Postgres 的 Auth 与 RLS 会把一部分权限逻辑放进数据库。
- 若优先“按量付费、无月最低”，选 Neon Launch。它在免费层之外没有固定月费，适合用量不确定的初期。

建议二：无论选哪家，测试库与用户库都用独立项目，不复用同一实例的 schema 隔离。分支或复制生产数据不能充当测试集，这一点与 `CONTEXT.md` 一致。

建议三：v2 的访问控制先放在应用层，不把 RLS 作为唯一防线。这样换数据库时不重写权限模型。

地区、套餐与月费留给 Luke 决定。本文不推荐具体地区，也不假设某个套餐可以长期免费。

## Vercel 平台约束

### 函数时长与流式

Fluid compute 默认开启。Hobby 的默认值和上限都是 300 秒。Pro 默认 300 秒，可配到 800 秒，30 分钟的扩展上限仍在 Beta，且要求按函数配置。Edge runtime 必须在 25 秒内开始响应，之后最多流式 300 秒。

函数时长包含发送流式响应的时间，不是“首字节前”的预算。函数超过时长会返回 504 与 `FUNCTION_INVOCATION_TIMEOUT`。请求与响应体上限为 4.5 MB，对文本聊天足够，但不能用来传音频或大文件。

建议阶段 1 把服务端预算设在 60 秒左右，并在应用层显式结束，而不是依赖平台 300 秒兜底。旧 Portal 曾采用服务端 60 秒预算、客户端 62 秒截止，多出的 2 秒用于先收到服务端的终止事件。这两个数字只是待测起点，不继承旧项目的承诺，阶段 1 需要按真实 Provider 的时延重新验证。

### 客户端断开与取消传播

Vercel 官方文档没有说明客户端断开后函数是否立即停止。流式文档只说明流式默认开启、时长上限如何配置，没有给出取消语义。

可以确认的是 SDK 侧的能力。AI SDK 的 `streamText` 接受 `abortSignal`，中止时流会发出 `abort` 部分，`onAbort` 收到已完成的步骤。是否把浏览器的 `request.signal` 接到 `streamText`，以及 Vercel 在客户端断开时是否触发该信号，文档未给出结论。

旧 Portal 的做法是自建传播，不依赖平台：响应流是 `ReadableStream`，`cancel()` 里调用 `AbortController.abort()`，服务端预算到点也主动 abort 并发出终止事件。这套模式可以照搬到 v2，但需要实测确认在 Vercel 上断开时 `cancel()` 会被调用。

待实测项：

- 浏览器停止后，服务端是否在数秒内收到 abort。
- 直接关闭标签页时，函数是否继续消耗时长。
- 中止后已生成的文本能否落库为“部分输出”，还是只剩失败状态。

### 私密部署与访问套餐

Vercel Authentication 在所有套餐可用。Hobby 也能用它保护 All Deployments，包括生产部署和绑定的自定义域名，官方 changelog 明确写明生产部署保护已在所有套餐免费提供。

Deployment Protection Exceptions 和 Shareable Links 不是保护方式。两者用于让指定访问绕过保护，属于例外通道，不能算作访问控制。开启后，任何拿到 Shareable Link 的人都能进入。

Password Protection 不在 Hobby 提供。Pro 按每个受保护项目 $20/月收费。Trusted IPs 与 Passport 只在 Enterprise 提供。Hobby 的公平使用条款限定为非商业、个人用途，超出额度通常要等 30 天恢复。Hobby 可以批准一个外部 Vercel 用户访问受保护部署，这是 Vercel 账号层面的访客，不是团队成员。

Vercel Authentication 不是唯一满足私密部署的路径。应用鉴权拒绝未认证的聊天页面和 API 读写，也能满足“未认证请求被拒绝”。两者的差别在拦截位置：应用鉴权只拦应用处理的请求，静态资源仍可能直接返回；若要求所有静态资源在到达应用前就被拦住，才需要部署入口保护。阶段 1 至少在应用层拒绝未认证请求；是否再加部署入口保护属于建议，等 Luke 决定。

Vercel Authentication 不是应用鉴权。它保护整站入口，但不告诉应用“这次请求是哪个用户”，也不能按用户隔离数据。产品仍需自己的会话与用户身份。

### 日志与遥测是否携带内容

运行时日志会保存 `console.log` 输出，按请求分组。Hobby 保留 1 小时，Pro 保留 1 天，Observability Plus 可到 30 天。单请求上限为 256 行、1 MB。日志详情包含请求路径、查询参数、User Agent、地区、状态码与耗时。官方页面没有说明默认记录请求体或响应体。

因此风险主要来自应用自己的日志语句，而不是平台默认采集。建议规定：不打印消息正文、模型输入输出或 Provider 原始响应；错误日志只记录类别、状态码、请求 ID 与长度。

AI SDK 的遥测需要注意。官方文档说明，注册遥测集成后，支持的调用默认发出遥测事件，并默认记录输入与输出。未注册集成时不发送遥测。注册后可以用 `isEnabled: false` 整体关闭，或用 `recordInputs: false` 和 `recordOutputs: false` 关闭输入输出记录。这属于“默认可能携带内容”的项。阶段 1 不注册遥测集成即可规避；若以后接入，必须先显式关闭输入输出记录。

Supabase 与 Neon 的平台日志、备份和数据保留条款本次未逐条核对，列为缺口，不扩大为警告。

## 应用鉴权方案

需要两层，职责不同。

| 层 | 作用 | 候选 | 阶段 1 建议 |
| --- | --- | --- | --- |
| 部署入口 | 未授权请求在到达应用前被拒 | Vercel Authentication（全套餐）；Password Protection（Pro）；Trusted IPs（Enterprise） | 建议用 Vercel Authentication 保护所有部署；应用鉴权拒绝未认证的聊天页面与 API 读写，同样能满足访问控制。 |
| 应用会话 | 识别用户、绑定数据归属、支持未来多用户 | Auth.js（旧项目用 NextAuth 4 + GitHub）；Supabase Auth；自建邮箱魔法链接 | 建议用 Auth.js 加一个可用身份源，会话存数据库。 |

理由：部署入口决定“能不能进来”，应用会话决定“以谁的身份读写”。两者混用会让产品身份绑在 Vercel 账号上，而 Vercel 账号不等于产品账号。Supabase Auth 只在选 Supabase 且愿意把用户表交给它时更省事，但会把身份数据与业务数据绑在同一供应商。

待决定：应用登录用哪个身份源。GitHub 对 Luke 方便，但对未来的普通用户不合适。这个选择不阻塞阶段 1，可以先只允许 Luke 的账号。

## 旧 Portal 的复用边界

调查对象为 `/Users/lukemyself/Projects/SayHear/apps/web/app/internal/`，共约 9,200 行，另有 `apps/web/src/` 下的请求处理器与 `app/styles.css` 中的外壳样式。只读定位，未运行。

### 已定的复用范围

复用旧 Portal 的聊天 UI 与交互已由 `CONTEXT.md` 确定，包括布局、消息展示、输入、流式反馈和响应式适配。本节记录这些体验资产在旧代码中的位置，不再作为偏好列出。

- 外壳结构：`portal-shell.tsx` 与 `styles.css` 的 `.portalShell` 一组。固定头部、72px 图标栏、320px 模块列、内容区，`100dvh` 加安全区适配。
- 响应式：`1024px` 断点。窄屏时导航变为抽屉，带遮罩、Escape 关闭、焦点回到触发按钮；宽屏时两列常驻，可折叠。
- 会话与日期导航：`chat-module-list.tsx` 用游标分页加载更早日期，`aria-current` 标记当前项，空列表时回落到“今天”。
- 草稿：外壳上下文按 key 保存草稿，不写浏览器存储。这个约束值得保留。
- 消息呈现：`message-time.tsx` 把时间放在预留的元信息行，悬停、键盘聚焦或触屏点击时显示，不引起布局跳动；助手消息旁有进入运行详情的图标。
- 输入与流式反馈：`text-conversation.tsx` 与 `text-conversation-state.ts`。包含 IME 组合输入处理、Enter 发送与 Shift+Enter 换行、输入框自增高到 200px、等待三点只在用户消息确认后出现、单一礼貌播报、滚动跟随阈值 48px 与“回到最新”、停止按钮、失败后显式重试、离开页面前提醒。
- 失败状态模型：等待阶段 `idle → submitting → awaiting → streaming → settled/stopped/failed`；提交失败按“确认前、确认后、中断、未知”四种情况分别处理，不静默重发。
- 可访问性：`role="status"` 的单一播报通道、错误 `role="alert"` 并移焦、焦点可见样式、`prefers-reduced-motion` 降级。

这些是已定复用的体验资产。建议按 v2 契约重写容器后复用结构与样式，不直接搬运组件。

### 必须重做的契约

- 事件协议：旧协议为 NDJSON，事件类型包括 `user_committed`、`assistant_delta`、`assistant_committed`、`response_interrupted`、`response_failed`、`action_admitted`。字段含 `turnId`、`generationCommandId`、`revisionId`、`sequence`、`logicalDate`。v2 的 canonical 数据未定，这些字段不能默认继承。
- 会话模型：旧系统以 Daily Session 和逻辑日期组织对话，跨午夜有专门处理。v2 是否沿用按日会话，是产品体验问题，需要在阶段 1 明确。
- 鉴权与写入门禁：旧项目用 NextAuth 4 的 GitHub 登录、数据库会话、内部 owner 校验，以及一个“恢复门禁关闭时禁止写入”的状态。v2 需要自己的身份与门禁，不复用这套语义。
- 运行详情：旧的 Context Inspector 有 1,255 行，Reflection Inspector 有 1,921 行，带 `generation_command_id` 深链。v2 只做最小版本，展示实际模型输入、所选历史、模型与失败位置，不迁入整套检查器。
- Journal 模块：入口、动作回执与重新生成文案都在外壳里。v2 阶段 1 不实现 Journal，需要从导航中移除，而不是保留空入口。
- 文案与语言：旧界面中英混排，错误文案是英文，按钮是中文。v2 需要统一的文案策略。
- 样式耦合：CSS 类名与旧组件一一对应，直接复制会带上 Journal 与检查工具的布局假设。

### 复用判断

布局、导航、消息呈现、输入与流式交互、失败状态模型和响应式行为属于已定复用范围。数据契约、鉴权、运行详情与 Journal 相关部分需要重写。工作量只能估算，不能宣称迁移已验证。

## 合成数据与验收责任

### 分工

编写 Agent（后台）：按数据集规格生成版本化文件，使用虚构人物与场景，不引用 Luke 的真实对话。每条数据带稳定 ID、时间、参与者与场景标签，保证可重复装载。生成后自检字段完整性与覆盖清单。

Luke：审阅体验。抽取若干段对话阅读，判断是否像真实交流、人物关系是否清楚、敏感细节是否必要且不冒犯。这一步是体验判断，不是逐条校对，也不构成入仓审批。

主 Agent：协调验收。定义验收证据格式，检查覆盖清单与隔离验证结果，确认每次数据集变更后重跑了检查。脚本实现交给 builder 执行，主 Agent 不直接编写。

数据集与记忆实现分开估算，避免阶段 3 因数据未就绪而滑期。

### 最低覆盖

阶段 0 要求覆盖：多日交流、人物关系、偏好变化、否定、同名人物、无答案场景、无关敏感细节、恶意历史指令。

阶段 1 追加：一条合成系统消息、一条工具调用与结果、一次中断的部分输出、可清理的单条内容、两个可辨识的合成主体用于隔离测试、跨午夜与不同时区的记录。

每条覆盖项都要有可执行的检查方式，例如按标签计数、按主体查询、故意越权读取必须失败。仅“数据里写了”不算覆盖。

### 验收证据格式

沿用计划中的字段：场景编号、输入、期望行为、实际输出或运行链接、模型与 prompt、persona、上下文策略版本、数据集版本、结论与 commit。阶段 1 需要确定执行方式是脚本还是手动，并让新运行可以按记录回放。

## 阶段 1 working spec 提纲

以下是提纲，不是已完成的 spec。每节标注决策类别。

1. 目标与非目标（已定）。可在线聊天、保存历史、解释输入、流式与失败可见。不含记忆、Reflection、Journal、语音、完整多用户。
2. 用户与访问（已定，方式待决定）。最初用户是 Luke。是否邀请其他人访问留到后续阶段，不作为当前必须回答的问题。部署入口保护为建议，应用会话识别 Luke。
3. 运行链路（建议，两个占位分支）。浏览器 → Next.js Route Handler → Harness → Provider → 流式事件 → 浏览器渲染 → 落库。Harness 分支一为 AI SDK `streamText`，分支二为 Mastra。最终选择待阶段 0 共识与 ADR。每段的责任在验收时要能用一次真实请求说明。
4. Provider 路径（偏好）。OpenCode Go 为主，DeepSeek 官方为备用。接入前核实协议、模型名、流式、停止与错误格式。暂不设 API 月预算上限，但非所有服务预算无限，需记录单次成本。
5. 流式、停止与失败（建议）。服务端预算 60 秒、客户端 62 秒只是待测起点，需按真实 Provider 重新验证；停止与“新消息替换旧回答”分开处理；部分输出只读展示并可显式重试；确认前后的失败分开处理。
6. canonical 最小语义（已定边界，形状待定）。用户输入、生成内容、系统与人设指令、工具调用、工具结果、中断产物都要有位置。阶段 1 不固定表结构，但合成系统消息与工具调用要能保存、检索并显示。
7. 运行详情最小版本（建议）。显示实际模型输入、所选历史、模型、失败位置。不展示未获得的内部推理。
8. 数据隔离与护栏（已有文档约束，实现待定）。两个独立实例，`TEST_DATABASE_URL` 与 `DATABASE_URL` 不交叉；测试环境不注入生产凭据；做一次故意交叉连接验证。环境变量名已记录在 `docs/agents/local-environment.md`，交叉连接护栏已由阶段 1 计划要求。具体实现方式待定。
9. 清理契约（已定范围，细节待决定）。至少支持单条清理与整账户清理；清理后不再进入当前上下文；说明平台日志、备份与 Provider 侧内容可能仍存在。
10. 部署与配置（建议）。Vercel 项目、环境变量、干净环境部署 smoke test；日志不含正文；不注册会记录输入输出的遥测。
11. 数据集 v0（建议）。按上节覆盖清单交付，带版本与装载脚本。
12. 验收证据与回放（待决定执行方式）。字段见上节。
13. 未决问题。取消后的部分内容如何保存、历史如何分组、登录方式、错误展示方式、数据地区与套餐。

## 未决问题与缺口

- 地区与套餐：由 Luke 决定，本文不推荐。地区影响延迟与司法辖区，套餐影响备份与费用。
- 数据条款：Supabase、Neon、Vercel 的子处理者、日志保留与备份加密未逐条核对。AI SDK 遥测默认记录输入输出的行为已确认，是否接入未定。
- 客户端断开的平台语义：官方文档未说明，列为阶段 1 实测。
- 旧 Portal 的迁移工作量：未运行对比，只能估算。
- Supabase 免费测试项目能否与 Pro 项目同组织：需要按实际账户确认。

缺口是有限的，不需要为每一项再开子调查阻塞阶段 0。以下是最低核实范围，必须在首次写入真实用户数据前完成，其余缺口可随阶段 1 实现补齐：

- 选定数据库套餐后，核对备份与恢复边界，并确认测试项目与用户项目是否在同一组织。
- 选定部署保护方式后，用一次未认证请求验证生产 URL 的实际行为。
- 接入 AI SDK 遥测前，确认关闭输入输出记录的具体配置。
- 首次调用 Provider 前，确认发送给 Provider 的内容范围。

已完成研究但尚未决策的项：数据库供应商、地区与套餐；部署入口保护方式；应用登录身份源；Harness 在 AI SDK 与 Mastra 之间的选择。尚未实测的项：客户端断开后的服务端行为、中止后部分输出能否落库、旧 Portal 适配工作量、60 秒与 62 秒预算在真实 Provider 下的表现。

## 来源

核验于 2026-10-21。

- Supabase 定价：https://supabase.com/pricing
- Supabase 备份：https://supabase.com/docs/guides/platform/backups
- Supabase 地区：https://supabase.com/docs/guides/platform/regions
- Supabase 连接：https://supabase.com/docs/guides/database/connecting-to-postgres
- Neon 定价：https://neon.com/pricing
- Neon 备份与恢复：https://neon.com/docs/guides/backup-restore
- Neon 地区：https://neon.com/docs/introduction/regions
- Neon 连接池：https://neon.com/docs/connect/connection-pooling
- Vercel 函数时长：https://vercel.com/docs/functions/configuring-functions/duration
- Vercel 函数限制：https://vercel.com/docs/functions/limitations
- Vercel 流式：https://vercel.com/docs/functions/streaming-functions
- Vercel 部署保护：https://vercel.com/docs/deployment-protection
- Vercel Authentication：https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication
- Vercel 生产部署保护对所有套餐免费：https://vercel.com/changelog/protect-production-deployments-for-free-on-every-plan
- Vercel Hobby 套餐：https://vercel.com/docs/plans/hobby
- Vercel 运行时日志：https://vercel.com/docs/logs/runtime
- Vercel Postgres 与 Marketplace：https://vercel.com/docs/postgres
- AI SDK `streamText`：https://ai-sdk.dev/docs/reference/ai-sdk-core/stream-text
- AI SDK 遥测：https://ai-sdk.dev/docs/ai-sdk-core/telemetry
- 旧 Portal：`/Users/lukemyself/Projects/SayHear/apps/web/app/internal/`，`apps/web/src/ndjson-response.ts`，`apps/web/app/styles.css`
