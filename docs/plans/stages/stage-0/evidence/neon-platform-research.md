# Neon 平台调研：Managed Better Auth 与数据库选型证据

状态：Draft，供主会话整合 Supabase+Auth 对比。核验日期：2026-10-21（价格与版本按当日官方页面），2026-10-22 纠错修订（见文末修订记录）。本文只记录官方证据，不表示任何路线已被采纳。未创建项目、未连接数据库、未读取凭据、未安装 SDK。

证据标记：已定（CONTEXT/已确认计划边界）、建议（本文判断）、待决定（Luke 才能定）、unknown（官方未说明，不推测）。

## 1. Auth 架构与 GA 状态

结论：当前 Neon Auth = Managed Better Auth（托管 REST 服务），旧 Stack Auth 已停止新用户。SDK 处于 0.x beta，但托管服务本身已 GA。

| 项 | 证据 | 原文/日期 |
| --- | --- | --- |
| 旧架构退出 | Legacy Neon Auth（Stack Auth）不再接受新用户 | "Legacy Neon Auth (Stack Auth) is no longer accepting new users"；"We'll keep supporting it for existing users." |
| 托管服务 GA | "The Neon backend is generally available" | changelog 2026-09-18，Auth 列为核心后端服务 |
| 服务形态 | "Managed Better Auth is the managed authentication service in the Neon backend for apps and agents." "It runs as a managed REST API service." | /docs/auth/about |
| SDK 版本 | "Managed Better Auth runs Better Auth version 1.7.6." "`@neondatabase/auth` 0.6.0-beta and later use a Better Auth 1.7 client." | /docs/auth/about |
| SDK 实际发布 | npm dist-tags latest：`@neondatabase/auth` = `0.7.0-beta`；`@neondatabase/auth-ui` = `0.4.0-beta`（2026-10-12） | registry.npmjs.org，2026-10-21 |
| 最近 SDK 升级 | "Managed Better Auth upgraded to Better Auth 1.7"：0.6.0-beta / neon-js 0.8.0-beta / auth-ui 0.4.0-beta；breaking：account 方法改用本地 account `id`；known issue：auth-ui 0.4.0-beta Providers 卡片无法解绑账号或显示 provider email | changelog 2026-10-16 |

判断：服务 GA 与 SDK beta 不矛盾，但 SDK 是 0.x 且官方明列 known issue。beta 属实。

## 2. 成本：DB 与 Auth 两项目、MAU 口径

Neon 计费在组织层、限额在项目层。官方原文："Plans apply per organization, and one Neon account can belong to multiple orgs on different plans."；"Projects belong to organizations, where plans and billing apply."；"Most limits are per project."。测试库与用户库是两个独立项目（已定边界），同组织即同套餐，测试项目不因在付费组织内而单独免费；两项目各占一份 per-project 限额（含 100 CU-hours / 1 GB / 分支数 / 500 GB egress）。免费层：Free 每项目 100 CU-hours、1 GB 存储、账户合计 20 GB、6 小时恢复窗口（上限 1 GB 变更）、5 分钟无活动挂起且不可关闭、上限 10 分支、5 GB egress。付费层 Launch：计算 $0.106/CU-hour、存储 $0.35/GB-month、instant restore $0.20/GB-month、历史窗口最长 7 天、无月最低；Scale：$0.222/CU-hour、窗口最长 30 天。child branch 走 copy-on-write，"start at $0"。

Auth MAU 口径：Free "Up to 60k MAU per project"；Launch/Scale "Up to 1M MAU per project"；clarification："Auth (MAU) can scale beyond 1M; contact Neon for higher limits."

关键：这是"含顶限额"，不是计量超额。官方没有 MAU 单价、没有超额费率、没有"超过即暂停 Auth"的说明。MAU 如何计数（唯一活跃用户定义、窗口、跨项目是否合并）官方未定义 → unknown。Launch/Scale 的 MAU 是随计划包含的上限，不是额外付费项。

超额/暂停语义（官方只对 Free 非 Auth 项说明）："Running out of CU-hours or egress (5 GB) suspends compute until the next billing period."；"Exceeding 1 GB of Postgres storage ... blocks writes."；"None of these limits delete your data."；"Upgrade to lift any limit immediately." Auth 超过 60k/1M 的行为未说明 → unknown（不能假设会暂停 Auth，也不能假设自动计费）。

成本计量公式（Launch，月）：

```
月成本 ≈ 0.106 × CU-hours + 0.35 × GB-month(主库存储)
        + 0.20 × restore-change-GB-month(仅 root branch)
        + 0.09 × 超出保留期的 snapshot GB-month
        + 1.50 × (分支数 - 含免分支数) 的按月折算
        + 0.10 × (egress GB - 每项目含 500 GB)
```

注意 `restore-change GB-month` 是用于即时恢复的变更数据量，不等于主库 GB-month，两者是不同计量变量，不可互相替代。Snapshots "$0.09/GB-month" 只对超出计划已含历史保留期的部分计费。额外分支 "$1.50/branch-month (prorated hourly)"，Free/Launch 含 10 分支、Scale 含 25。egress 付费含 500 GB per project，之后 "$0.10/GB"。instant restore "charged only on root branches; child branches don't add to this charge"。

场景基线（单位：美元/月，仅平台计量，不含 Provider）。假设 1 CU 常驻 ≈ 730 CU-hours/月；免费层 100 CU-hours ≈ 0.137 CU 常驻，约 1 GB 存储，6 小时恢复。下表只覆盖计算与主库存储，不含 snapshot/额外分支/egress，实际账单需按上面公式加项。

| MAU | 架构 | 计算 | 存储 | 恢复窗口 | 月成本（仅计算+主库存储） |
| --- | --- | --- | --- | --- | --- |
| 50 | 测试 Free + 用户 Free，0.137 CU 常驻各一 | 免费 100 CU-hours 内 | 免费 1 GB 内 | 6 h | $0 |
| 500 | 用户 Launch 1 CU 常驻 | $77.4 | ~$0.35 | 7 天 | ~$78 + restore 用量 |
| 5,000 | 用户 Launch 1 CU 常驻 | $77.4 | ~$0.35 | 7 天 | ~$78 |
| 50,000 | Launch 1 CU；MAU 仍在 1M 内 | $77.4 | 随数据量 | 7 天 | ~$78 + 存储 |
| 60,000 | Free 即达上限；Launch 不受影响 | Launch $77.4 | — | 7 天 | ~$78 |
| 150,000 | Launch 1 CU；仍在 1M 内 | $77.4 | — | 7 天 | ~$78 |

注意：60k 只是 Free 计划的 Auth 上限，Launch/Scale 的 1M 内均无 Auth 附加费。计算费随并发扩容，不是随 MAU 线性增长；真实成本取决于同时在线与查询量，上表是单 CU 基线，不是预测。

"按量无月最低"属实：Launch/Scale "metered hourly and billed at the end of the month, with no monthly minimum"。

## 3. Auth 功能生命周期

来源：/docs/auth/roadmap（状态标签 ✅/⚠️/🔜）、/docs/auth/guides/plugins/admin、user-management、production-checklist。Roadmap 原文："Not all Better Auth plugins are currently supported."

| 功能 | 状态 | 证据 |
| --- | --- | --- |
| Email/password | ✅ | roadmap "Email & password ✅ Supported" |
| Email verification | ✅ 但默认关闭，需自备邮件商才能用链接 | "Email verification is not enabled by default." "Verification links: Require a custom email provider" |
| Password reset | ✅ | production-checklist："Password reset: Works with shared or custom email providers" |
| OAuth Google/GitHub/Vercel | ✅ | roadmap；生产需自建 OAuth app |
| Magic link | ✅ | roadmap |
| Email OTP | ✅ | roadmap |
| Phone number | ✅ | roadmap |
| Passkeys | unknown（roadmap 未列） | 未提及 |
| MFA | 🔜 Coming soon | roadmap |
| SSO/SAML | unknown（未提及，不等于支持） | 未提及 |
| Account linking | 部分/unknown：auth-ui 0.4.0-beta 无法解绑账号 | changelog 2026-10-16 known issue |
| Ban/unban | ✅ | admin：`banUser` "Baning prevents sign-in for a user." `unbanUser` |
| 删除用户 | unknown：admin 页无 removeUser/deleteUser，user-management 只列 "Deleting user accounts" 主题无方法 | 官方未提供删除路径。不得据此建议直接 SQL 删 `neon_auth` 内部 schema 行——无官方授权，且可能绕过 hash / 级联 / JWKS 一致性。需向 Neon 确认官方 API 与 GDPR 删除流程 |
| 撤销会话 | ✅ 部分 | `revokeUserSession`、`revokeUserSessions`、`revokeOtherSessions: true` |
| 邮件供应商 | ✅ 自备 SMTP；默认共享 `auth@mail.myneon.app` 仅供开发测试 | "Replace shared SMTP ... with your own email service" |
| 速率限制 | unknown：只说明共享邮件商会限流，无 Auth 登录限流数字 | 未给数值 |
| Admin 其他 | ✅ `listUsers`/`createUser`/`setRole`/`listUserSessions`/`impersonateUser`（≤1 小时）；需 admin 角色会话 | admin 插件页 |
| 修改邮箱 | ⚠️ 文档冲突，需向 Neon 确认，不要自行判定 | admin 插件页："Update user information such as email, name, and custom fields." vs user-management："Email address changes are not currently supported." admin 插件面可能比文档枚举更宽，"文档没列"不能推出"不支持" |
| Organization | ⚠️ Partial | roadmap |
| Standalone frontend + backend | 🔜 未支持，因 HTTP-only cookie 不能跨域共享 | roadmap |

## 4. 恢复与分支是否含 Auth

- 恢复含 Auth："All Postgres data and schema on your branch, along with Managed Better Auth data stored in the `neon_auth` schema" are replaced；"There is no way to exclude `neon_auth` from a restore"；备份分支"still holds your earlier auth state"（/docs/guides/branch-restore）。
- 分支克隆含 Auth："Because authentication data (users, sessions, and configuration) lives directly in your database's `neon_auth` schema, it is cloned along with your business data when you create a branch."；"Sessions do not transfer between branches."（/docs/auth/branching-authentication）。
- 时间点一致性：PITR 把库与 `neon_auth` 一起回放到同一时间点，登录态随 sessions 表一起回退。这是由 `neon_auth` 随分支恢复的机制推出的**推断**，官方未陈述恢复后 session/token 是否仍有效，需在演练中验证。
- RPO/RTO：官方只给历史窗口（Free 6 h/1 GB 变更上限；Launch 7 天；Scale 30 天），**窗口长度不等于 RPO**，官方未给 RPO/RTO 数字 → unknown，不虚构。
- 测试不用生产克隆：`CONTEXT.md` 已定两库隔离，测试库不得连接或重置用户库。上面的分支/克隆行为只说明技术上会复制 Auth 数据，不构成允许用生产分支做测试。

## 5. SDK 成熟度与锁定

- 版本：服务 GA（2026-09-18），SDK 0.x beta（auth 0.7.0-beta、auth-ui 0.4.0-beta、neon-js 0.8.0-beta）。GitHub neondatabase/neon-js 仓库 "There aren't any releases here."，35 open issues / 30 open PRs（2026-10-21）→ 发布渠道走 npm dist-tags（auth latest = 0.7.0-beta），GitHub Releases 只是未使用的渠道，**不能据此推出"发布纪律弱"**；35 open issues / 30 open PRs 是社区活跃度事实，不是纪律指标。beta 定性来自版本号本身与官方 known issue，不来自发布渠道。
- 已记录粗糙点（可见窗口内）：changelog 2026-10-16 有 1 次 breaking + 1 个在修 known issue；changelog 2026-10-09 有 1 次 bug fix。这支持"beta 有已知粗糙点"，不支持"发布纪律差"的定性。
  - Breaking（2026-10-16）：`accountInfo`、`unlinkAccount`、`getAccessToken`、`refreshToken` 改用本地 account `id` 识别已链接账号，"They no longer accept `providerId`."
  - Known issue（2026-10-16）："In `@neondatabase/auth-ui` 0.4.0-beta, the Providers settings card can't unlink an account or show the provider email." "A fix is in progress."
  - Bug fix（2026-10-09）："Fixed an issue where you couldn't create a user without a display name."
- Next.js SSR：支持 App Router。"Requires Next.js App Router."；"Server components using auth methods must be rendered dynamically"，需 `export const dynamic = 'force-dynamic'`；`createNeonAuth` from `@neondatabase/auth/next/server` 提供 `.handler()`/`.middleware()`/`.getSession()`；"`proxy.ts` replaces `middleware.ts` in Next.js 16."
- 退出/自托管路径：官方承认自托管 Better Auth 是出路（"custom plugins, hooks, and options not yet supported by Managed Better Auth"）。数据在 `neon_auth` schema，"queryable with SQL"，理论上可导出表。但导出密码 hash / session / user id 的官方迁移流程：legacy Stack Auth 迁移页没有导入导出或 ID 兼容说明；Managed Better Auth → 自托管 Better Auth 的官方迁移指南未找到 → unknown。不能因 Better Auth 开源就认定无锁定：迁移需要处理 hash 算法兼容、session 表结构、OAuth client 重定向与 `neon_auth` 归属。
- 维护责任：Neon 负责托管服务运行（"Zero server management"），开发者负责邮件商、OAuth app、可信域名、模板定制（webhooks 拦截）。

## 6. 地区、网络与运维责任

- 仅 AWS："Managed Better Auth is currently available for AWS regions only." "Azure support is not yet available." 区域页："Postgres and Managed Better Auth run in all regions."（8 个 AWS 区域均可用）；"Neon Azure regions ... are deprecated."
- 网络限制："Managed Better Auth does not currently support projects with IP Allow or Private Networking enabled." → 若未来要私有网络，Auth 需迁移。
- 项目创建后地区不可改，迁移需新建项目（沿用 stage-0 证据）。
- 免费项目 90 天无活动可能被删（regions 页，2026-10-05 起）→ 影响"长期闲置的测试项目"。

## 未决与 unknown

1. MAU 计数定义、跨项目是否合并、超额后 Auth 行为与是否计费。
2. 删除用户的官方 API 与 GDPR 删除流程。
3. Passkeys、SSO/SAML、账号解绑、速率限制的确切状态。
4. Auth 的 RPO/RTO 承诺；恢复后 session/token 是否仍有效（待演练验证）；恢复是否单列 Auth 一致性文档。
5. Managed Better Auth → 自托管 Better Auth 的官方迁移路径与 hash/session 导出兼容性。
6. 免费测试项目与付费用户项目同组织：已核实——"Plans apply per organization"，同组织即同套餐，测试项目不因在付费组织内而单独免费；两项目各占一份 per-project 限额。无需再列为未决。
7. 真实冷启动延迟、Vercel 到 Neon 的取消传播（不在本文范围）。

## 来源（均核验 2026-10-21）

- https://neon.com/docs/auth
- https://neon.com/docs/auth/about
- https://neon.com/docs/auth/roadmap
- https://neon.com/docs/auth/production-checklist
- https://neon.com/docs/auth/branching-authentication
- https://neon.com/docs/auth/guides/user-management
- https://neon.com/docs/auth/guides/plugins/admin
- https://neon.com/docs/auth/quick-start/nextjs-api-only
- https://neon.com/docs/auth/reference/nextjs-server
- https://neon.com/docs/auth/migrate/from-legacy-auth
- https://neon.com/docs/guides/backup-restore
- https://neon.com/docs/guides/branch-restore
- https://neon.com/docs/introduction/regions
- https://neon.com/docs/introduction/plans
- https://neon.com/pricing
- https://neon.com/docs/changelog（2026-09-18 GA、2026-10-16 SDK 升级）
- registry.npmjs.org/@neondatabase/auth、/@neondatabase/auth-ui
- github.com/neondatabase/neon-js/releases

## 修订记录

- 2026-10-22：依据 `database-auth-critical-check.md` 独立核查与主 Agent 纠错要求修订。改动：计费口径由"按项目计费"改为"组织层计费、项目层限额"；新增成本计量公式与 snapshot/额外分支/egress 单价；删除用户由"需 SQL 删 `neon_auth` 行"降级为 unknown；修改邮箱由"❌ 不支持"改为"⚠️ 文档冲突，需向 Neon 确认"；RPO/RTO 明确"窗口 ≠ RPO"；删除"GitHub Releases 缺失 → 发布纪律弱"推断，改为发布渠道与粗糙点事实；恢复后会话有效性由未证实表述改为待验证推断。
