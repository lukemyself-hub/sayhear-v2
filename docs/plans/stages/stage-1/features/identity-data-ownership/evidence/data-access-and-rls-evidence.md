# 数据访问路径与 RLS 证据

调研日期：2026-10-22。范围：Issue #1「范围与决定依据」「删除与隐私」「数据护栏」；ADR 0001、0008。约束：Next.js 服务端在 Vercel iad1、Supabase Free us-east-1、浏览器不直连 Supabase、owner 来自可信认证、绕过 RLS 的凭据不进浏览器、跨主体读写须验证。

## TL;DR

- **推荐 A（supabase-js + 用户 JWT + RLS）作为阶段 1 主路径。** 理由不是"官方推荐"，而是它让 owner 约束落在数据库层：请求以 `authenticated` 角色执行，`auth.uid()` 来自服务端验签后的令牌；应用漏写过滤时返回空集/写入被拒，而不是读到别人数据。写路径的原子性用 **Postgres 函数（RPC）** 承担"保存用户消息 + 建 run + 建 attempt"；幂等靠唯一约束。
- **B（Drizzle/postgres.js 直连 + 每事务 `set local role authenticated` + `request.jwt.claims`）可行但需自建机制。** Drizzle 官方只有策略/角色 DSL 与 `authUid` 助手（源码 `drizzle-orm/src/supabase/rls.ts`），**没有**"按请求设置角色与 claims"的运行时 API；官方文档把该模式放在社区示例里，并称未来移入 `drizzle-orm/supabase`。截至 2026-10-22 仍未移入（npm 最新 0.45.4）。
- **C（secret key / postgres 角色）不满足本项目约束。** secret key 映射 `service_role`（`BYPASSRLS`），postgres 是表 owner 也默认绕过 RLS；此时 owner 只剩应用代码一处保证，与 Issue #1 的"数据库权限策略须经跨主体验证"冲突。只能作为受控的后台任务通道（开通账号、清理 auth 用户、备份），且不得进入请求路径的通用客户端。
- **关键陷阱：** 直连连接串默认以 `postgres` 登录。若忘记逐事务切换角色，RLS 静默失效且测试仍"通过"。这是 A/B 之间最大的风险差。
- **推荐附带条件：** 读取/普通写入走 A；"消息+run+attempt"原子写用 RPC；流式 checkpoint 用短事务逐段更新；账户清理用 Admin API 删 `auth.users` + 各业务表 `ON DELETE CASCADE`（官方 managing-user-data 明示 "Specify `on delete cascade` in the reference"）。

## 事实基础（标注来源）

| 事实 | 证据 | 标注 |
| --- | --- | --- |
| 每个 Data API 请求在**一个事务**内执行 | PostgREST docs 源码："every request to an API resource runs inside a transaction"，`START TRANSACTION … END` | 官方文档/源码 |
| `auth.uid()` 读取 `request.jwt.claim.sub`；线上版本另有 coalesce `request.jwt.claims` JSON 的写法（两处不一致，实际部署以项目内 `pg_get_functiondef` 为准） | supabase/auth `migrations/00_init_auth_schema.up.sql`（2023-10-20 最后改动）；supabase/supabase#4794 | 源码/推断 |
| RLS 默认拒绝；`auth.uid()` 无用户时为 null，策略静默不匹配 | RLS guide：建议 `auth.uid() IS NOT NULL AND …`、`to authenticated` | 官方文档 |
| secret key → `service_role`（`BYPASSRLS`）；publishable key → anon/authenticated；旧 anon/service_role 2026 年底弃用 | API keys guide | 官方文档 |
| `postgres` 不是 superuser 但有 admin 权限；表 owner 默认绕过 RLS，除非 `FORCE ROW LEVEL SECURITY`；超级用户与 `BYPASSRLS` 永远绕过 | roles-superuser（仅说明非 superuser）；PostgreSQL 5.9 原文 | 官方文档；"`postgres` 是 public 表 owner" 属**推断**（Supabase 文档未直说，需在测试库用 `\dt` 确认） |
| 新建 public 表默认授予 anon/authenticated 全部 DML；Supabase 正改为 opt-in | Securing your API | 官方文档 |
| 直连 transaction mode 不支持 prepared statements、pipelining、session state | connecting-to-postgres | 官方文档 |
| Free = Nano：max connections 60，pooler max clients 200 | compute-and-disk | 官方文档 |
| 引用 `auth.users` 时指定 `on delete cascade`；deleteUser 删 auth.users 并级联 auth.sessions | managing-user-data | 官方文档 |
| 删除用户后旧 JWT 在过期前仍有效；ban 不等于删除 | managing-user-data | 官方文档 |
| 迁移应只经 SQL migration 文件，`db push`；RLS 策略也进迁移 | database-migrations | 官方文档 |
| pgTAP：`supabase test db` 默认本地，`--linked`/`--db-url`；每测试独立事务回滚 | CLI reference | 官方文档 |
| Drizzle 提供 `pgPolicy/pgRole`、`authUid = (select auth.uid())`；每请求设角色只在社区示例 | orm.drizzle.team/docs/rls；drizzle 源码 | 官方文档/源码 |
| Drizzle 连接 Supabase 必须 `prepare: false`；若只用 Drizzle 建议关闭 Data API | Supabase Drizzle guide | 官方文档 |

## 对比表

| 维度 | A. Data API + 用户 JWT + RLS | B. 直连 SQL + 每事务切角色 | C. secret/postgres + 应用过滤 |
| --- | --- | --- | --- |
| owner 由谁强制 | 数据库：JWT `sub` → `authenticated` → 策略 | 数据库：仅当每事务都 `set local role` + claims | 应用代码；RLS 默认不生效 |
| 应用漏写 owner 过滤 | 读返回空集；写被 `WITH CHECK` 拒 | 若角色切换正确，同上；**若漏切角色，静默全表可见** | 直接跨主体泄露 |
| 原子写（消息+run+attempt） | 单请求即事务；用 RPC 函数或 FK 嵌套插入 | `db.transaction()` 原生，最直接 | 同 B |
| 幂等唯一约束 | 支持；upsert `onConflict` 或 RPC 内 `on conflict` | 支持 | 支持 |
| 流式 checkpoint | 每段一个短请求；需处理用户 JWT 过期 | 每段一个事务；连接复用简单 | 同 B |
| 连接/池 | 不占应用连接；Supabase 管 PostgREST 连接 | 每实例 1 连接（`max:1`），6543，`prepare:false` | 同 B |
| 迁移 | Supabase CLI SQL 迁移，含 RLS/GRANT | Drizzle Kit 生成 schema + 策略；与 Supabase CLI 易双源 | 同 B |
| 每请求延迟 | 多一跳 HTTPS（Vercel→Supabase API→PostgREST） | 一次 TCP 到 pooler | 同 B |
| 跨主体测试 | pgTAP 切 role/claims + 双 JWT 端到端 | pgTAP 测策略，但**测不到应用是否切角色** | 无数据库层可测 |
| 凭据暴露面 | publishable key + 用户 JWT，均可进服务端 | 数据库密码只在服务端 | secret 只在服务端，但权限过大 |
| 与 Issue #1 契合 | 高 | 中（依赖自制封装正确） | 低 |

## 关键细节

### 事务与幂等
- A：PostgREST 保证单请求一个事务。三种写法：① RPC（`create function ... security invoker`）一次完成三步；② 依赖 FK 的嵌套插入（PostgREST 资源嵌入写入；**具体支持度未在本次取证中确认，标推断/待验证**）；③ 分三次请求——**不满足原子性**。推荐 ①，并用 `unique(owner_id, client_request_id)` 兜底；函数内 `insert … on conflict do nothing returning`，冲突时读回已有 run。
- B/C：`db.transaction(async tx => …)` 直接覆盖；唯一约束同样有效。
- 流式 checkpoint：无论 A/B，每次 checkpoint 是独立事务，不能与请求事务合并。阶段 1 需要"已落库内容保留"，短事务逐段更新 `assistant` 消息 + run 状态即可；不要长事务持有连接。

### 连接与 Vercel
- 官方 serverless 建议：模块级单例、`max: 1`、`prepare: false`、SSL、transaction mode（6543）。postgres.js 默认 pipeline，transaction mode 不支持，可能挂起或错配行。
- Free/Nano 上限 60 直连、200 pooler clients；A 不消耗应用连接，B 每个 warm 实例 1 条。单用户场景两者都远低于上限；A 在并发冷启动上更省心。
- **未知**：Supavisor 默认 pool size 的官方数字本次未取到（相关页面未列默认值）。

### 延迟
- 函数与库同区（iad1 ↔ us-east-1）。A 多一次 HTTPS 跳转，B 一次 TCP；**推断**同区差约个位数到数十毫秒/请求，而一次聊天请求的 LLM 等待是秒级，数据库路径差异不构成决策因素。**未知**：未实测。

### 迁移
- 官方明确：所有远端 schema 变更只走 migration 文件，`supabase db push`；RLS 策略、GRANT 与表同批迁移；`supabase db diff` 仅用于把本地实验固化为迁移。
- Drizzle Kit 能从 TS schema 生成 SQL 和策略，但与 Supabase CLI 迁移历史是两套账本；混用会出现"drizzle 认为已同步、supabase 迁移表没有记录"的分叉。若选 B，建议**单一账本**：Supabase CLI 迁移为真源，Drizzle 只作查询构建器（或 Drizzle Kit 生成后由 CLI 应用）。
- 本次未找到 Drizzle/Supabase 官方对比文档（双方文档均未覆盖），属**推断**。

### 跨主体测试
- A：pgTAP 在 `supabase/tests/*.sql`，`set local role authenticated; set local request.jwt.claim.sub = '<uuid>'`，覆盖 select/insert/update/delete 的允许与拒绝；`supabase test db` 本地或 `--linked`。再加端到端：两个合成用户的 JWT 调 Next.js API，断言读不到/写不进对方数据、伪造 owner 无效。
- B：pgTAP 能验证策略本身，但验证不了"每个查询路径都切了角色"。需要额外的结构性测试/封装约束（例如只暴露 `withUser()` 包装器），否则是 A 之外新增的失效面。
- C：RLS 只是未被激活的摆设，跨主体只能靠应用测试，无法证明"数据库兜底"。

### RLS 性能要点
- 策略写 `(select auth.uid())` 触发 initPlan 缓存；实测 179ms → 9ms。
- 策略列必须建索引且位于 btree 首列；实测 171ms → <0.1ms。
- 策略加 `to authenticated`；查询侧仍显式 `.eq('owner_id', uid)`（171ms → 9ms）。
- 分页按 `(owner_id, created_at desc)` 建复合索引，既服务策略也服务排序。
- 避免在策略里逐行 join；用 `= any(array(select …))` 或 security definer 函数。

### 账户清理
- 官方推荐业务表引用 `auth.users(id)` 并 `on delete cascade`；`auth.admin.deleteUser` 删除 auth.users，级联 auth.sessions（撤销 refresh token）与业务表。
- 但**旧 access token 在过期前仍有效**（官方明示）。Issue #1 要求"撤销可用应用会话"：仅删用户不够，需短 JWT 过期、服务端校验 `session_id` 仍在 `auth.sessions`，或接受窗口并在文档写明。
- Storage 对象会阻止删除用户（官方明示）；阶段 1 无 Storage，暂不涉及。
- 备份需含 `auth` schema（ADR 0001 已记录）。
- **推断**：级联删除在一个事务内完成，数据量大时可能较慢；阶段 1 单用户量级不构成问题。

### 凭据边界
- A 的服务端客户端用 publishable key + 每请求用户 access token；**secret key 不进请求路径**。secret key 若误用，PostgREST 在带用户 token 时仍按用户 RLS 执行（RLS guide），但不应依赖这一行为。
- 若采用 A，建议只暴露必要 schema/表，并关闭"自动暴露新表"；GRANT 与 RLS 同迁移。

## 推荐与翻转条件

**推荐 A**，并配套：
1. 所有请求路径用用户 JWT 的 supabase-js 客户端；secret key 仅存在于三个后台任务（开通、清理、备份）。
2. "保存消息 + 建 run + 建 attempt" 与幂等合并为一个 `security invoker` RPC。
3. 每张 owner 表：`owner_id uuid not null references auth.users(id) on delete cascade`、RLS 四类策略、`(select auth.uid())`、`to authenticated`、owner 索引。
4. pgTAP 跨主体 + 双 JWT 端到端，作为"数据库兜底"的证据。
5. 迁移单一账本：Supabase CLI。

**翻转到 B 的条件（任一）**：
- 原子/多语句事务成为每个请求的常态，RPC 数量与复杂度超过可维护阈值；
- 实测 Data API 每请求开销对聊天体验有可感影响（需实测，不以推断翻转）；
- 需要 PostgREST 难以表达的查询/锁语义（如 `select … for update` 编排）；
- 团队决定以 Drizzle 作为唯一 schema 真源，并接受"每查询必须经过角色封装 + 结构性测试"的额外失效面。

**翻转到 C 的条件**：仅当产品退化为单用户、且 Luke 明确接受放弃数据库层隔离；与当前 Issue #1 冲突，不建议。

**不构成翻转**：旧 anon/service_role key 2026 年底弃用——publishable + 用户 JWT 模型继续支持 A。

## 对决策的影响

- 决策点 1 应收敛为"**A 为主 + RPC 承担原子写 + secret 仅后台**"，而不是"ORM 选型"；ORM 可作为 A 之上的可选查询层，但不能替代 RLS。
- 决策点 2（最小数据契约）必须把 `owner_id → auth.users(id) on delete cascade` 写进每张 owner 表，并明确 `owner_id` 来自 JWT `sub`，不接受客户端字段。
- 决策点 4（测试环境）需要 pgTAP 与双 JWT 两层；`supabase test db --linked` 只能在测试项目上运行，护栏需在连接前判定项目身份。
- 决策点 5（验收）新增两条：应用漏写过滤时数据库仍拒绝（负向测试）；删除用户后旧 JWT 的有效窗口有明确处理。
- 遗留待验证：流式长回复期间用户 JWT 过期对 checkpoint 写入的影响（session.md 已登记）；嵌套插入写入支持度；Supavisor 默认 pool size；A/B 实测延迟。

## 未知

1. PostgREST 嵌套插入（父+子一次写入）在 Supabase 当前版本的官方支持与限制——本次未取到明确文档。
2. Supavisor Free/Nano 默认 pool size 官方数值。
3. iad1 ↔ us-east-1 上 A/B 的实测每请求延迟差。
4. 长回复（>1 小时 JWT 有效期）期间服务端如何续期并继续以用户身份写 checkpoint 的具体机制。
5. Free 项目 Data API 是否有独立速率限制（未找到官方数字）。

## 来源（访问于 2026-10-22）

- RLS 策略与性能：https://supabase.com/docs/guides/database/postgres/row-level-security ；https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv （含 179ms→9ms、171ms→<0.1ms 实测；页面无更新日期）
- API keys（publishable/secret、BYPASSRLS、旧 key 2026 年底弃用）：https://supabase.com/docs/guides/api/api-keys
- 角色：https://supabase.com/docs/guides/database/postgres/roles ；https://supabase.com/docs/guides/database/postgres/roles-superuser
- GRANT 与自动暴露：https://supabase.com/docs/guides/api/securing-your-api
- 连接方式与 serverless 配置：https://supabase.com/docs/guides/database/connecting-to-postgres
- 连接数与 Nano 限额：https://supabase.com/docs/guides/platform/compute-and-disk
- 连接管理/池占比：https://supabase.com/docs/guides/database/connection-management
- 用户数据与级联删除：https://supabase.com/docs/guides/auth/managing-user-data
- 迁移：https://supabase.com/docs/guides/deployment/database-migrations
- pgTAP 测试：https://supabase.com/docs/reference/cli/supabase-test-db ；https://supabase.com/docs/guides/database/testing
- PostgREST 事务（源码）：https://github.com/PostgREST/postgrest-docs/blob/main/docs/references/transactions.rst
- `auth.uid()` 定义（源码）：https://github.com/supabase/auth/blob/master/migrations/00_init_auth_schema.up.sql ；https://github.com/supabase/supabase/issues/4794
- Drizzle RLS 与 Supabase 助手（源码）：https://orm.drizzle.team/docs/rls ；https://github.com/drizzle-team/drizzle-orm/blob/main/drizzle-orm/src/supabase/rls.ts ；npm `drizzle-orm@0.45.4`
- Drizzle + Supabase 连接（`prepare:false`）：https://supabase.com/docs/guides/database/drizzle
- Drizzle 迁移：https://orm.drizzle.team/docs/migrations
- PostgreSQL RLS 语义：https://www.postgresql.org/docs/current/ddl-rowsecurity.html （PostgreSQL 18 文档）
