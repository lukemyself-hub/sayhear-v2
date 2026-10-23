# 阶段 0 主会话接续

更新日期：2026-10-22。来源为本会话 Luke 的指示、CONTEXT.md 与所链接证据。阶段 0 已正式启动，尚未验收通过。

## 当前目标与授权

Luke 要求主会话负责协调、讨论、学习与关键决定，有明确边界的任务交后台 agent。已明确要求持续完成必要调研与方案整理，证据足够且需要产品判断时再集中讨论。未授权提交、推送、创建云资源或部署。

当前进入阶段 0 收尾。已接受 AI SDK、Supabase 两库 Free、美国东部部署、邮箱密码、自建简洁运行记录及可替换 fallback，权威决定见 ADR 0001–0005。下方按轮次保存历史记录，旧推荐与待决定状态不代表当前状态。无活跃后台调研。

核对主计划发现：“不超过约 1 小时”是合成请求示范的时间盒，不是必须运行一小时的负载测试。之前多次称其为“一小时示范”不准确。已有请求输入、流输出和脱敏 JSON 保存证据可用于讲解，不需为了时长增加调用。尚需完成学习回访与正式 SPEC 交接，不能把文件完成视为阶段通过。

## 已定、偏好与推荐

- 既有共识：Vercel Web、最初用户 Luke、两个隔离数据库、基本访问与清理、复用旧 Portal 聊天体验。参见 CONTEXT.md。
- Luke 偏好：OpenCode Go 主 Provider，DeepSeek 官方 API fallback，目标 DeepSeek V4.1 Flash，暂不设 API 月预算。自动切换行为尚未决定。
- 运行框架推荐 AI SDK，Mastra 可行；本地 mock 已完成，未获最终选型共识。参见 stage-0-runtime-validation.md。
- 早先基于“只需 Postgres”推荐 Neon 不是已接受决定，须由本轮完整平台比较重新评估。

## 当前证据与计划

1. Neon 研究已落盘于 neon-platform-research.md。关键反方复核在 database-auth-critical-check.md。整合时必须修正原研究的组织计费、恢复窗口不等于 RPO、无 GitHub Releases 不代表维护差、MAU 不等于计算负载等问题。
2. 首个 Supabase 调查 agent 超时无产物，已明确停止。替代定点调查已完成 supabase-platform-research.md。主会话直接核实删除用户、改邮箱、密码找回、MAU 定义和备份边界。Supabase 主 JS SDK 为稳定发布，但 SSR 辅助包官方仍标 beta，不使用“全部稳定”的比较。
3. 主 Agent 已形成 Supabase + Supabase Auth 的长期推荐，分析整理在 database-auth-long-term-comparison.md。已建立 Proposed ADR 0001 并登记索引，尚未获 Luke 同意。理由是完整账号生命周期与当前明确的功能边界，代价包括 PITR 费用、SSR beta 和身份迁移耦合；Neon 的恢复与按量成本优势保留。
4. 集中决定后更新阶段 1 working spec 与 ADR；真实调用、恢复演练、部署仍未执行。

## 活跃委派

- 平台比较与证据整合已完成。最终报告为 docs/plans/stages/stage-0/evidence/database-auth-long-term-comparison.md，Proposed ADR 为 docs/adr/0001-database-and-managed-auth.md。
- 2026-10-22 接续会话启动两项后台调研（general-purpose agent；delegate-claude 读者角色无网络，不适合网页调研）：
  - Provider 条款：Go ZDR 续期、Go 非编码用途许可、DeepSeek 官方 API 训练与保留。产物 docs/plans/stages/stage-0/evidence/stage-0-provider-terms-evidence.md。
  - 恢复与地区：Supabase 无 PITR 时的实际 RPO、自建 dump 替代、PITR 现价、Free 暂停规则、亚洲地区与 Vercel 函数地区配对。产物 docs/plans/stages/stage-0/evidence/database-recovery-and-region-evidence.md。
- 主会话同时向 Luke 讲解 RPO，并收集恢复目标与费用偏好（偏好由 Luke 定，成本映射等调研结果）。

## Luke 本次回答（2026-10-22）

- 恢复目标：最多接受丢失约 1 天数据（RPO ≈ 24h）。
- 费用：初期测试库与用户库都放 Supabase Free 层；接受闲置一周暂停，手动恢复。
- 用户地区：最初用户在中国大陆与欧美两地；初期不上架商店，仅小范围内测。
- 恢复调研已回（database-recovery-and-region-evidence.md）。主会话直接核实 CLI 文档：`db dump` 默认排除 auth、storage 与扩展 schema（原文 "The ignored schemas include auth, storage, and those created by extensions."），但 `db dump` 有 `-s, --schema` 包含指定 schema 的参数；用它导出 auth 数据并恢复是推断，须演练。Free 层无平台备份，Pro 每日备份不可下载、整项目恢复，PITR 价格与前置条件与旧文档一致。
- Provider 条款调研已回（stage-0-provider-terms-evidence.md）。主会话直接核实 OpenCode ToS（生效 2026-08-15）："You will only use the Services for your own internal use, and not on behalf of or for the benefit of any third party"。推断：Luke 本人使用可行；向其他内测用户提供服务与该条冲突，需 Luke 重评主 Provider 或内测阶段的 Provider 方案。Go ZDR 仍到 2026-10-31，无续期公告；DeepSeek 官方 API 允许衍生产品开发，但训练/保留 unknown、数据存中国境内、无 ZDR/DPA。
- 地区与可达性调研已回（stage-0-region-and-reachability-evidence.md）。主会话核实 Vercel 大陆指南：无大陆节点，`.vercel.app` 可被阻断，自定义域名"less likely to be flagged"但不保证，不建议前置代理，境内托管需 ICP。Supabase Free 不能用 custom domain，故浏览器不直连 supabase.co 只能靠服务端访问。PIPL 小规模（<10 万人）豁免跨境三机制，但单独同意与影响评估仍适用（推断）；Supabase DPA 含 SCC，Free 可否签 unknown。
- 主 Agent 整合提案（待 Luke 确认）：Supabase Free ×2 + 用户库每日加密 dump（含 auth schema）+ 恢复演练；Vercel hnd1 + Supabase 东京；自定义域名、浏览器只访问自有域名；Go 仅供 Luke 本人，邀请内测前重选 Provider 并完成同意与隐私告知；邀请内测时用户库升 Pro。
- 原待核：Free 层是否有可恢复备份（若无，RPO 24h 需自建每日 dump）；大陆访问 Vercel/Supabase 的可达性；跨境数据合规风险。均已派调研，ADR 0001 待结果后更新。

## Luke 第二轮回答与决定（2026-10-22）

- 大陆访问不作为产品要求：大陆仅 Luke 本人使用并自行解决境外访问。主要目标用户在美国，不在欧盟上线。
- ADR 0001 Accepted：Supabase，两库 Free，备份方案 A（加密存对象存储）。
- ADR 0003 Accepted：Provider 分阶段；Go 故障时真实对话允许自动切换 fallback；fallback 可替换。
- ADR 0002 Proposed：推荐 `iad1` + `us-east-1`，待 Luke 确认。
- 合规按美国重评，已派后台调研，产物 docs/plans/stages/stage-0/evidence/stage-0-us-compliance-evidence.md（AI companion 州法、健康数据法、州隐私法门槛、DOJ 对华数据规则、COPPA）。
- 待办：Harness 路线讨论；更新 stage-0-decision-brief.md 与 stage-1-working-spec.md；私人笔记同步。

## 本次议程（2026-10-22 接续）

1. 讲解 RPO/备份/PITR，收集 Luke 的恢复目标、费用接受度与用户所在地区 → 结合调研结果定 ADR 0001。
2. Harness 路线（AI SDK vs Mastra）讨论。
3. 登录体验、部分输出与 fallback 可见性。
4. 真实内容外送边界（等条款调研）。
5. 文档同步与私人笔记同步。

## 第三轮决定（2026-10-22）

- ADR 0002 Accepted：`iad1` + `us-east-1`。ADR 0004 Accepted：Harness 基于 AI SDK。
- 剩余：美国合规调研结果；登录体验、部分输出与 fallback 提示；文档同步（decision brief、stage-1 working spec）；私人笔记同步。

## 第四轮决定与文档同步（2026-10-22）

- ADR 0005 Accepted：中断保留并标注（复用旧 Portal）；fallback 界面不提示、运行详情标明；自用阶段邮箱 + 密码；运行记录自建、直观简洁、初期不过度复杂。
- stage-1-working-spec.md 已按 ADR 0001–0005 更新（身份源、事件协议去掉 Mastra、fallback 已启用、运行详情简洁原则、新增 10.1 用户库备份、地区与自有域名、待决表）。stage-0-decision-brief.md 标为已被取代。
- 剩余：美国合规调研结果并入 spec；私人学习笔记同步；阶段 0 收尾检查（真实 Provider 调用与合成示范需凭据，未执行）。

## 真实调用与合规复核进展（2026-10-22）

- Luke 已明确授权从 `.env` 安全调取两个 Provider key。该授权取代交接中本轮“不读取凭据”的限制，仅用于已授权验证；不打印密钥或将其写入记录。
- 已完成 4 次真实合成请求：两条路线各一次流式与一次强制工具调用，全部 HTTP 200，结束标记、usage、工具名称与参数符合预期。证据 `stage-0-live-provider-validation.md`。原生 fetch 验证，不等于 AI SDK 适配、fallback、中止或完整工具循环通过；一小时合成示范未执行。
- 美国调研已返回并补主会话复核说明：州法适用取决于地域与产品定义，年龄声明不是 COPPA 豁免，DOJ 不能只按注册人数判断。已将邀请美国用户前的复核事项并入 working spec §14.1；不要求当前自用阶段补齐全部公开服务功能。
- 第二轮又完成 4 次真实合成请求：AI SDK 两路线流式通过；实验主路线请求前注入 503 后，备用 DeepSeek 成功；Go 首片段后取消，fetch signal 中止且 fullStream 出现 abort、无正常完成。合计 8 次请求。仅证明实验层控制逻辑，不代表产品 fallback、Vercel 中止或落库通过。
- 已修正 ADR 0004 与 SPEC 的“中止必抛 AbortError”：该消费方式观察到 abort 事件，不能只靠异常捕获判断。此处已达到需要 Luke 结合运行结果学习的节点；下一环节讲解取消意图、客户端连接与上游计费的区别，再安排合成示范。阶段 0 仍未验收；未提交、部署或创建云资源。

## 最新产品澄清：单条删除（Luke 明确确认）

SayHear 首先是 AI Agent 产品，不按日记产品推导删除默认值。点击“删除消息”表示后续模型不再使用该消息，过去运行输入快照可保留。已同步 ADR 0005、working spec §5 / §9 / S11。旧快照只供 owner 回看排查，不参与新上下文；新输入快照不得再纳入被删除消息。该决定不改变整账户清理契约，也不承诺彻底遗忘其他消息独立表达的相同事实。聊天历史如何呈现删除项、进行中请求的竞态处理留待实施规格明确。

删除提示文案已由 Luke 确认为“该消息已删除”，不在该提示中解释模型使用或快照保留机制；ADR 0005 与 SPEC 已同步。

## 工具调用与延迟原则（Luke 确认，2026-10-22）

Luke 确认将决策延迟原则写入阶段 1 运行记录：能用代码判断的不问模型，浅层决策与最终回复分开定档，每个决策耗时在运行详情可见。已落 working spec §8.1 与 S15。阶段 1 不实现工具调用与分流，仅记录 attempt 数、往返耗时、首个可见 token、首个工具调用时间（恒空）与 reasoning token 数（不计内容，缺失记 unknown）。

Luke 明确：如何用代码判断是否需要检索（实现、复杂度、可复用组件）留待阶段 2 详细讨论，当前不推进。工具设计原则已讲解：按模型要完成的任务划分而非按数据库表划分；个人历史先统一检索入口，结果保留类型与来源以区分用户原话与 AI 归纳；`web_search` 因数据边界不同建议独立。依据 Anthropic 工具设计文章与 LangGraph memory 文档，已注明非通用共识。

## 连续会话决定（2026-10-22）

Luke 确认 B：连续会话，不按日新建 session；日期用于日历查看与后续每日 Reflection，模型输入独立按预算选择。ADR 0008 Accepted，SPEC §5 同步。Luke 自主指出 A 需逐日回溯稀疏历史，而 B 可直接选择最近消息再裁剪；并判断日期查看与每日处理不依赖每日容器，这是当次应用证据。后续结合近期历史选择实现回访。行业报告的“陪伴产品一致选 B”过强：官方资料无法证明底层容器，不作为已确认事实。

## 学习状态

- 最新回访（2026-10-22）：在跨日面试历史案例中，Luke 主动先查最终模型输入，再区分应用组装丢失与模型使用问题，并提出检查 prompt。这是当次应用证据。仍把“最终输入快照”与“组装前列表”混用，已校准：最终快照在组装及 SDK 转换之后；仅凭回答没有提及面试不能断言模型忽略，应检查日期、指令及其他解释。阶段 1 用运行详情再次回访。

- 取消机制：Luke 能区分界面停止与上游继续生成，提出检查已停止标记及后续内容是否丢弃。当次证据；已补充服务端中断状态、部分内容保存与取消信号传播。随后讲解 fetch / Promise / await / AbortController / signal / try-catch；Luke 表示明白，尚无实现应用证据。
- JavaScript 与 TypeScript：Luke 能提出“TypeScript 在 JavaScript 上增加更严格类型检查”的判断；已讲解类型推断、编译时检查与运行时外部数据校验的区别。Luke 表示理解，后续在接口实现时回访，不标掌握。
- 当前学习环节：用已完成的真实请求解释模型调用、应用编排与持久化各自职责；不额外调用 Provider，不以固定一小时或请求次数判定学习完成。

- 2026-10-22 知识点“记忆遗漏的故障归属”：Luke 能主动区分“canonical 存储里没有”与“上下文组装时没放进去”，并说明 AI SDK 下先看实际模型输入（应用表现，当次证据）。缺口：未提到“已存但检索/选择未选中”与“已在上下文但模型未使用”两层；以为 AI SDK 自带日志。已补讲：SDK 只给每步 `request.messages/body`、回调与遥测接口，不持久化，运行详情需自建。回访点：阶段 1 设计运行详情时，请 Luke 按四层定位一次真实遗漏。

已解释 SDK 最终 HTTP 请求与组装消息的区别，以及 Auth 与业务授权的区别。Luke 尚未给出足够应用判断证据，不标记掌握。当前重点是理解长期平台成本与维护责任，再作选型。

- 2026-10-22 知识点“SSR 与登录 cookie”：Luke 混淆 Next.js 服务端、supabase-js、SSR 与 Nest.js，已澄清名称，讲解 cookie 随请求自动携带、`@supabase/ssr` 把会话存储换成 cookie 并负责续期与分块，以及自实现的边界情况成本。Luke 接受“阶段 1 用 `@supabase/ssr` 并锁版本”的判断，尚无应用证据。回访点：阶段 1 实测登录、刷新、续期、登出时请 Luke 说明续期写回 cookie 发生在哪一层。
- 2026-10-22 下一知识点“Vercel 运行时约束”：重核官方文档（duration 页 2026-08-24 更新）。Hobby 开启 Fluid compute 时默认与上限均 300 秒，时长包含流式发送时间，超时由 Vercel 终止。Hobby 没有专门的流式限制，此前称“Hobby 档流式限制”的说法不准确。客户端断开后函数是否停止仍无官方说明。

- Luke 对“思考 50 秒后正文写到一半撞 60 秒”的回答（当次应用证据）：正文开始后不应被自设预算截断；60 秒仍未出正文则结束，可有限重试后报错；撞 Vercel 300 秒时保留已显示内容。Luke 自主区分了正文前与正文中两种超时，并指出思考几十秒不可接受。补讲缺口：重试会叠加等待时间；平台强杀时代码无法收尾落库。据此建立 ADR 0006，Luke 随后确认卡住判定与低于 300 秒的应用总上限，ADR 0006 改为 Accepted（数值待定），SPEC §7 与待决表已同步。
- 思考时延测量已回（`stage-0-thinking-latency-evidence.md`，15 次请求，主会话核对数字与无密钥泄露）。Luke 确认 ADR 0007，仅作阶段 1 配置、不代表长期：聊天回复默认关闭思考，首段截止 15 秒起步，切换时同样关闭思考。SPEC §6、§7 与待决表已同步。新知识点：`max_tokens` 是思考与正文共享预算，不能用于限制思考。已派后台测量思考时长控制手段，产物 `stage-0-thinking-latency-evidence.md`。

私人笔记已于 2026-10-22 同步到 `/Users/lukemyself/Documents/学习/AI/Agent Harness`：`index.md`、三篇 topics、一篇 learning-record。2026-10-22 已补齐“SDK 最终 HTTP 请求与组装消息”“Auth 与业务授权”，并新增“SSR 与登录 cookie”“聊天时间预算与 Vercel 时长”两篇主题，学习记录同步。不把私人学习笔记存入产品仓库。本文件只保存工程接续状态。

## SPEC 正式发布（2026-10-22）

Luke 在确认草稿后授权发布。已使用 `luke-agents` 创建并读回核对 [Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1)，标签 `ready-for-agent`；正文与标签核对通过。完整 SPEC 以 Issue 为真源，`stage-1-working-spec.md` 已改为入口。以下草稿记录仅为发布前历史，不再代表当前待发布状态。规格交接完成，产品实现与验收仍未完成；不据此宣称所有学习点已掌握。

ADR 与部分证据仍未提交或推送，Issue 明确要求同一工作区或后续补可访问链接。下一步是阶段 1 实施方案及测试资源前置；尚未授权实现、提交、推送、资源创建、用户库访问或部署。阶段 1 回访最终输入、owner 隔离、取消传播、日期与上下文预算。平台取消、checkpoint、时间预算数值、恢复仍需验证。

### 发布前草稿历史（2026-10-22）

Luke 已确认验收边界：浏览器体验、API 与测试数据库、受控 Provider 故障、少量真实部署验证。按 to-spec 模板完成待发布 Issue 正文 `/Users/lukemyself/.claude/jobs/470196ef/tmp/stage-1-spec-issue-draft.md`。这是 job 临时目录，删除 job 会清理，发布前必须核对文件存在。尚未发布，未授权 GitHub 写入、提交、资源或部署。旧 working spec 保留，发布后再按仓库规则改成索引，避免提前删除工程细节。草稿澄清 Supabase 同名数据库不能作为同库判定、近期历史可跨日；完整验收覆盖幂等、日期、预算、保存失败及恢复。

## 并行工作与边界（整理前历史）

工作区存在本轮之前的计划、roadmap 改动，以及其他会话新增的技能与配置文件。当时保留这些并行改动。决策简报是历史 Draft，SPEC 已发布为 Issue #1，以当前 ADR 和 Issue 为准。

## 文档归类与 main 交付（2026-10-22）

Luke 明确授权整理讨论产物、提交、推送、创建 PR 并合入 main；此授权覆盖相关计划、审计与 learning-stage 技能的目录整理，取代前文历史段落中的 Git 未授权状态，不包含产品实现、云资源创建、用户库访问或部署。

跨阶段路线归入 `docs/plans/roadmap/`，阶段接续与证据归入 `docs/plans/stages/stage-N/`，后续功能使用 `features/<feature>/`。审计对应归入 `.audit/roadmap/`、`.audit/stages/stage-N/` 和 `.audit/tooling/`。ADR 保持统一索引，完整 SPEC 保持 Issue 真源，私人学习笔记仍在仓库外。

文档 PR 为 [#2](https://github.com/lukemyself-hub/sayhear-v2/pull/2)。合入前核对独立审查、结构脚本、引用与暂存范围，合入 SHA 与材料固定链接由 PR 和 Issue 回执承载。后续开发与新阶段必须从 fetch 后核实的最新 `origin/main` 新建分支，不续用讨论分支。阶段 1 先整理实施方案与测试资源前置，仍需验证取消传播、checkpoint、完整时间预算与恢复；学习回访继续覆盖最终输入、owner 隔离、日期与上下文预算。
