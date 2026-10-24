# 测试环境隔离证据：本地 Supabase 与远端测试 Free 项目

核查日期：2026-10-22。范围：仅回答 `session.md` 决策点 4/5（本地栈与远端测试项目分工、两库身份判定、env 布局、合成装载、迁移防误推）。未运行 `supabase` CLI、未连接任何项目、未创建云资源。标签：**官方文档** / **源码** / **推断**。

## TL;DR

- **推荐三层**：本地 Docker 栈跑自动测试、RLS/pgTAP、Auth 流程与合成装载；远端测试 Free 项目只做「部署前预检 + Preview smoke + 迁移演练」；用户 Free 项目只跑真实 smoke，永不进入测试进程。
- **本地栈不计入 2 个 active project 上限**（推断，见 §1），所以本地栈 + 测试项目 + 用户项目可共存。
- **身份判定不能靠库名**（两边都是 `postgres`）。可靠信号是 **project ref**：URL host（`<ref>.supabase.co`）、`supabase/.temp/project-ref`、以及 legacy key 的 `ref` claim。**`iss` 在托管项目上是 `https://<ref>.supabase.co/auth/v1`**（源码 + 推断）。
- **护栏形态**：一次性写入的 sentinel 行 + 启动时双向校验（URL↔key 同项目、ref↔期望值、sentinel↔env 类别），任一项不匹配**在写入前 fail closed**。仅靠 URL 或仅靠 DB 名都不够。
- **测试进程永远看不到用户凭据**：用户库变量只在 `.env.local`/Vercel Production 出现；测试 runner 用 `.env.test`（Next.js 在 `NODE_ENV=test` 下**不加载** `.env.local`）。
- **迁移**：本地 `db reset` → 测试项目 `db push` → 用户项目只在授权窗口内人工 `db push`。CLI 的「已 link 的项目」是单一状态，误推风险主要来自 link 状态残留，需在命令前显式校验 ref。

## 1. 本地栈 vs 远端测试项目

| 用途 | 本地 CLI 栈 | 远端测试 Free 项目 |
| --- | --- | --- |
| 自动测试（每次提交/PR） | 首选。可 `db reset`、可反复装载、无网络依赖 | 不适合高频：Free 会闲置暂停，reset 有延迟 |
| Auth 邮件流程（确认、找回密码、改邮箱） | 首选。本地邮件被**捕获而非发送**，Web UI 在 `54324` | 受默认 SMTP 限制：仅组织成员地址、**2 封/小时**、best-effort |
| RLS / pgTAP | 首选。`supabase test db`，事务内 `begin/rollback` | 可跑但慢、会污染数据、需清理 |
| 合成数据集装载 | 首选（`seed.sql` + 幂等脚本） | 用于验证「远端装载路径」，低频 |
| 迁移演练 | `db reset` 全量重放 | **必做**：验证 `db push` 在真实托管 Postgres 上成立 |
| 部署 smoke（Preview/Vercel） | 不能替代（无托管网络/池化/TLS） | 必做 |
| 恢复演练 | 不适用 | 必做（ADR 0001 要求） |

**2 个项目上限**：官方定价页原文「Free projects are paused after 1 week of inactivity. Limit of 2 active projects.」本地栈是 Docker 容器、不注册到平台，**不计入**（推断：官方未逐字说明，但「active projects」指平台项目；本地 `init` 明确「doesn't sign you in or connect the directory to a project on the Supabase Platform」——官方文档）。风险：若推断错误，本地栈也不会占额，因为根本没有平台侧实体。

**资源**：本地栈是 10+ 容器（Postgres、Kong/API gateway、Auth/GoTrue、PostgREST、Realtime、Storage、Studio、Edge Runtime、analytics、本地 SMTP）。官方文档**未给最低内存**；社区经验 4 GB 起步、8 GB 舒适（第三方，非官方，标 unknown）。macOS 推荐 OrbStack（官方文档）。端口固定导致**一台机器同时只能跑一个本地栈**；多 worktree 并行需改端口或实验性 `supabase stack`（官方文档，标 unknown 是否已 GA）。

**Parity 缺口**（官方文档 + 推断）：

| 项 | 本地 | 托管 | 影响 |
| --- | --- | --- | --- |
| 连接池 | `[db.pooler]` 默认 `enabled = false`，端口 54329（源码 config.toml） | Supavisor：6543 transaction / 5432 session；shared pooler IPv4-only（官方） | 本地测不出池化行为；直连 SQL 的会话/事务语义须在托管验证 |
| 直连地址 | `localhost:54322` | `db.<ref>.supabase.co:5432`，**IPv6**（官方） | 本机网络环境不暴露 IPv6 问题 |
| 邮件 | 捕获，无投递 | 默认 SMTP 2 封/小时、仅组织成员；生产需自建 SMTP | 本地通过 ≠ 远端能发信 |
| 签名密钥 | 默认对称 secret（源码 `defaultJwtSecret`） | 新项目可用非对称 ES256/RS256 + JWKS（官方） | 本地默认路径与托管默认不同；验证逻辑要覆盖两种 |
| 新 key 格式 | 本地生成 `sb_publishable_`/`sb_secret_`（官方 CLI 文档） | 新项目默认新 key，legacy 2026 年底弃用（官方） | 不要写死 legacy JWT 解析 |
| Edge/analytics | 有但非生产同构 | — | 阶段 1 不依赖 |

## 2. 「我在跟哪个项目说话」

**不可靠信号**

- 数据库名：两边都是 `postgres`（Issue #1 明确要求不得据此判定）。`current_database()` 只回答「连到了某个 Postgres」，不回答「是哪个项目」。
- 单独看 URL：能拿到 ref，但**不能证明 key 属于同一项目**（混配场景）。
- 单独看 key：legacy key 的 `ref` claim 可读，但**新式 `sb_secret_...` 不是 JWT**（官方：「Publishable and secret keys are short strings, not JWTs」），没有可解 claim。

**可靠信号（按强度）**

1. **URL host 的 ref**：`https://<project_ref>.supabase.co/rest/v1/`（官方 REST 文档）。解析 host 第一段；本地为 `127.0.0.1:54321`，ref 记为 `local`。
2. **legacy key 的 `ref` claim**：CLI 源码 `CustomClaims{ Issuer "iss,omitempty"; Ref "ref,omitempty"; Role ... }`（`apps/cli-go/pkg/config/apikeys.go`）。托管 legacy key 的 payload 形如 `{"iss":"supabase","ref":"<ref>","role":"service_role"}`（**推断**：源码显示 CLI 本地生成时 `Ref` 为空、`Issuer="supabase-demo"`；托管侧填 ref 的行为未见官方逐字文档 → 标 unknown，实施时用真实 key 解码确认）。
3. **用户 access token 的 `iss`**：GoTrue `AccessTokenClaims` 内嵌 `jwt.RegisteredClaims`，`Issuer = config.JWT.Issuer`（源码 `internal/tokens/service.go`）；自托管 compose 设 `GOTRUE_JWT_ISSUER: ${API_EXTERNAL_URL}`（源码）。托管 `API_EXTERNAL_URL` 为 `https://<ref>.supabase.co/auth/v1`，故 `iss` 含 ref（**推断**，未取得托管实例实测）。官方 JWT 文档只写「`iss` identifies the server which issued the token」并给出 `https://project_id.supabase.co/auth/v1` 示例。
4. **JWKS 端点**：`https://<ref>.supabase.co/auth/v1/.well-known/jwks.json`（官方）。能取到即证明该 ref 存在；不能证明「这就是我配的那个」。
5. **sentinel 行**：应用表 `environment_identity(singleton bool primary key default true, env_kind text, project_ref text, dataset_version text, created_at)`。每个环境**一次性**写入，之后只读。

**混配检测（关键）**：URL 来自项目 A、key 来自项目 B 时，PostgREST/Auth 会以 `Invalid API key`/401 拒绝（推断，基于 key 由项目 JWT secret 签名）。但**不能把「请求失败」当作唯一护栏**——它发生在连接之后，且新式 secret key 的行为可能不同。推荐在**进程启动时**做主动探测：

```
resolveIdentity(env):
  refFromUrl   = parseRef(SUPABASE_URL)            // 本地 => "local"
  refFromKey   = legacyJwtRef(SUPABASE_SECRET_KEY) // 非 JWT => null（合法）
  expect       = env.ENVIRONMENT_KIND              // "local" | "test" | "user"
  assert refFromUrl == env.EXPECTED_PROJECT_REF    // 显式变量，不靠推断
  assert refFromKey == null || refFromKey == refFromUrl
  row = select * from environment_identity          // 读，不写
  assert row.project_ref == refFromUrl
  assert row.env_kind == expect
  if expect != "local" and not TEST_ALLOW_REMOTE:   // 测试进程默认禁止远端
     assert expect == "test"                        // "user" 在测试进程里直接拒绝
```

失败即抛错并中止，**任何写入之前**。sentinel 的写入是独立的、需人工授权的 bootstrap 步骤（`supabase db push` 后运行一次脚本），不放在应用启动路径里（否则启动路径会写库）。

**对决策的影响**：护栏必须是「多信号一致 + 显式期望值 + 读 sentinel」，不是单一 check。`env_kind` 与 `project_ref` 都存进 sentinel，使得「用户项目被误标成 test」也能被独立变量挡住。

## 3. Env 布局（Next.js + Vercel）

Next.js 加载顺序（官方，2026-08-25 更新）：`process.env` → `.env.$(NODE_ENV).local` → `.env.local`（**`NODE_ENV=test` 时跳过**）→ `.env.$(NODE_ENV)` → `.env`。

| 文件 | 提交 | 内容 | 谁读 |
| --- | --- | --- | --- |
| `.env.example` | 是 | 变量名 + 说明，无真实值 | 人 |
| `.env` | 否 | 共享非密钥默认（如 `SUPABASE_URL=http://127.0.0.1:54321` 不适用，见下） | — |
| `.env.local` | 否（Next 默认 gitignore） | **用户库**凭据 + 本地开发指向本地栈 | `next dev`（development） |
| `.env.test` | 是（Next 官方建议入库） | **测试项目**的非密钥配置；密钥用 `.env.test.local` | 测试 runner（`NODE_ENV=test`） |
| `.env.test.local` | 否 | 测试项目的 secret（仅当必须连远端测试项目时） | 测试 runner |
| `.env.development.local` | 否 | 可选覆盖 | `next dev` |

要点：

- **测试进程看不到用户凭据**：因为 `.env.local` 在 `NODE_ENV=test` 下不加载（官方原文：「`.env.local` won't be loaded, as you expect tests to produce the same results for everyone」）。这是最强的结构性保证——即使 `.env.local` 里写着用户库 URL，`vitest`/`jest` 也读不到。
- 变量命名分离：`SUPABASE_URL` / `SUPABASE_SECRET_KEY`（应用，按环境注入）与 `TEST_SUPABASE_URL` / `TEST_SUPABASE_SECRET_KEY`（仅测试）。装载器**只读 `TEST_*`**，且 `TEST_SUPABASE_*` 缺失即失败，不回退到 `SUPABASE_*`。
- `ENVIRONMENT_KIND` + `EXPECTED_PROJECT_REF` 显式声明；loader 用它做 §2 的断言。
- **不要**把 `NEXT_PUBLIC_` 用于任何 Supabase 凭据（Issue #1：浏览器不直连 `supabase.co`；且 `NEXT_PUBLIC_` 在 build 时内联）。

**Vercel 三环境**（官方）：

| Scope | Supabase 指向 | 变量 |
| --- | --- | --- |
| Production | 用户 Free 项目 | `SUPABASE_URL`/`SUPABASE_SECRET_KEY`（Secret 类型） |
| Preview | **测试 Free 项目** | 同名变量，值为测试项目（Secret 类型） |
| Development | 本地栈 | `vercel env pull` 拉到 `.env`；Secret 值 Vercel 读不回，本地需手填（官方：Secret 无法读回，`vercel env pull` 会写占位符） |

- Preview 指向测试项目是**推荐**：Preview 部署可跑真实 smoke，且不会碰用户数据。代价：Preview 与 Production 共享同一个测试项目，并发 Preview 会互相污染 → 用 per-branch 变量或串行 smoke。
- 可开启团队策略 **Separate Production Secret Values**（官方），强制 Production 的 secret 与 Preview 不同值，从平台侧防止误配同值。
- 变更 env 只对新部署生效（官方），改完需 redeploy。
- `vercel env pull --environment=preview` 可拉 Preview 变量，但 Secret 类型拿不到真实值（官方）。因此**测试凭据不要依赖 Vercel 下发**，用本地 `.env.test.local`。

## 4. 合成数据与两个主体

- `supabase/seed.sql` 在**首次 `supabase start`** 与**每次 `supabase db reset`** 后、迁移完成后执行（官方）。可用 `[db.seed] sql_paths` 拆多文件（官方）。
- `seed.sql` **不负责 auth 用户**（官方页未覆盖）；auth 用户用 Admin API `createUser`，`email_confirm: true` 使账号立即可用（官方测试指南示例）。`createUser` 可传 `id`/`user_metadata` 等（官方参考页仅列 `attributes`，具体字段未逐项文档化 → 标 unknown；官方测试指南的 TypeScript 示例确实用 `email_confirm`）。
- **可重复装载**：Admin API 对重复邮箱报错，脚本需「先按邮箱查、存在则复用 id」。更稳的做法是**固定 UUID**：`createUser({ id: <fixed-uuid>, email, password, email_confirm: true })`（推断：字段未在官方参考页逐项列出，需实测确认）。业务表 seed 用固定 UUID + `on conflict do nothing/update`，保证幂等。
- **两个主体**：`subject-a@test.invalid`、`subject-b@test.invalid`，UUID 固定并写进 seed 常量文件；数据集版本号写进 `environment_identity.dataset_version`。
- **`db reset` 的边界**（官方）：本地默认只重置本地栈（「Requires the local development stack to be started」）；`--linked` / `--db-url` 会重置远端并「drop all user created entities」。**绝不对用户项目使用 `--linked`**。
- **只重置测试项目**：不推荐用 `db reset --linked`（会 drop 全部用户对象、且 Free 层慢）。推荐「先验证 ref，再 `db push` + 幂等 seed 脚本」，或接受 `db reset --linked` 但前置 §2 的 ref 断言 + 二次确认。阶段 1 数据量小，`db reset --linked` 在测试项目上可接受；关键是**命令前打印并比对 ref**。

## 5. 迁移流

```
改 schema → supabase migration new <name> (或本地 Studio + db diff)
        → supabase db reset (本地，验证全量重放 + seed)
        → supabase test db (pgTAP/RLS)
        → [授权] supabase link --project-ref <TEST_REF>; supabase db push --dry-run; supabase db push
        → 测试项目 smoke + 恢复演练
        → [独立授权] link --project-ref <USER_REF>; db push --dry-run; db push
```

- `db push` 需要先 `link`；`--dry-run` 只打印将应用的迁移（官方）。
- **link 状态是单一、有状态的**：存在 `supabase/.temp/project-ref`（源码 `temp-paths.ts`），且 CLI 的 init gitignore 模板忽略 `.temp`（源码 `INIT_GITIGNORE_TEMPLATE`）。误推风险来自「上一步 link 的是用户项目，下一步忘了切回」。
- **防误推**（推断，需实施验证）：
  1. 迁移命令统一走包装脚本：读 `supabase/.temp/project-ref`，与 `TEST_PROJECT_REF` 比对，不符即退出；用户项目推送需显式 `--allow-user-project` + 交互确认。
  2. 用 `--project-ref` 而非依赖已 link 状态（部分命令支持；`db push` 本身走 linked 状态，需先 `link`）。
  3. CI 只用 `TEST_PROJECT_REF`/`TEST_DB_PASSWORD` 的 GitHub secret（官方 managing-environments 模式），用户项目凭据**不进 CI**。
  4. 用户项目推送只在本地、授权窗口内人工执行，且先 `db push --dry-run` 人工核对。
- 本地与远端 Postgres 大版本必须一致（config.toml 注释：「This has to be the same as your remote database's」）；本地模板默认 `major_version = 17`（源码），须与托管核对。

## 对决策的影响

1. **分工**：本地栈承担全部自动测试、RLS、Auth 邮件、合成装载；远端测试项目承担迁移演练、Preview smoke、恢复演练。这与 Issue #1「四个验证层面」一致，且不消耗额外项目额度。
2. **护栏**：采用「显式 `EXPECTED_PROJECT_REF` + URL/key/sentinel 三方一致 + 测试进程禁止 `env_kind=user`」；拒绝以库名或单一 URL 判定。`iss`/`ref` claim 作为辅助信号，不作为唯一依据（托管 `ref` claim 未逐字文档化）。
3. **Env**：测试凭据只放 `TEST_*` + `.env.test(.local)`，利用 Next.js 在 test 模式跳过 `.env.local` 的结构性隔离；Vercel Preview 指向测试项目。
4. **装载**：seed 负责业务表，Admin API 负责两个主体；固定 UUID + `on conflict` 保证可重复。
5. **迁移**：包装脚本 + `--dry-run` + CI 只持测试凭据；用户项目推送为人工、显式授权步骤。
6. **学习点**：可向 Luke 演示「同一份 `.env.local` 在 `NODE_ENV=test` 下为何读不到」以及「混配 URL/key 时错误发生在哪一层」。

## 未知 / 需实测

- 托管 legacy key 的 `ref` claim 是否确实填写（源码只证明 CLI 本地生成时为空）。
- 托管 access token 的 `iss` 实际值是否为 `https://<ref>.supabase.co/auth/v1`（推断自 compose 的 `API_EXTERNAL_URL`）。
- 新式 `sb_secret_...` 是否有任何可读的项目标识（官方明确「not JWTs」；是否随请求回显 ref 未知）。
- 本地栈实际内存占用（官方无数字）。
- 多 worktree 并行跑本地栈的端口方案是否稳定（`supabase stack` 实验性）。
- `createUser({ id })` 是否被 Admin API 接受（官方参考页未列字段）。
- Free 项目 `db reset --linked` 的实际耗时与限流行为。
- Vercel Preview 并发部署共享测试项目时的数据竞争程度。

## 来源

- 官方文档（均 2026-10-22 获取）：`/guides/local-development`（端口、OrbStack、「never expose publicly」）、`/guides/local-development/cli/getting-started`（端口表、`--no-backup`）、`/guides/local-development/seeding-your-database`（seed 时机、`sql_paths`）、`/guides/local-development/cli/config`（`[local_smtp]`、`auth.email.smtp` 默认 `inbucket:2500`）、`/guides/local-development/testing/overview`（pgTAP、`supabase test db`、`email_confirm`）、`/guides/database/connecting-to-postgres`（6543/5432、IPv6）、`/guides/auth/auth-smtp`（2 封/小时、仅组织成员）、`/guides/auth/signing-keys`、`/guides/auth/jwts`（`iss` 语义）、`/guides/api/api-keys`（新 key 非 JWT、secret 绕过 RLS、legacy 2026 底弃用）、`/reference/cli/supabase-db-push`、`/reference/cli/supabase-db-reset`、`/guides/deployment/managing-environments`
- 官方文档：https://nextjs.org/docs/app/guides/environment-variables（2026-08-25，加载顺序、test 跳过 `.env.local`）、https://vercel.com/docs/environment-variables（2026-09-17）、https://vercel.com/docs/environment-variables/sensitive-environment-variables（2026-08-28）、https://vercel.com/docs/cli/env（2026-08-20）
- 源码 `supabase/cli`：`apps/cli-go/pkg/config/apikeys.go`（`CustomClaims{Issuer,Ref}`）、`apps/cli/src/command-internal/temp-paths.ts`（`.temp/project-ref`）、`apps/cli/src/shared/init/project-init.templates.ts`（`INIT_GITIGNORE_TEMPLATE`、默认 config）
- 源码 `supabase/auth`：`internal/tokens/service.go`（`AccessTokenClaims`、`Issuer`）、`internal/conf/configuration.go`（`JWTConfiguration.Issuer`）
- 源码 `supabase/supabase`：`docker/docker-compose.yml`（`GOTRUE_JWT_ISSUER: ${API_EXTERNAL_URL}`）
