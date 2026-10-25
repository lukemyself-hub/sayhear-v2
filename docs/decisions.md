# ADR 索引

## TL;DR

- 设计、开发或修改具体功能前，先按下方主题和关键词检索，并读取所有命中的 ADR。
- 不无目标地通读全部 ADR。
- 新增 ADR 时在本文件登记编号、标题、状态和主题。

## Status

Draft

## 决策列表

| 编号 | 标题 | 状态 | 主题 |
| --- | --- | --- | --- |
| [0001](adr/0001-database-and-managed-auth.md) | 采用 Supabase Postgres 与 Supabase Auth，初期两库均用 Free 层并自建每日备份 | Accepted | 数据库、托管身份、备份恢复、迁移 |
| [0002](adr/0002-hosting-region.md) | 函数与数据库同置美国东部 | Accepted | 地区、延迟、部署 |
| [0003](adr/0003-provider-phasing-and-fallback.md) | Provider 分阶段与可替换 fallback | Accepted | Provider、fallback、数据外送 |
| [0004](adr/0004-harness-on-ai-sdk.md) | Harness 直接基于 AI SDK 构建 | Accepted | Harness、上下文组装、运行详情 |
| [0005](adr/0005-chat-experience-and-run-record.md) | 聊天中断、fallback 可见性、登录方式与运行记录 | Accepted | 聊天体验、登录、运行记录 |
| [0006](adr/0006-chat-time-budgets.md) | 聊天请求按正文开始前与进行中分段设时间预算 | Accepted | 聊天体验、超时、流式、Vercel 时长 |
| [0007](adr/0007-stage-1-thinking-off.md) | 阶段 1 聊天回复默认关闭思考，首段截止从 15 秒起步 | Accepted | Provider 参数、思考模式、延迟 |
| [0008](adr/0008-continuous-conversation.md) | 连续会话保存消息，日期导航与模型上下文分别组织 | Accepted | 会话、日期导航、上下文、Reflection |
| [0009](adr/0009-server-data-access-and-rls.md) | 服务端以用户身份经 Data API 访问数据库，RLS 兜底 owner 隔离 | Accepted | 数据访问、权限、RLS、owner、特权操作 |
| [0010](adr/0010-minimal-data-contract-and-owner.md) | 阶段 1 最小数据契约：每张产品表直接带 owner，跨表引用同 owner | Accepted | 数据模型、owner、外键、删除、账户清理 |
| [0011](adr/0011-stage-1-login-lifecycle.md) | 阶段 1 登录生命周期：控制台开通、服务端 cookie 会话、登出立即失效 | Accepted | 登录、会话、登出、账号开通、找回密码（延后） |
| [0012](adr/0012-test-environments-and-user-project-guardrails.md) | 三层测试环境与用户库的三道护栏 | Accepted | 测试环境、凭据隔离、项目身份、迁移、Preview |
| [0013](adr/0013-identity-and-isolation-acceptance.md) | 身份与隔离验收分别覆盖应用、数据库、环境护栏和部署链路 | Accepted | 验收、登录续期、登出重放、RLS、环境误配 |
| [0014](adr/0014-web-framework-nextjs-app-router.md) | Web 框架采用 Next.js App Router（Node runtime），以三条护栏约束续期、缓存与入口 | Accepted | Web 框架、cookie 续期、缓存、v1 设计复用、迁移 |
| [0015](adr/0015-message-parts-and-ordering.md) | 消息采用 AI SDK parts，使用独立 seq 排序并保留产品状态 | Accepted | 数据模型、消息、parts、排序、状态、运行记录 |
| [0016](adr/0016-per-request-system-instructions.md) | 每次模型请求显式提供有效产品指令 | Accepted | 每次请求携带指令，仓库独立文件随部署维护；阶段 1 不设独立 system 聊天记录；文件版本仍待确认 |

## 主题检索

| 主题 | ADR |
| --- | --- |
| 数据库与托管身份 | [0001](adr/0001-database-and-managed-auth.md) |
| 身份与隔离验收 | [0013](adr/0013-identity-and-isolation-acceptance.md) |
| 测试环境、凭据隔离与迁移护栏 | [0012](adr/0012-test-environments-and-user-project-guardrails.md) |
| 数据访问、权限与 owner 隔离 | [0009](adr/0009-server-data-access-and-rls.md)、[0010](adr/0010-minimal-data-contract-and-owner.md) |
| 备份与恢复 | [0001](adr/0001-database-and-managed-auth.md) |
| 地区与部署 | [0002](adr/0002-hosting-region.md)、[0014](adr/0014-web-framework-nextjs-app-router.md) |
| Web 框架、页面续期与缓存 | [0014](adr/0014-web-framework-nextjs-app-router.md) |
| Harness 与运行详情 | [0004](adr/0004-harness-on-ai-sdk.md)、[0005](adr/0005-chat-experience-and-run-record.md) |
| 系统指令、每轮上下文与输入快照 | [0004](adr/0004-harness-on-ai-sdk.md)、[0005](adr/0005-chat-experience-and-run-record.md)、[0016](adr/0016-per-request-system-instructions.md) |
| 聊天体验与登录 | [0005](adr/0005-chat-experience-and-run-record.md)、[0011](adr/0011-stage-1-login-lifecycle.md) |
| 数据模型 | [0008](adr/0008-continuous-conversation.md)、[0010](adr/0010-minimal-data-contract-and-owner.md)、[0015](adr/0015-message-parts-and-ordering.md) |
| 消息格式、parts、排序与生成状态 | [0015](adr/0015-message-parts-and-ordering.md) |
| Provider 接入 | [0003](adr/0003-provider-phasing-and-fallback.md) |
| 聊天时间预算、超时与流式 | [0006](adr/0006-chat-time-budgets.md) |
| 思考配置与首段延迟 | [0007](adr/0007-stage-1-thinking-off.md) |
| 连续会话、日期与上下文 | [0008](adr/0008-continuous-conversation.md) |
| Reflection | [0008](adr/0008-continuous-conversation.md)（日期导航与会话边界） |
