---
status: accepted
---

# 服务端以用户身份经 Data API 访问数据库，RLS 兜底 owner 隔离

阶段 1 需要保证每个人只能读写自己的消息、运行与输入快照，且应用代码某处漏写过滤时不泄露数据（Issue #1：owner 来自可信认证，数据库权限策略须经跨主体验证，绕过 RLS 的凭据不进浏览器）。

## 决定（Luke 于 2026-10-22 确认）

- 请求路径：服务端用 `@supabase/ssr` 从 cookie 取得并验证用户会话，再以该用户令牌通过 supabase-js（Data API）访问数据库。数据库以 `authenticated` 角色执行，所有 owner 作用域表启用 RLS，策略比对每行 `owner_id` 与 `(select auth.uid())`。查询侧仍显式按 owner 过滤，RLS 是兜底而非唯一防线。
- 原子写：“保存用户消息 + 创建 run + 创建 attempt”由一个 `security invoker` 的 Postgres 函数一次完成，仍受 RLS 约束；幂等靠 owner 作用域的唯一约束。
- 特权通道：Secret key 仅用于没有用户令牌的少数操作——关闭注册下开通账号、账户清理删除 auth 用户、测试合成主体装载、备份。集中在独立模块，不进入请求路径的通用客户端。
- 请求开始时确认用户令牌剩余有效期覆盖本次运行预算与保存收尾余量，不足先续期；续期及 Set-Cookie 必须在返回流式响应前完成。续期后仍不足或续期失败，不启动生成。沿用 ADR 0006 的低于 300 秒总预算，实施时须额外考虑锁定 SDK 的临期自动刷新窗口，避免流中刷新导致浏览器 cookie 未同步；不能依赖 SDK 中途刷新兜底。仍以用户身份写入，不切换特权凭据。
- Luke 于 2026-10-23 确认流式登出边界：登出成功后的新请求立即拒绝，已通过入口检查并开始的回复允许在原预算内完成和保存，不新增运行中撤销轮询。资料和待验证项见[流式令牌核查](../plans/stages/stage-1/features/identity-data-ownership/evidence/streaming-token-lifetime-evidence.md)。
- 迁移以 Supabase CLI SQL migration 为单一真源，RLS 与授权语句一并纳入。

## 选项与取舍

| 选项 | owner 由谁保证 | 漏写过滤时 | 主要代价 |
| --- | --- | --- | --- |
| A 用户令牌 + Data API + RLS（推荐） | 数据库 | 读为空、写被拒 | 多表原子写须写成数据库函数；每次查询经 HTTP |
| B 直连 SQL + 逐事务切换角色与 claims | 数据库，前提是每次切换 | 若漏切角色，以表 owner 身份绕过 RLS，且测试可能仍通过 | Drizzle 无官方运行时支持，需自建；连接池需 transaction mode 配置 |
| C Secret key + 应用过滤 | 仅应用代码 | 泄露 | 与 Issue #1 冲突；旧仓库即此路径，RLS 曾被列为后补 |

依据见[数据访问与 RLS 证据](../plans/stages/stage-1/features/identity-data-ownership/evidence/data-access-and-rls-evidence.md)与[旧仓库经验](../plans/stages/stage-1/features/identity-data-ownership/evidence/legacy-auth-ownership-findings.md)。

## 数据库函数的边界（Luke 讨论补充，2026-10-22）

- 原子写须进数据库函数是 A 特有代价：B/C 持有直连连接，可在应用代码里开事务连续执行多条语句；Data API 每个 HTTP 请求各自一个事务，无法跨请求。
- 函数只做原子写与幂等判断，不承载上下文选择、Provider 或重试等业务逻辑。
- 函数与服务端分开发布，接口保持薄且稳定：先执行迁移、再部署服务端；变更只做向后兼容的追加，需要不兼容修改时新增函数，服务端切换后再删除旧函数。
- 可迁移性：函数本身是标准 Postgres（PL/pgSQL），可迁到其他 Postgres。耦合点在 Supabase 特有的 `auth.uid()`、`authenticated` 角色与 Data API；owner 读取收敛到一个本项目的辅助函数，迁移时只改一处。A 整体比 B 更依赖 Supabase，但身份本身已因 ADR 0001 绑定 Supabase Auth。
- 测试：pgTAP 在本地栈直接验证函数（两主体、伪造 owner、重复提交）；经服务端的两令牌端到端测试验证接口契约。两者均随每次 CI 自动运行。

## 重评条件

数据库函数承载的业务逻辑明显增多而难以测试维护；Data API 时延成为聊天瓶颈（需同区实测）；Drizzle 或 Supabase 提供官方的按请求角色切换运行时支持；需要长事务或跨请求会话状态。

## 待验证

Data API 与直连的同区时延差；Free 项目 Data API 速率限制；表 owner 角色与 RLS 绕过行为须在测试库确认；跨主体隔离以两个真实用户令牌的端到端测试证明，pgTAP 只证明策略本身。
