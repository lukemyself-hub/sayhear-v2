# 数据库与 Auth 长期主线对比（Neon vs Supabase）

日期：2026-10-22。状态：Draft，**未经 Luke 同意**。性质：最终证据整合与纠错，不新研究。依据 `docs/plans/stages/stage-0/evidence/neon-platform-research.md`（Neon，2026-10-21 核验 + 2026-10-22 纠错）、`docs/plans/stages/stage-0/evidence/supabase-platform-research.md`（Supabase，2026-10-22 核验 + 补页）、`docs/plans/stages/stage-0/evidence/database-auth-critical-check.md`（独立反方核查，2026-10-22）。

不数字打分。目标权重按定性权衡。未创建项目、未连库、未安装 SDK、未读凭据。

## 1. 证据状态与冲突

| 主题 | Neon | Supabase |
| --- | --- | --- |
| Auth 服务形态 | Managed Better Auth，托管 REST 服务，服务已 GA（changelog 2026-09-18） | Supabase Auth（内置，随平台） |
| Auth SDK 成熟度 | `@neondatabase/auth` 0.7.0-beta、`@neondatabase/auth-ui` 0.4.0-beta | `@supabase/supabase-js` 2.118.0 stable；**`@supabase/ssr` 0.12.7 官方明写 beta**（"This package is currently in beta." / "the API is still unstable and may have breaking changes"） |
| MFA | 🔜 Coming soon（roadmap） | 已支持：App Authenticator(TOTP) + phone；phone 因子 $75/月起 |
| 改邮箱 | **文档冲突**：admin 插件页 "Update user information such as email..." vs user-management "Email address changes are not currently supported." → 需向 Neon 确认 | 已核：登录用户可通过 `updateUser` 更新邮箱；该用户接口不要求暴露 `service_role` |
| 删用户 | unknown：admin 页无 deleteUser/removeUser；不得建议 SQL 删 `neon_auth` 行 | 已核：服务端 `deleteUser` 要求 `service_role`；`shouldSoftDelete` 默认 false，可选 soft delete 也不可逆 |
| 找回密码 | ✅ Password reset（可用共享或自备邮件商） | ✅ 已核：`resetPasswordForEmail` |
| 账号解绑 | known issue：auth-ui 0.4.0-beta Providers 卡片无法解绑账号或显示 provider email，修复中 | 未逐条核实（不在本次核验范围） |
| 恢复含 Auth | ✅ "There is no way to exclude `neon_auth` from a restore."；会话不跨分支 | auth schema 未在备份页写明 → 合理推断含 auth 表，**不是保证**，恢复演练待核实 |
| Storage 对象 | Neon 无对应 Storage API 计费项在本次范围 | 明确不含："Database backups do not include objects you store via the Storage API."；恢复旧备份不找回其后被删对象 |

Neon 侧"发布纪律弱"已删除：GitHub Releases 缺失 ≠ 纪律差（发布走 npm dist-tags），35 open issues / 30 open PRs 是活跃度不是纪律指标。可见窗口内是 1 次 breaking + 1 个在修 known issue + 1 次 bug fix——支持"beta 有已知粗糙点"，不支持"发布纪律差"的定性。

## 2. 成本：公平口径

- Neon 计费在**组织层**（"Plans apply per organization"），限额在**项目层**（"Most limits are per project"）。同组织即同套餐，测试项目不因在付费组织内而单独免费；两项目各占一份 per-project 限额。
- **MAU 不是数据库成本变量。** 不能把 MAU 换算成固定数据库成本：Supabase 侧 MAU 只影响 Auth 计费（100k 后 $0.00325/MAU），Neon 侧 Launch/Scale 的 1M MAU 是含顶限额、无 per-MAU 单价。数据库成本取决于 CU-hours、存储 GB-month、恢复与备份、egress，与活跃用户数无官方换算关系。
- Neon 月成本公式（Launch）：`0.106 × CU-hours + 0.35 × GB-month(主库存储) + 0.20 × restore-change-GB-month + 0.09 × 超出保留期的 snapshot GB-month + 1.50 × (分支数 − 含免分支数) + 0.10 × (egress GB − 每项目含 500 GB)`。`restore-change GB-month` 是即时恢复的变更量，**不等于主库 GB-month**，不可互相替代。额外 snapshot $0.09/GB-month、额外分支 $1.50/branch-month、egress 含 500 GB/project 后 $0.10/GB。

### Auth 边际成本（只算 Auth，不含数据库）

| MAU | Supabase | Neon |
| --- | --- | --- |
| 50 / 500 / 5,000 / 50,000 | $0（Free 层含 50k，Pro 含 100k） | $0（Launch 含 1M 内，无 Auth 附加费） |
| 150,000 | 超出 100k 的 50,000 × $0.00325 = **$162.5 额外** | $0（仍在 1M 内） |
| 测试项目 | 测试项目若用 Free 层（限 2 active projects、1 周无活动暂停）不占生产配额；若在 Pro 组织内则计 compute，且 **MAU 跨 project 聚合口径官方未明确**，不得断言 | 测试项目占一份 per-project 限额；Auth MAU 跨项目是否合并不明 → unknown |

Supabase 跨 project MAU 去重与组织级聚合口径仍未由本轮抓取的原文明确。定价页写 "Supabase uses organization-based billing."，MAU 页说明计费周期内登录或刷新 token 的不同用户计数，各 project usage 可在 Usage 页查看；可见不等于已说明跨项目去重方式。

Neon Launch 的 1M MAU 是含顶限额，不是计量超额；超过 1M 官方只说 "contact Neon for higher limits"，无单价。计算费随并发扩容，不随 MAU 线性增长。

### 平台基础成本（不含 Provider 与 Auth 边际）

- Supabase：Pro $25/月含 $10 compute 抵扣。两个 Micro = $25 + $10 + $10 − $10 = **$35/月**（官方示例一致）。若生产需 Small compute 以满足 PITR 最低要求：$25 + Small(约 $15) + Micro $10 − $10 抵扣 = **约 $40/月基础**，加 PITR 7 天约 **$100/月**，合计 **约 $140/月**。这是**假设情景**，不是强制套餐：是否启用 PITR、生产是否上 Small，取决于业务恢复目标，不是阶段 0 既定要求。
- Neon：Launch 1 CU 常驻 ≈ 730 CU-hours × $0.106 = $77.4/月 + 存储，恢复窗口 7 天；Scale 1 CU ≈ $162/月，窗口 30 天。测试 Free 层每项目 100 CU-hours ≈ 0.137 CU 常驻，6 小时恢复窗口。

**Neon 在备份/恢复这一项成本明确更低**：免费层即有 6 小时恢复窗口，Launch 含 7 天历史窗口且 instant restore 按变更量 $0.20/GB-month 计费；Supabase PITR 7 天是固定约 $100/月附加、替换每日备份且需至少 Small compute。这一点不能因推荐 Supabase 而被掩盖。

## 3. 功能边界

- 普通用户账号体验方面，Supabase 的改邮箱、服务端删除用户、找回密码均已直接核对官方 API 文档；基础登录方案见前期研究。Neon 改邮箱处存在文档冲突、删除用户处为 unknown，不能据此建议直接 SQL 删 `neon_auth`。
- MFA：Supabase 已有（TOTP 免费因子，phone 因子 $75/月起）；Neon 🔜 coming soon。
- Standalone frontend + backend：Neon 🔜 未支持（HTTP-only cookie 不能跨域共享）；Supabase 未在本次范围逐条核实。
- Neon 已知 breaking 与 UI issue 属实但属 beta 粗糙点；**删除路径 unknown 不等于"缺功能"**，可能是文档缺口，也可能尚未提供——需向 Neon 确认。

## 4. 最终建议（主 Agent 结论，未获 Luke 同意）

**建议 Supabase + Supabase Auth 作为长期主线。** 核心理由：对普通用户，完整账号体验与现有功能边界在 Supabase 侧有明确官方支持，而 Neon 的 Managed Better Auth 仍处早期、正在快速变化，关键账号操作存在文档冲突与 unknown。这不是"Neon 功能少"的判定，而是"当前可确认性差异"的判定。

**不把 MFA 作为阶段 0 强制要求**：Neon MFA coming soon，Supabase phone MFA 有固定月费；阶段 0 只有 Luke 一个用户，TOTP 因子无附加费，按需再加。

### 代价（明确列出）

- PITR 贵：约 $100/月且替换每日备份，需至少 Small compute。
- **`@supabase/ssr` 0.12.7 是官方明示的 beta**，API 仍可能 breaking——不能说"Supabase 全栈稳定"。主 SDK 2.118.0 stable，SSR 包 beta，两者状态必须分开陈述。
- 供应商锁定：`auth.users` 表结构、RLS、helper 函数、service_role 秘钥体系由平台拥有。
- 功能更多但别乱用：Storage、Edge Functions、Realtime、phone MFA 各自带来成本与复杂度，阶段 0 不启用。

### 迁移

两边数据都在 Postgres，但迁移不是"拷库即用"：password hash 格式、session/token 表结构、OAuth client 重定向、`auth.users` 与业务表的 RLS 策略、平台 helper 函数都需演练。**不说"必失效"，也不说"必无缝"**——未演练前不得断言任何一边。

## 5. 重评条件

- Neon 官方确认改邮箱支持方式、删除用户的官方 API/GDPR 流程、MFA 上线时间表。
- Neon 官方明确 MAU 计数定义与跨项目是否合并。
- Supabase 官方明确 MAU 跨 project 去重与组织级聚合口径。
- `@supabase/ssr` 发布 1.0 或出现 breaking 变更。
- 业务恢复目标确定后重算：PITR 是否必要、保留期是否足够（**保留期 ≠ RPO**，官方未给 RPO/RTO 数字）。
- 用户规模或并发特征变化，使计算/egress/备份项在总成本中占比改变。

## 6. 首次真实用户前的最低验证

1. 测试库完成真实闭环：注册 → 登录 → 找回密码 → 改邮箱 → 删除账号。
2. 删除账号区分 soft delete 与 `shouldSoftDelete: false`，并验证删除后业务数据与 Storage 对象的处理。
3. 完成一次恢复演练：确认 `auth.users` 是否在每日备份/PITR 内（当前是推断，不是保证），以及恢复后既有 session/token 是否仍有效。
4. 若启用 PITR，验证最低 Small compute 与"PITR 替换每日备份"的实际影响。
5. 若未来存附件，验证 Storage 对象有独立备份/版本策略——库备份不含对象。

## 来源

Neon：https://neon.com/docs/auth/about、/roadmap、/guides/user-management、/guides/plugins/admin、/guides/branch-restore、/auth/branching-authentication、/introduction/plans、https://neon.com/pricing、https://neon.com/docs/changelog（均核验 2026-10-21，纠错 2026-10-22）。
Supabase：https://supabase.com/pricing、/docs/guides/platform/backups、/docs/guides/auth/auth-mfa、/docs/guides/auth/server-side、/docs/guides/platform/manage-your-usage/monthly-active-users、https://supabase.com/docs/reference/javascript/auth-admin-deleteuser、/auth-updateuser、/auth-resetpasswordforemail、registry.npmjs.org/@supabase/supabase-js、/@supabase/ssr（均核验 2026-10-22）。
