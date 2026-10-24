# 证据：服务端会话、账号开通、找回密码、登出与删除撤销

调研 2026-10-23，抓取当日官方文档与 supabase 仓库源码。标注：**官方** / **源码** / **推断**。

## 主会话核查与勘误（2026-10-22，优先于下方原调研）

正式文件已收到，权限放行后子 agent 的 Write 成功。下方保留原报告以便追溯，但不是全部已验证的共识；原报告标注 2026-10-23，与本会话日期不同，版本与源码未提供固定提交链接，易变事实采用前须重核。

- **撤销结论错误（涉及摘要 9–10、决策影响、Q5 与下一步）**：Auth 服务 `/user` 等端点检查 session，不能推导 PostgREST/Data API 同样检查。官方 [Sessions](https://supabase.com/docs/guides/auth/sessions) 与 [SSR advanced guide](https://supabase.com/docs/guides/auth/server-side/advanced-guide) 明确：未过期 JWT 在会话撤销后仍可有效；`getClaims()` 只检查签名与到期，需要发现会话撤销时调用 `getUser()`。ADR 0009 的 RLS 路径不自动满足立即撤销，须在应用请求入口确定检查策略并验收。此问题也存在于用户 JWT 路径，不能仅列为 secret key 路径的 U7。
- **唯一续期点的表述过强（摘要 3、Q1）**：Proxy 是 Next.js 指南采用的集中刷新位置，并非平台唯一能续期的位置；可写 cookie 的服务端入口也能刷新。须正确回写 cookie、禁止缓存认证响应，并验证并发刷新行为，不能把“多处刷新必然随机登出”当成已证实结论。
- **恢复密码不要求旧密码（Q3）**：官方 [Passwords](https://supabase.com/docs/guides/auth/passwords) 的恢复流程是 `verifyOtp({type, token_hash})` 后 `updateUser({password})`；`current_password` 是已登录用户改密可选的确认措施。
- **自有域名恢复链路已核对**：上述 Passwords 页明确给出 `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=recovery&next=/account/update-password` 和服务端 `verifyOtp`。模板需替换默认 ConfirmationURL；应用仍须限制 next 跳转目标，并在实现期测试邮件预取与一次性 token。
- **SMTP 事实与未知分开**：官方 [SMTP](https://supabase.com/docs/guides/auth/auth-smtp) 明确默认服务只发组织团队成员、当前 2 封/小时，自定义 SMTP 初始 30 封/小时可调；该页没写套餐限制，不能据此认定 Free 不支持，或单用户找回密码已结构性不可用。自定义 SMTP 是生产可靠性推荐，是否成为本次前置条件须结合 Luke 的收件地址及发送需求确认。
- **签名密钥影响验签成本，不推翻已接受路径**：U2 可在实施期核实；无需重新决定 ADR 0009。U3 由官方“关闭注册后仅已有用户能登录”支持，具体密码登录仍纳入验收。其余未固定版本的源码推断保留待核，不以源码仓库首页链接当作可复现验证。

## 原调研 TL;DR（有上述勘误，勿独立引用）

1. 服务端授权用 `getClaims()`（**官方**："Always use `supabase.auth.getClaims()` to protect pages and user data"）；`getUser()` 仅在需实时发现"会话已在别处撤销"时用，每次一次网络请求；服务端**绝不能用** `getSession()`（**官方**：*Never* trust it in server code such as Proxy）。
2. 成本取决于签名密钥：非对称（ES256/RS256）时 `getClaims()` 本地验签（JWKS 缓存）；HS256 / 无 kid / 无 WebCrypto 时**源码回落 `getUser()`**，即每请求一次 Auth 往返。
3. 续期只在 proxy；Next.js 16 起 `middleware.ts` 更名 `proxy.ts`（v16.0.0 deprecated），须回写 `Set-Cookie` 与 `Cache-Control: private, no-store`，Proxy 应是唯一刷新点（双重刷新致随机掉线）。
4. `@supabase/ssr` latest `0.12.7`（2026-09-08），**官方文档仍标 beta**："This package is currently in beta… API is still unstable and may have breaking changes"。
5. 服务端用户态请求用 **publishable key**（映射 anon/authenticated，RLS 生效）；**secret key 不进浏览器**（始终 service_role、绕过 RLS）。legacy anon/service_role **官方称 2026 年底弃用**。
6. 找回密码**可完全落在自有域名**：模板 `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=recovery` + 自有路由 `verifyOtp({type, token_hash})`；**官方** reset 页无任何 `*.supabase.co/auth/v1/verify` 链接。默认模板用 `{{ .ConfirmationURL }}` 才指向 supabase.co，**必须替换**。
7. PKCE 是 SSR 默认（**源码** `createServerClient` 写死 `flowType: "pkce"`）；POST `/verify` 传 token_hash 时不得同时带 email/phone/redirect_to（**源码** 400）。
8. 关注册只拦公开 `/signup`（**源码** `signup.go:115`），**admin createUser 不受影响**（**源码** 无 DisableSignup 检查）；内置 SMTP **2 封/小时且只发项目团队成员**，自定义 SMTP 默认 30 封/小时。
9. **登出/删号都不能立即作废已签发 access JWT**（**源码**注释："There is no way to revoke a user's access token jwt until it expires"，默认寿命 1 小时）；但 Supabase 服务端 `requireAuthentication → maybeLoadUserOrSession` 查 `auth.sessions`，登出删行即 403。
10. 因此「登出后会话不能继续读写」**只在走用户 JWT 路径时由平台自动成立**；若用 secret key（无 `session_id` claim、跳过检查），撤销必须我们自实现。

## 对决策的影响

- **数据访问路径与撤销语义耦合（最重要）**：用户 JWT + Data API + RLS 是唯一让 Issue #1「登出后会话不能继续读写」自动满足的选项；secret key + 应用过滤把该验收项变成我们的实现责任，否则最长 1 小时越权窗口。
- **选路径前先确认签名密钥形态**：只有非对称密钥下 `getClaims()` 才是纯本地验签；**官方未说明新项目默认类型**（U2）。
- **Next.js 大版本 + 文件名**：16 已改名 `proxy.ts`。仓库默认 App Router 但**尚无 ADR**，落 ADR 时应锁定大版本与文件名。
- **`@supabase/ssr` 仍 beta**：与 Issue #1「锁定版本」直接相关；升级前须重跑续期/登出/找回密码用例。
- **账号开通已收敛**：dashboard 或 admin createUser 均可绕过关注册，`email_confirm: true` 免验证邮件。**但找回密码仍须自定义 SMTP**，与"两库均 Free"叠加出真实成本项（第三个邮件服务账号）。
- **PKCE + 自有域名 reset 可行且无 `*.supabase.co` 泄漏**，不需 Supabase 自定义域名能力。

## Q1 服务端会话模式

**Next.js 模式（官方 https://supabase.com/docs/guides/auth/server-side/nextjs）**：客户端 `createBrowserClient`（单例），服务端 `createServerClient`（每请求新建）。Next.js 16+ 用 `proxy.ts`；15 及以前必须 `middleware.ts` + `export async function middleware`。`getAll()` 读请求 cookie；`setAll` 第二参数为 cache headers（`Cache-Control`/`Expires`/`Pragma`），"must be applied to the HTTP response to prevent CDNs from caching the response"。Proxy 内 `request.cookies.set` 传给 Server Components、`response.cookies.set` 回传浏览器——"is what keeps users signed in"。必须返回 `setAll` 构建的 `supabaseResponse`（换 response 要先复制 cookie 与三个 cache header）。默认 cookie 名 `sb-<ref>-auth-token`。refresh token 一次性，两处刷新互相踩掉表现为 "users being signed out at random"，**Proxy 应唯一刷新**。

**三者取舍（官方）**：`getClaims()` 每次验签，非对称下本地、对称下走 Auth server，临期先刷新；`getUser()` 从 Auth server 取最新记录，一次网络调用；`getSession()` "reads the session out of the cookie without revalidating it"，仅适合需原始 token 时（如转发）。**关键差别**：`getClaims()` 只验签名与有效期，**不确认 session 仍活跃**——要发现别处撤销必须 `getUser()`（"an unexpired token stays valid even when the session behind it was revoked"）。

**成本（源码 `GoTrueClient.getClaims`）**：`!header.alg || alg.startsWith('HS') || !header.kid || 无 WebCrypto` → `signingKey=null` → 回落 `getUser(token)`；否则 `fetchJwk(kid)`（内存 `JWKS_TTL` 缓存）后本地 `crypto.subtle.verify`。**官方 reference**："If the project is not using an asymmetric JWT signing key (like ECC or RSA) it always sends a request to the Auth server." **官方 signing-keys**：JWKS 在 `/.well-known/jwks.json`，"does not involve Auth server"；edge 缓存 10 分钟 + 客户端内存 10 分钟。

**部署陷阱（官方 advanced guide）**：auth/续期路由禁用 ISR，否则 "the cached response will include the `Set-Cookie` header"，后到访客登录成别人；用户态路由加 `private, no-store`，缓存 key 含 refresh token；Vercel Fluid compute "Always initialize the Supabase client inside the request handler, not at module level"；prefetch 会在 cookie 就绪前打服务端请求。**官方 proxy 页**：Server Function 非独立路由，matcher 排除某路径会跳过该路径上的 Server Function，"Always verify authentication and authorization inside each Server Function rather than relying on Proxy alone"。

**版本**：`@supabase/ssr@0.12.7`（2026-09-08）、`@supabase/supabase-js@2.118.0`（2026-10-15）、`next@16.4.2`（npm registry）。**官方** server-side 页：*"This package is currently in beta."* **源码** `createServerClient` 固定 `flowType:"pkce"`、`autoRefreshToken:false`、`detectSessionInUrl:false`、`persistSession:true`、`skipAutoInitialize:true`，忽略 `auth.storage` 并告警；默认 cookie `{path:"/", sameSite:"lax", httpOnly:false, maxAge:400天}`（**官方** advanced：不需 HttpOnly，浏览器要读 refresh token）。Next.js proxy 页版本史：`v16.0.0` Middleware 废弃并更名 Proxy，Proxy 默认 Node.js runtime；提供 codemod `npx @next/codemod@canary middleware-to-proxy .`。

## Q2 API 密钥（官方 https://supabase.com/docs/guides/api/api-keys）

- `sb_publishable_…`：低权限，"Safe to expose online"；无用户映射 `anon`，有用户映射 `authenticated`，RLS 按用户生效。"Using a publishable key doesn't mean your user is anonymous."
- `sb_secret_…`：始终 `service_role`，绕过 RLS，"must never leave your control"。"A secret key doesn't work in a browser. Supabase matches on the `User-Agent` header and returns HTTP 401."（官方同时说明这层检查不完整，攻击者可用其他工具滥用。）
- 新密钥非 JWT，走 `apikey` header 而非 Bearer；"anything that tries to verify one as a JWT fails."
- legacy anon/service_role：长寿命 JWT，"Legacy version of publishable/secret keys"，**官方称 2026 年底弃用**；"A warning sign of outdated docs is a long key starting with `eyJ`."
- **服务端用户态请求用 publishable key**；secret key 无用户上下文，无法按用户隔离——与 Issue #1「owner 来自可信认证结果」一致。
- **浏览器是否需要 key**：若浏览器永不调用 Supabase，则**推断**无需任何 key，全部留服务端环境变量（官方未逐字陈述）。**张力点**：官方 Next.js 指南仍建 `createBrowserClient` 用于客户端续期；照抄会让 publishable key 与 Supabase URL 进入 bundle（不违背"不直达"的网络边界，但触及密钥暴露边界），见 U5。

## Q3 找回密码只走自有域名（官方 passwords / auth-email-templates / redirect-urls）

- **PKCE**："SSR needs the PKCE flow, which redirects with an auth code that you exchange via `exchangeCodeForSession`"；`@supabase/ssr` 默认 PKCE；**源码**写死 `flowType:"pkce"`。覆盖 Magic Link、OAuth、Sign Up、Password Recovery。**密码登录不需 PKCE 兑换**：**源码** `signInWithPassword` 直接 POST `/token?grant_type=password`，响应体即 session。
- **reset 流程（官方 PKCE 示例）**：服务端 `resetPasswordForEmail(email)` **不带 `redirectTo`**，目标写死在模板；模板 `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=recovery&next=/account/update-password`；自有 `GET /auth/confirm` 读 `token_hash`/`type`/`next`，`verifyOtp({type, token_hash})`，成功后跳改密页（官方给出完整 `app/auth/confirm/route.ts`）。改密 `updateUser({password, current_password})`，`current_password` 需 supabase-js ≥2.102.0。`resetPasswordForEmail()` 不泄露账号是否存在。
- **默认模板会指向 supabase.co**：**官方** email-templates 页确认 `ConfirmationURL` 形如 `.../auth/v1/verify?token={{ .TokenHash }}&type=email&redirect_to=…`；**必须把 `{{ .ConfirmationURL }}` 换成自建链接**。
- **token_hash 约束（源码 `verify.go`）**：POST `/verify` 传 `token_hash` 时不得同时带 `email`/`phone`/`redirect_to`（400 "Only the token_hash and type should be provided"）；`isUsingTokenHash` 要求其余字段皆空。**GET `/verify` 会把 `token` 当 `token_hash`（源码 TODO 计划废弃）并 303 把 code 放 URL query**——正是会经过 supabase.co 的路径，**必须用 POST `verifyOtp`，不要走 GET 重定向**。
- **redirect allowlist**：**官方** 要求 `redirectTo` 匹配 dashboard 列表，支持 `*`/`**`/`?`，生产写精确路径；Site URL 是缺省跳转，"critical for email confirmations and password resets"。**源码** `IsRedirectURLValid`：SiteURL 的 host/scheme/port 全匹配即通过，否则遍历 `URIAllowListMap`；十进制 IP 一律拒、非 loopback IP 拒、怪异 hostname 拒。**官方**：认证失败时 "the user will still be redirected to the redirect URL provided"，错误细节在 fragment。
- **模板变量（官方）**：`ConfirmationURL`、`Token`（6 位 OTP）、`TokenHash`、`SiteURL`、`RedirectTo`。托管项目 dashboard 改，或 Management API `GET/PATCH /v1/projects/$REF/config/auth`（`mailer_templates_*`、`mailer_subjects_*`）。**官方警告**：外部邮件商开链接追踪会改写链接，须关闭追踪与重写；部分服务商会预取链接消耗 token，官方替代方案是模板只放 `{{ .Token }}` 让用户输码，或中间页二次确认。

## Q4 关注册、建单账号、SMTP（官方 general-configuration / rate-limits / auth-smtp）

- **官方**："If this config is disabled, only existing users can sign in." **源码** `signup.go:115`：`if config.DisableSignup { return ErrorCodeSignupDisabled }`。
- **admin createUser 不受影响**：**源码** `adminUserCreate`（`internal/api/admin.go`）全程无 `DisableSignup` 检查；与 GoTrue 上游 `DISABLE_SIGNUP` 语义一致（"only way to create new users is through invites"，管理面保留）。**推断**成立。
- **createUser 细节（源码）**：须给 `email` 或 `phone`；`password` 与 `password_hash` 互斥；**不给 password 会随机生成 64 字符密码**（用户拿不到，需另行设密或 invite）；明文密码走 `checkPasswordStrength`；**官方**示例含 `email_confirm: true` 免验证邮件。
- **两条建号路径**：① dashboard 手动；② admin API `createUser({email, password, email_confirm:true})`，需 secret/service_role，仅服务端（**官方**："This function should only be called on a server."、"Never expose your `service_role` key in the browser."）。
- **SMTP**：内置 **2 封/小时**且**只发项目团队成员**，"Unless you configure a custom SMTP server"，其他收件人报 *Email address not authorized*，**官方**称 "not meant for production use"；自定义 SMTP 默认 **30 封/小时**（可调），"works with any email sending service that supports the SMTP protocol"。
- **限额**：`/recover` 每 IP 30 次/5 分钟，**同一用户 60 秒一次**；sign-up/sign-in 每 IP 30 次/5 分钟；token refresh 150 次/5 分钟；OTP/magic link/confirm 每用户 60 秒。
- **Free 能否自定义 SMTP：unknown**（auth-smtp 页完全不提套餐）。

## Q5 登出与删号的撤销

- **寿命**：**官方** access token "usually between 5 minutes and 1 hour"，**默认 1 小时**；不建议更短（<5 分钟、尤其 <2 分钟会频繁刷新、时钟偏移、破坏提前刷新）；token 至少覆盖最长请求。timeout/lifetime 只在下次 refresh 时执行，真实时长 = 配置值 + JWT 有效期；过期 session 在 24 小时后逐步删除。
- **不可撤销**：**源码** `GoTrueClient.signOut` 注释："There is no way to revoke a user's access token jwt until it expires. It is recommended to set a shorter expiry on the jwt for this reason."
- **登出（源码 `logout.go`/`sessions.go`）**：scope `global`（默认）/`local`/`others`；实现是**删行**：`DELETE FROM auth.sessions WHERE user_id=?` / `WHERE id=?` / `WHERE id!=? AND user_id=?`。`signOut` 带 token 调 `admin.signOut`，404/401/403 忽略，`scope!=='others'` 时清本地 session 与 code-verifier。
- **登出后的 JWT**：**官方** sessions 页——access token 每次使用**不查库**，"an unexpired token stays valid even when the session behind it was revoked"；判断需查 `session_id` 是否仍有行，"only for the most sensitive actions"。**Supabase 自己做了这个检查**：**源码** `requireAuthentication → maybeLoadUserOrSession` 用 `sub` 找 user（无则 403 `User from sub claim in JWT does not exist`）、用 `session_id` 找 session（无则 403 `Session from session_id claim in JWT does not exist`）；`/logout`、`/user` 等挂了该中间件。**源码** `middleware.go` 注释："a JWT remains usable past logout or revocation otherwise. Sessionless admin tokens (e.g. service_role) skip this check."
- **结论**：以**用户 JWT** 打到 Supabase（Data API/PostgREST）时，RLS + session 检查让"登出后不能继续读写"**自动成立**；用 secret/service_role 则必须自实现。
- **删号（官方 reference + 源码 `admin.go`）**：`deleteUser(id, should_soft_delete)`，"Requires a `service_role` key"，仅服务端；`shouldSoftDelete` 必填，"Defaults to false"，软删 "allows user identification from the hashed user ID but is not reversible"。源码：`true` → 软删 user/identities，**硬删** factors、WebAuthn，并 `models.Logout(tx, user.ID)` 清全部 session；`false` → `tx.Destroy(user)`（**推断**：借 `on delete cascade` 连带删 sessions/refresh_tokens）。**源码 migration** `20220811173540`：`sessions.user_id references auth.users(id) on delete cascade`、`refresh_tokens.session_id references auth.sessions(id) on delete cascade`。**官方** deleteUser 页未说明 sessions 处理，上述级联标 **源码/推断**。
- 与 Issue #1「账户清理…撤销可用应用会话」：Supabase 侧会话撤销可由 deleteUser 完成（两种模式都移除 session），**但业务表删除与"备份中仍可恢复"的边界需我们自己的清理逻辑**。

## 未知项

| # | 未知 | 为何重要 | 状态 |
|---|---|---|---|
| U1 | **Free 能否配自定义 SMTP** | 决定找回密码在 Free 层是否结构性可用；不可配则 Luke 若非团队成员收不到邮件，2 封/小时也不够 | 官方无陈述；需 dashboard 实测 |
| U2 | **新项目默认签名密钥 ES256 还是 HS256** | 决定 `getClaims()` 本地验签还是每请求一次 Auth 往返，直接影响延迟与 Q1 成本 | 官方未陈述；查项目 JWKS 端点 |
| U3 | 关注册后 `signInWithPassword` 对已有用户是否可用 | 若不可用则 Luke 自己被锁门外 | **推断**可用（只拦 `/signup`）；需实测 |
| U4 | createUser + `email_confirm:true` 后是否仍要求首登改密 | 影响首登体验与是否需 invite/magic-link 辅助设密 | 需实测 |
| U5 | 纯服务端（不建 browser client）续期是否够用 | 决定 publishable key 能否完全不进浏览器 bundle | **推断**可行；实现期验证 |
| U6 | 自定义模板 Management API key 全集 | 决定模板代码化管理，影响备份/恢复演练能否覆盖 auth 配置 | 官方仅给部分 key 名 |
| U7 | 走 secret key 路径时登出后最长 1 小时越权窗口 | 须自实现 `session_id` 校验或缩短 token 寿命 | 机制已由源码确认；窗口取决于是否实现 |

## 下一步（供决策）

1. 先定**签名密钥形态（U2）**再定数据访问路径——唯一同时影响延迟模型与撤销语义的前置项。
2. **优先评估"用户 JWT + Data API + RLS"**：唯一让「登出后不能继续读写」由平台自动满足的选项，与 Issue #1 验收项和 ADR 0001 最一致。
3. **SMTP（U1）在创建用户库资源前确认**；Free 层上唯一的硬阻塞候选。
4. Next.js 大版本 + `proxy.ts` 文件名 + `@supabase/ssr` 锁版本，一并进 Web 框架 ADR。

## 置信度

Q1/Q2/Q3 **高**（官方逐字 + 源码交叉）；Q4「关注册不阻断 createUser」**中高**（源码无检查 + 上游语义，无官方逐字）；Q5 删号级联 **中高**（源码显式 Logout + migration 级联，官方页未说明）；U1–U7 **未解决**。

## 来源

**官方**：`/guides/auth/server-side/nextjs`、`/server-side/advanced-guide`、`/server-side`、`/guides/api/api-keys`、`/guides/auth/passwords`、`/auth-email-templates`、`/redirect-urls`、`/sessions`、`/signing-keys`、`/rate-limits`、`/auth-smtp`、`/general-configuration`（均在 `https://supabase.com/docs` 下）；`/docs/reference/javascript/auth-{admin-createuser,admin-deleteuser,getclaims}`；https://nextjs.org/docs/app/api-reference/file-conventions/proxy
**源码**：https://github.com/supabase/ssr（`src/createServerClient.ts`、`src/cookies.ts`、`src/utils/constants.ts`）；https://github.com/supabase/auth（`internal/api/{signup,admin,verify,logout,auth,middleware,token}.go`、`internal/models/{sessions,refresh_token}.go`、`internal/utilities/request.go`、`migrations/20220811173540_add_sessions_table.up.sql`）；https://github.com/supabase/auth-js（`src/GoTrueClient.ts`）
**版本**（npm registry，2026-10-23）：`@supabase/ssr@0.12.7`、`@supabase/supabase-js@2.118.0`、`next@16.4.2`
