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

## 主题检索

| 主题 | ADR |
| --- | --- |
| 数据库与托管身份 | [0001](adr/0001-database-and-managed-auth.md) |
| 备份与恢复 | [0001](adr/0001-database-and-managed-auth.md) |
| 地区与部署 | [0002](adr/0002-hosting-region.md) |
| Harness 与运行详情 | [0004](adr/0004-harness-on-ai-sdk.md)、[0005](adr/0005-chat-experience-and-run-record.md) |
| 聊天体验与登录 | [0005](adr/0005-chat-experience-and-run-record.md) |
| 数据模型 | [0008](adr/0008-continuous-conversation.md) |
| Provider 接入 | [0003](adr/0003-provider-phasing-and-fallback.md) |
| 聊天时间预算、超时与流式 | [0006](adr/0006-chat-time-budgets.md) |
| 思考配置与首段延迟 | [0007](adr/0007-stage-1-thinking-off.md) |
| 连续会话、日期与上下文 | [0008](adr/0008-continuous-conversation.md) |
| Reflection | [0008](adr/0008-continuous-conversation.md)（日期导航与会话边界） |
