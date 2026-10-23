# Neon Auth 关键主张反方核查

性质：独立只读核查。范围：6 个官方页面，未创建项目、未连库、未读凭据、未装依赖。核验日期：2026-10-22。只新建本文件，未修改 `docs/plans/stages/stage-0/evidence/neon-platform-research.md`。

来源（本次仅这 6 页）：`/docs/auth/roadmap`、`/docs/auth/guides/user-management`、`/docs/auth/guides/plugins/admin`、`/docs/guides/branch-restore`、`/docs/auth/branching-authentication`、`/pricing`（外加 `/docs/changelog` 用于第 5 项，属必要补充）。

## A. 已证实（原文仍在）

1. **MFA 仍未支持**："MFA support" — "🔜 Coming soon"（roadmap）。
2. **更改邮箱仍不支持**：user-management "Email address changes are not currently supported."（roadmap 未列此项，靠此页证实）。
3. **60k/1M 是含顶限额，非计量超额**：Free "Up to 60k MAU per project"；Launch/Scale "Up to 1M MAU per project"；"Auth (MAU) can scale beyond 1M; contact Neon for higher limits." 页面无 per-MAU 单价、无超额费率。
4. **恢复必含 neon_auth 且不可排除**："There is no way to exclude `neon_auth` from a restore."；"the backup branch created by the restore still holds your earlier auth state"。
5. **会话不跨分支**："Sessions do not transfer between branches."；"Each branch gets a unique Auth API URL. Tokens issued in one branch are not valid in another."；"Sessions → Sessions (copied, but will expire)"。
6. **beta 属实且明列 known issue**：changelog 2026-10-16 有 breaking 与 known issue（见 E2）。

## B. 需降级（不能按现有措辞使用）

1. **删除用户：从"需 SQL 删 neon_auth 行"降级为 unknown。** admin 页与 user-management 页均无 `removeUser`/`deleteUser`；user-management 只在开头的覆盖列表里出现 "Deleting user accounts"，无对应章节、无示例、无 API、无 SQL。官方未给删除路径 → 应记为"官方未提供，需向 Neon 确认"，不得据此建议直接 SQL 删 `neon_auth` 内部 schema（无官方授权，且可能绕过 hash/级联/JWKS 一致性）。
2. **恢复后的会话复活：从未证实降级为推断。** branch-restore 只说连接会短暂中断（"Existing connections to the selected branch are temporarily interrupted during the restore operation."、"your connection details do not change"），**没有任何一句关于恢复后 session/token 是否仍有效**。JWKS 随 `neon_auth` 一起回滚可支持推断，但官方未陈述 → 只能作为"待验证假设"，不得写成已测结论；恢复窗口 ≠ RPO，官方也未给 RPO/RTO 数字。
3. **"发布纪律弱"删除，改为可核验事实。** "no GitHub releases + 0.x beta" 推不出纪律差：发布走 npm dist-tags（auth 0.7.0-beta），GitHub Releases 只是未用渠道。35 open issues / 30 open PRs 是社区活跃度，不是纪律指标。

## C. 事实错误 / 需改写

1. **"Neon 按项目计费"不准确。** 官方：**"Plans apply per organization, and one Neon account can belong to multiple orgs on different plans."**；"Projects belong to organizations, where plans and billing apply."；"Most limits are per project." 即**计费在组织层、限额在项目层**。研究正文与其未知项 6（免费测试项目与付费用户项目能否同组织）应据此改写：同组织即同套餐，测试项目不因在付费组织内而单独免费；两项目是各占一份 per-project 限额。
2. **成本表漏项（影响两项目 + 分支估算）**：额外分支 "$1.50/branch-month (prorated hourly)"，Free/Launch 含 10 分支、Scale 含 25；Snapshots "$0.09/GB-month"；egress 付费含 "500 GB per project included, then $0.10/GB"；instant restore "charged only on root branches; child branches don't add to this charge"。原表只列计算/存储/恢复三项，会低估。
3. **`updateUser` 与邮箱不可改存在文档冲突（需向 Neon 确认，不要自行判定）**：admin 页 "Update user information such as email, name, and custom fields." vs user-management "Email address changes are not currently supported."。同时说明 admin 插件面可能比文档枚举更宽，**"文档没列"不能推出"不支持"**。

## D. 具体文档级证据（回答"哪个 breaking issue 有证据"）

1. **Breaking（changelog 2026-10-16）**：`accountInfo`、`unlinkAccount`、`getAccessToken`、`refreshToken` 改为用本地 account `id` 识别已链接账号，**"They no longer accept `providerId`."**
2. **Known issue（changelog 2026-10-16）**："In `@neondatabase/auth-ui` 0.4.0-beta, the Providers settings card can't unlink an account or show the provider email." "A fix is in progress."
3. **Bug fix（changelog 2026-10-09）**："Fixed an issue where you couldn't create a user without a display name."

即：本次可见窗口内是**1 次已记录 breaking + 1 个在修 known issue + 1 次 bug fix**。这支持"beta 有已知粗糙点"，不支持"发布纪律差/不成熟"的定性。

## E. 未变的安全边界

两库隔离、测试不连用户库不变。分支/克隆会复制 `neon_auth`（"it is cloned along with your business data when you create a branch"）只是技术事实，不构成允许用生产分支做测试。
