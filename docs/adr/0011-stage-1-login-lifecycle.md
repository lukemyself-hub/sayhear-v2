---
status: accepted
---

# 阶段 1 登录生命周期：控制台开通、服务端 cookie 会话、登出立即失效

在 [ADR 0001](0001-database-and-managed-auth.md)（Supabase Auth）、[ADR 0005](0005-chat-experience-and-run-record.md)（邮箱密码）与 [ADR 0009](0009-server-data-access-and-rls.md)（用户 JWT + Data API + RLS）之下，确定阶段 1 的账号开通、会话校验与登出语义。证据见 `docs/plans/stages/stage-1/features/identity-data-ownership/evidence/auth-server-session-evidence.md`（以文件顶部勘误为准）。Luke 于 2026-10-23 确认。

## 决定

- 范围：阶段 1 只做账号开通、登录、续期、登出。**找回密码延后**，因此阶段 1 不发送任何邮件，不依赖 SMTP。Issue #1 已同步修改。
- 开通：关闭公开注册。Luke 的账号由人在用户项目的 Supabase 控制台手动创建，并标记邮箱已确认；应用不提供开通入口，也不持有用于开通的特权凭据。测试项目中的合成主体由测试装载流程经特权通道创建（ADR 0009）。
- 会话：浏览器只访问应用域名。服务端使用锁定版本的 `@supabase/ssr` 维护 cookie 会话，续期时回写 Set-Cookie，认证响应设置 `Cache-Control: private, no-store`，Supabase client 每个请求新建。服务端不以 `getSession()` 作为身份依据。
- 登出立即失效：读写私人数据的请求（聊天、读取历史、删除等）在服务端入口用 `getUser()` 向 Auth 确认会话仍然有效，再用该用户令牌访问 Data API。不读写私人数据的请求可以用 `getClaims()` 本地验签。验收标准：登出后，用登出前复制的 cookie 发起的读写请求立即被拒绝。
- 流式边界（Luke 2026-10-23 接受）：登出成功后新发起的私人数据请求立即拒绝；已通过入口检查并开始的回复允许在原时间预算内完成与保存。入口检查不等于整个流期间持续检查撤销，不承诺登出会取消已有请求。令牌续期在流开始前完成，见 ADR 0009。
- 理由：access token 默认约 1 小时有效，登出只删除服务端会话记录。`getClaims()` 与 Data API 只检查签名和到期时间，发现不了已撤销的会话；只有入口处的 `getUser()` 才能兑现“登出后不能继续读写”。代价是每个此类请求多一次到 Auth 的往返（同区域，量级待实测），相对模型首段等待可以忽略。

## 实施期验证项

- 新项目签名密钥类型（非对称或 HS256），影响 `getClaims()` 是否本地完成。
- 关闭注册后，控制台创建的账号可以用 `signInWithPassword` 登录，且首次登录不强制改密。
- 实测 `getUser()` 的往返耗时。
- 长回复期间令牌过期对流式 checkpoint 写入的影响（与 ADR 0009 共同处理）。

## 重评条件

需要找回密码、多人账号或自助注册；`getUser()` 往返成为可感知的延迟；Supabase 提供能在 Data API 层检查会话撤销的机制；`@supabase/ssr` 的稳定版本改变推荐做法。
