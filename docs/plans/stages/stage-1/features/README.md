# 阶段 1 功能讨论索引

完整阶段范围以 [Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1) 为准。以下是本地设计讨论与临时草稿，不代表已实现或授权发布。

| 功能 | 状态 | 入口 |
| --- | --- | --- |
| identity-data-ownership：登录、服务端身份与数据归属 | 设计已收口，SPEC 草稿待审阅和发布授权，验收未运行 | [接续](identity-data-ownership/session.md)、[草稿](identity-data-ownership/spec-draft.md)、[学习记录](identity-data-ownership/learning-history.md) |
| canonical-data-model：消息与运行数据结构 | 通用约定和 AI SDK parts 已接受，完整 schema 尚未收口 | [接续](canonical-data-model/session.md)、[讨论历史](canonical-data-model/discussion-history.md)、[ADR 0015](../../../../adr/0015-message-parts-and-ordering.md) |

下一会话从 canonical-data-model 的[接续记录](canonical-data-model/session.md)恢复。消息行粒度、run 关联、删除清空与并发保护已接受；停点为尚未确认的系统记录方案，之后讨论合成工具记录、会话、run/attempt 和快照布局。两项功能共享 ADR 0010 的归属契约，字段设计不回写到身份功能讨论中。

2026-10-24 Luke 授权整理当前 worktree 文档并合入 main。本轮交付只覆盖文档与接续，不代表产品已实现、验收已运行，或身份 SPEC 草稿已发布为执行 Issue。交付 PR 创建后在此登记；合入状态以 GitHub 回执为准。
