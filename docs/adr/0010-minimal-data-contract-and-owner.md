---
status: accepted
---

# 阶段 1 最小数据契约：每张产品表直接带 owner，跨表引用同 owner

在 [ADR 0009](0009-server-data-access-and-rls.md) 的 RLS 路径下，确定哪些记录归属于谁、归属如何约束、删除如何传播。只固定行为契约，物理表名与完整列在实施时提出。Luke 于 2026-10-22 确认。

## 决定

- owner 即 Supabase Auth 用户 ID（`auth.users.id`），不另建应用账号表。阶段 1 不需要账号级产品属性；以后需要时再加，不影响已有 owner 列。
- 阶段 1 的 owner 作用域记录：连续会话、消息（用户、assistant、系统、合成工具调用与结果）、run、attempt、输入快照。每类记录**直接**带 `owner_id`，RLS 策略逐表比对本列，不通过连表推断归属。这里列举内容类别，不规定每类各占一行；消息行粒度见 [ADR 0015](0015-message-parts-and-ordering.md)，系统记录的角色与选择规则仍待确认。
- 跨表引用同时带 owner：子记录引用父记录时以 `(owner_id, 父 id)` 组合外键约束，保证两者同属一人。原因是 Postgres 的外键检查绕过 RLS（Postgres 文档 Row Security Policies 一节），仅凭 RLS 无法阻止把自己的 run 挂到他人消息上。只在真实存在的引用上使用，不在无引用的表上冗余铺设。
- 阶段 1 的引用关系与数量：

  | 引用 | 数量 | 用途 |
  | --- | --- | --- |
  | 消息 → 会话 | 一个会话多条消息 | 连续会话容器 |
  | run → 触发它的用户消息 | 一条用户消息可有多个 run（显式重试各为新 run，传输重发不新增） | 重试不覆盖旧回答 |
  | attempt → run | 一个 run 最多两个 attempt（主路线 + 一次 fallback） | 追溯真实路线 |
  | assistant 消息 → 产生它的 run | 一个 run 至多一条 assistant 消息；首段前失败则没有 | 来源链：回答 → run → attempt → Provider/模型 |
  | 输入快照 → attempt | 每次实际发送一份 | 运行详情 |
  | 以上全部 → `auth.users` | — | 账户清理级联 |

- 幂等：run 以 `(owner_id, 客户端请求标识)` 唯一。
- 账户清理：各表对 `auth.users` 外键 `on delete cascade`，由特权通道删除 auth 用户后数据库一次级联清除。
- 单条删除：消息保留一行作为“该消息已删除”占位，带删除时间，**清空行内原文**；历史选择排除已删除消息；过去输入快照中的副本按 ADR 0005 保留并按 owner 隔离。删除不级联到该消息的 run 与快照。

## 重评条件

出现跨 owner 共享的数据（如未来多人共享内容）；需要账号级产品属性；组合外键带来的迁移或查询复杂度明显超过其防护价值；需要撤销删除。
