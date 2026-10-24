# 旧仓库 SayHear 鉴权与数据归属证据（只读调研）

来源仓库：`/Users/lukemyself/Projects/SayHear`（main `cce52bb`，2026-10-21）。调研日期 2026-10-22。
性质：旧结论是证据，不是 v2 的决定。v2 已定 Supabase + Auth（ADR 0001/0005），本文件只提炼经验教训。

## TL;DR

旧仓库是"单 Internal Owner + 应用层鉴权 + 双数据库（业务 / Purge Marker）"架构。身份走 Auth.js（NextAuth）GitHub OAuth + PostgreSQL database session；所有 API 不接受客户端 owner ID，`user_id` 一律由服务端 session 经 `active_internal_owner` 视图映射得出。数据归属全靠 `user_id` 列 + 复合外键 + 应用层 SQL 过滤实现，**没有 RLS**（架构文档把 RLS 列为 External MVP 前才补的 defense-in-depth）。测试隔离靠独立 env 变量 + loopback/数据库名断言 + 独立 schema，从不回落到 `DATABASE_URL`。

## 发现 1：鉴权闸门（auth gate）

- **技术栈**：Auth.js（next-auth）GitHub OAuth，`strategy: "database"` session，7 天有效期，HttpOnly cookie（`apps/web/src/auth.ts:48`-`103`；cookie 名 `sayhear.session-token`，preview/prod 加 `__Secure-` 前缀，`auth.ts:55`-`72`）。
- **身份来源**：`app_users` / `internal_owner_identities`（`owner_slot` CHECK 只允许 = 1，硬性单 owner）+ `auth_sessions`（存 session_token 的 SHA-256 hash），活跃 owner 由视图 `active_internal_owner` 定义（`packages/data/migrations/0001_foundation.sql:1`-`38`）。
- **登录适配器 fail-closed**：`createUser` 直接抛 `UnauthorizedIdentityProvisioningError`（"Internal Owner users must be pre-provisioned."），`getUserByAccount` 只查 `active_internal_owner` 视图 —— 新 GitHub 账号无法自助注册（`packages/data/src/postgres-auth-adapter.ts:45`-`60`、`107`-`110`）。
- **owner 开通是独立 CLI**：`pnpm db:provision-owner` 只接受环境里配置的 issuer/subject + 预生成 UUIDv7；事务内 `FOR UPDATE` 锁 owner_slot=1 行，已存在不同身份即报错（`packages/data/src/cli/provision-internal-owner.ts`；`packages/data/src/postgres-internal-owner-access-repository.ts:59`-`117`）。身份映射一旦写入不可变。
- **API 鉴权模式（统一）**：每个 route 组装 handler 时注入 `authenticate(request)`，实现为 `getServerSession(composition.authOptions)`；无 session 返回 401（`apps/web/app/api/internal/access/route.ts:14`-`21`）。App Router 没有全局 middleware —— 每个 `/internal` 页面各自 `getServerSession` + `redirect`（如 `apps/web/app/internal/page.tsx:26`-`28`；布局注释明确"每个页面保留自己的 guard"，`app/internal/layout.tsx:9`-`14`）。约 37 个 route/page 逐一列举见 `apps/web/app/api/internal/**`。
- **真正的授权闸门在服务层**：认证（你是谁）之后还有第二道 owner 判定 —— `InternalOwnerAccessService.getAccess/assertOperator` 查 `findActiveOwner`，非活跃 owner 抛 `InternalOwnerAccessDeniedError` → 403（`packages/application/src/internal-owner-access.ts:38`-`63`）；写路径在 SQL 事务内 `FOR UPDATE` 重查 owner active + status（`packages/data/src/postgres-user-text-conversation-repository.ts:831`-`853`，返回 `owner_denied`，应用层转 403 `UserTextOwnerDeniedError`，`packages/application/src/user-text-conversation.ts:679`、`713`）。
- **拒绝客户端 owner ID**：所有 handler 统一拒绝请求参数/请求体里的 `user_id` / `owner_id` / `userId`，返回 400 `client_owner_identifier_not_allowed`（`apps/web/src/user-text-turn-handler.ts:31`-`35`；同模式见 `internal-access-handler.ts:21`、`conversation-history-handler.ts:14`、`operator-full-purge-handler.ts:37` 等十余处）。
- **私有写闸门（第三道）**：即使身份正确，真实写入还要求最新备份策略证据 verified 且指纹匹配（`getAccess` 返回 `privateWrites` gate 状态；README "Real private writes remain blocked until..."，`README.md:50`-`52`）。
- **敏感读取 step-up**：Reflection 正文展开 Evidence 原话需要 10 分钟内的 GitHub OAuth roundtrip step-up（HMAC intent cookie + 原子事务重验 session/data epoch），见 ADR-0129 与 `apps/web/src/content-step-up.ts:8`-`19`。
- **Cron 身份**：GitHub Actions 每小时的 Recovery Scan 用独立 `CRON_SECRET`（README `README.md:54`-`56`）。

## 发现 2：数据归属建模

- **每张私有表都带 `user_id` UUID 列**，并大量使用复合外键把"记录属于该 owner 的 session"锁定在 schema 层：`daily_sessions` 的 `UNIQUE (user_id, logical_date)`、`UNIQUE (daily_session_id, user_id)`、每用户唯一活跃 session 部分索引（`packages/data/migrations/0002_user_text_conversation.sql:1`-`25`）；`interaction_turns` / `conversation_events` / `conversation_event_revisions` 均携带冗余 `user_id` 并用 `FOREIGN KEY (daily_session_id, user_id)` 复合引用（同文件 `:39`-`125`）。跨 owner 引用在 FK 层即被拒绝（测试佐证："A session that belongs to another owner fails the composite owner FK"，`tests/system/memory-trust-actions.system.test.ts:2620`）。
- **归属执行在应用层 SQL**：所有 repository 查询都显式带 `user_id` 条件，且写事务先重查 owner（active/epoch）再写（`packages/data/src/postgres-journal-repository.ts:86`-`106`：`row.user_id !== input.userId` 即拒绝）。
- **没有 RLS / CREATE POLICY**：`packages/data/migrations/**` 全量 grep 无一命中。架构文档 `docs/architecture/18-20-privacy-security-lifecycle.md:146` 把 "RLS 或等效 defense-in-depth" 列在 **External MVP 前**的待办清单里；同文件 `:328`-`329` 按阶段表列 Foundation/1A.1 只承诺 stable `user_id` + data epoch + fence。
- **多用户假设**：ADR-0014 明确 Phase 1 只有一个 Internal Owner，不建注册/邀请/恢复/多用户生命周期，但"每条记录仍带稳定服务端派生 `user_id`，API 永不信任客户端 owner ID"以保留隔离不变量；正式多用户隔离与跨账号越权测试推迟到 Phase 2（`docs/adr/0014-phase-one-has-one-internal-owner-account.md:8`-`10`）。`docs/architecture/24-29-testing-and-delivery.md:1107`-`1116` 列 Phase 2 gate：正式 Auth、session rotation、tenant scoping、RLS、越权测试等。
- **Daily Session 归属不随午夜改变**：exchange 属于开始时的本地日期，`logical_date` / `timezone_at_start` 不可变（ADR-0012，`docs/adr/0012-...md:8`-`10`）。
- **Entity 也 user-scoped**：ADR-0088，私人 Entity 默认单用户作用域，label 不定义身份（`docs/adr/0088-...md:8`-`12`）。
- **删除沿 owner**：Full Purge 以整个 owner 为 scope（`owner_purge_orders` / `owner_purge_receipts`，`packages/data/migrations/0019_owner_full_purge.sql:15`、`60`）；ADR-0131 要求每个私人数据面登记可验证的 purge 合同；Purge Marker 存在独立的 marker 数据库（见发现 3）。Owner-first 锁顺序与事务内重查 owner/epoch 见 ADR-0153（`docs/adr/0153-...md`）。
- **持久 ID 不透明**：branded ID type（`UserId` 等），ADR-0085 规定 persistent ID 不透明、semantic ID 版本化。

## 发现 3：测试库与用户库分离

- **变量分四层**：`DATABASE_URL`（应用业务库）、`PURGE_MARKER_DATABASE_URL`（独立 marker 库，必须 ≠ `DATABASE_URL`）、`TEST_DATABASE_URL`、`TEST_PURGE_MARKER_DATABASE_URL`（`.env.example` 顶部与 :41-43；`docs/agents/local-environment.md:21`-`24`）。
- **启动期护栏**：`assertSafeRuntimeConfiguration` 拒绝 `PURGE_MARKER_DATABASE_URL == DATABASE_URL`（`apps/web/src/runtime-config.ts:472`-`478`；composition 建池时也有注释重申，`apps/web/src/server-composition.ts:160`-`164`）。测试专用开关（deterministic provider、固定时钟 `SAYHEAR_TEST_NOW`、test principal）只允许 `deployment === "test"`，preview/prod 启动即抛错（`runtime-config.ts:151`-`163`）；开发签名密钥在 preview/prod 也被禁止（`:164`-`168`）。
- **本地配置纪律**：`.env` 与 `.env.neon` 两套 profile 有意同名不同值，文档明令不跨文件同步、按任务只加载一个 profile、写入/迁移前确认目标、"不要把生产数据库用于测试"（`docs/agents/local-environment.md:6`-`28`）。
- **CI 双库 by construction**：`pr-validate.yml` 起两个独立 postgres:17 容器（端口 5432/5433），注入 `TEST_DATABASE_URL` / `TEST_PURGE_MARKER_DATABASE_URL`（`.github/workflows/pr-validate.yml:44`-`70`）；`scripts/ci/test-databases.ts` 校验两变量必需、归一化后不得指向同一库、不得回落（"the CI database check never falls back to a shared or in-memory database"，`test-databases.ts:28`-`32`）。
- **逆袭者检查（最强护栏，v2 直接可借鉴）**：验收 runner 的隔离门 `eval/continuity-acceptance-301/src/isolation.ts` 用三条独立事实回答"这库安全吗"（文件头注释 `:1`-`18`）：目标只能是专用变量且**永不回落 `DATABASE_URL`**（`:81`、`:144`-`180`，与 `DATABASE_URL` 同库即拒绝 `:165`-`173`）；只允许 loopback host、拒绝重定向连接参数（host/hostaddr/port/service）并用 pg 驱动真实解析目标（`:56`-`124`）；库名必须匹配合成名模式 `sayhear_(test|acceptance|...)`（`:46`、`:125`）。SUT schema 由运行自己创建并盖 run identity 戳，`assertSyntheticOwner` 拒绝触碰含真实 owner（非 `.invalid` issuer）或有其他用户的 schema（`:120`-`160`）。
- **系统测试不回落 mock**：`TEST_DATABASE_URL is required; the system seam never falls back to a mock database.`（`tests/system/conversation-behavior.system.test.ts:45`）；每个 suite 建一次性 `sayhear_test_*` schema 并 DROP（`packages/test-support/src/postgres.ts:32`-`49`）；CI 启动前探测残留 schema，非空即 fail（`scripts/ci/test-databases.ts:83`-`103`）。
- **托管验收与生产隔离**：ADR-0144 要求独立 Vercel 项目 + 独立业务库/marker 库，"No incomplete manifest or test-principal bypass is introduced"；`scripts/export-hosted-workflow-canary.ts:193`-`203` 主动对比 `TEST_DATABASE_URL` 与生产 `DATABASE_URL` 身份，相同即拒绝导出。ADR-0020 规定读取真实私人数据的 Replay 必须在无生产库凭据的隔离运行时。
- **未见"测试误连生产"事故记录**：grep 未发现混库事故（旧 repo 的 "incident" 注释均为 Provider/OUTBOX 技术事故，如 `packages/data/src/postgres-outbox-dispatcher-repository.ts:66` 2026-08-17）。防护是预防性的（fail-closed 门 + 双库 by construction），不是事后修复。

## 发现 4：已知问题与待办

- RLS/tenant scoping/跨账号越权测试/多用户 deletion ledger 全部明确推迟到 Phase 2 External MVP gate（`docs/architecture/24-29-testing-and-delivery.md:1107`-`1116`；ADR-0022）。单 owner 期间 schema 层只有 FK + CHECK，没有 defense-in-depth 第二层。
- 无全局 middleware；每个页面/route 亲手写 guard。布局注释承认这是刻意的（各页面自带 redirect，`apps/web/app/internal/layout.tsx:9`-`14`），但约 37 个入口的手工重复是新增风险点（漏写一个 route 即裸奔 —— 缓解是 `authenticate` 注入模式集中了逻辑，但 guard 的存在性不被框架强制）。
- `internal_owner_identities.owner_slot` CHECK（= 1）是单 owner 的 schema 硬编码；v2 若要多用户需另设计（旧库该表无法平滑扩容）。
- 部分 owner-associated 元数据在 Full Purge 后保留 30 天且"单 owner 期间视为 owner-associated"，ADR-0130 自认这不因去 ID 就算匿名（`docs/adr/0130-...md:10`）。
- 旧 ADR-0144 曾被 ADR-0148 修订（commit 等式曾一度把部署身份与验收混同，后拆分为"部署身份 / 配置授权 / 能力验收"三件事，见 `docs/adr/0144` 头部修订注记）—— 教训：身份类判定要一次拆清楚，避免返工。

## 可沿用

- "身份映射 → 服务端派生 user_id → API 拒绝客户端 owner ID" 三段式：`user_id` / `owner_id` 参数一律 400 的统一模式（`user-text-turn-handler.ts:31`）与 `UserId` branded type。
- 预开通账号 + `createUser` 抛错禁止自助注册（`postgres-auth-adapter.ts:107`）。
- 双独立库（测试业务库 / 测试 marker 库）+ CI by construction + 启动期等值断言（`runtime-config.ts:472`）。
- acceptance runner 式三条独立事实隔离门：专用变量不回落、loopback + 数据库名模式 + 禁重定向参数、schema 戳 + 合成 owner 断言（`isolation.ts`）——与 v2"测试永远碰不到用户库"目标几乎同构。
- 写事务内重查 owner active/epoch（`postgres-user-text-conversation-repository.ts:831`-`853`）与跨 owner 复合外键（`0002` migration）。
- 集群式 `handlers` 工厂：`authenticate` 注入 + 错误到 HTTP 状态映射集中，route 文件薄。

## 不应沿用

- 数据库 session + 7 天固定 maxAge（Auth.js strategy "database"，`auth.ts:100`）：无 rotation；v2 Supabase Auth 自管。
- schema 硬编码单 owner（`owner_slot = 1` CHECK）。
- 每张表冗余 `user_id` 列 + 复合 FK 的手工一致性：表多时迁移与 purge 成本高（124 表/130 索引的 purge inventory，`docs/plans/g1-activation.md:48`）；v2 有 RLS 可把 tenant 过滤推进 DB 层，不必如此重的应用层复合键。
- 把 RLS 推迟为"以后补"：旧架构文档自己也把 RLS 列为 gate 前待办；v2 从一开始用 Supabase RLS 是既定方向（ADR-0001），这里的教训是"应用层过滤不可作为唯一防线"。
- 无全局 middleware 的逐页手写 guard（约 37 处重复）。
- `.env` / `.env.neon` 双 profile 同名变量不同值：纪律靠人 README 约定，容易踩坑（`local-environment.md:10`-`14` 自己都在教"不要覆盖另一份"），v2 的护栏应自动化而非文档化。

## 未知 / 可进一步核实

- G1 验收期 `SAYHEAR_TEST_PRINCIPAL_SUBJECT` 实际如何接线到 session（grep 只见 runtime-config guard 与测试，未见生产实现文件；可能已随 G2 清理移除）。
- `auth_sessions` 表与 Auth.js `createPostgresAuthAdapter` 的 session 写路径是否一致覆盖（adapter `createSession`/`updateSession` 未逐行核对，`postgres-auth-adapter.ts:238`-`250`）。
- 是否曾有跨页面 guard 漏写的实际 incident：git log 未见，但无法排除未记录的情况。
- Hosted acceptance（独立 Vercel 项目）当时的实际 Vercel/数据库配置（需查 Vercel MCP 或当时 Issue，超出本次只读代码调研范围）。

---
（行号基于旧仓 main `cce52bb` 快照。）
