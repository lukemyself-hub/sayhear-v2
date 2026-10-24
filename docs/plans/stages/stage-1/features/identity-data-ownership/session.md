# 阶段 1 功能接续：登录、服务端身份与数据归属

更新：2026-10-24。来源：Luke 本次指令、[Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1)、[阶段 0 接续](../../../stage-0/session.md)。

## 目标与授权

- 任务是阶段 1 的身份前置设计：只有 Luke 能登录和读写自己的聊天；测试不能触碰用户库。覆盖可信 owner、访问与引用隔离、登录生命周期、环境护栏和验收。
- 当前分支 stage-1/identity-data-ownership，worktree .claude/worktrees/stage-1-identity，基线 df98124。
- 允许调研、讨论、ADR、记录整理和本地 SPEC 草稿。Luke 于 2026-10-24 收尾时另行明确授权整理本 worktree 文档、提交、推送并通过 PR 合入 main；不包含产品实现、资源创建、用户库连接、部署或新增/修改 Issue。后续 session 不继承新的发布授权。
- Luke 2026-10-24 指示将数据结构后半段拆到独立 feature，原始设计目标满足则收尾本功能 SPEC。

## 就绪检查与当前状态

原始方案讨论已收口，可以综合 SPEC；不代表已实现、实测、发布或完整交接。

| 原议题 | 已确认依据 | 结果 |
| --- | --- | --- |
| 服务端身份与访问路径 | [ADR 0009](../../../../../adr/0009-server-data-access-and-rls.md) | 用户令牌经 Data API；逐表 RLS；security invoker 原子写；特权通道隔离 |
| 最小数据归属契约 | [ADR 0010](../../../../../adr/0010-minimal-data-contract-and-owner.md) | owner 直接列；同 owner 组合外键；幂等、单条删除与账户清理边界 |
| 登录生命周期 | [ADR 0011](../../../../../adr/0011-stage-1-login-lifecycle.md) | 控制台开通、邮箱密码、cookie、真实续期、登出后新请求立即拒绝；找回密码延后 |
| 测试环境 | [ADR 0012](../../../../../adr/0012-test-environments-and-user-project-guardrails.md) | 本地/云端测试/用户项目三层；凭据、目标身份与迁移三道护栏 |
| 验收边界 | [ADR 0013](../../../../../adr/0013-identity-and-isolation-acceptance.md) | 应用、数据库、环境与部署分别验证 |
| Web 框架前置 | [ADR 0014](../../../../../adr/0014-web-framework-nextjs-app-router.md) | Next.js App Router Node；可写 cookie 位置续期、私人页 no-store、入口薄 |

长回复身份边界已接受：流开始前续期且有效期覆盖预算、保存余量及锁定 SDK 的临期刷新窗口；失败不启动生成。登出后新请求拒绝，已有回复可在原预算内完成和保存。

## SPEC 与依赖

- 本地临时 [SPEC 草稿](spec-draft.md) 已按既有决定整理并核对范围，未发布；完整阶段执行范围仍以 Issue #1 为准。草稿需在发布或恢复时核对，避免成为第二份长期真源。
- [canonical 数据结构](../canonical-data-model/session.md) 是独立后续讨论，承接消息、会话、run/attempt、输入快照的物理结构。最小 owner 与引用契约继续由 ADR 0010 规定。
- 身份适配与环境护栏可据本规格规划；所有真实产品表的 RLS/外键覆盖、聊天原子写和 checkpoint 集成，需数据结构及聊天功能就绪后实施验证。不能据本功能设计收口宣称整个阶段 ready 或验收完成。
- 下一会话直接到兄弟 feature 讨论系统记录候选方案；本功能草稿保留供后续审阅，字段讨论不再记在本目录。

## 待验证与构建第一步

- 先读 Issue #1、相关 ADR 与本地环境规则，检查工具链和凭据边界。OrbStack 与 Supabase CLI 已同意在进入实施时安装，目前尚未安装或验证。
- 在合成隔离环境实测控制台开通路径、cookie 回写、临期续期和缓存隔离。
- 登出重放以行为为准。不能只凭调用 getUser 宣称立即失效；锁定版本若不检查撤销，补会话存在性检查，不降低验收标准。
- 令牌有效期跨越原到期点的 checkpoint 保存、断流与托管部署差异需要真实验证；未运行。
- 受保护的环境身份初始化、URL/key/ref 混配、sentinel 缺失或探测失败须在写入前中止，并核对目标未改变；未运行。
- 云端测试迁移、Preview 与恢复演练需相应资源和部署授权，未执行。用户库操作另外确认。

## 证据与学习

调研均已返回，无活跃委派。源码结论不是运行通过，使用易变事实前核对锁定版本。

- [Auth 与会话](evidence/auth-server-session-evidence.md)，以顶部勘误为准。
- [数据访问与 RLS](evidence/data-access-and-rls-evidence.md)。
- [测试环境隔离](evidence/test-environment-isolation-evidence.md)，后续 ADR 优先于早期推荐。
- [旧仓库身份经验](evidence/legacy-auth-ownership-findings.md)。
- [流式令牌有效期](evidence/streaming-token-lifetime-evidence.md)。
- [身份学习记录](learning-history.md)，保存理解表现与校准，不代表已掌握。
- 表结构学习与四份相关证据已迁至 [canonical-data-model](../canonical-data-model/session.md)，保留[原讨论历史](../canonical-data-model/discussion-history.md)。
- 回访：特权身份与用户身份如何选择；外键引用方向；PostgREST 请求事务；getUser/getClaims；续期应在 Proxy、Route Handler 或 Server Component 哪层发生。实施时结合实际行为回访。
- 外部学习笔记尚待同步到 /Users/lukemyself/Documents/学习/AI/Agent Harness。worktree 没有 study-notebook 链接，不能宣称已同步。

## 已发生的外部变更与交付限制

Luke 2026-10-23 明确授权后，已用 luke-agents 修改 Issue #1，移除阶段 1 找回密码并细化登出验收。本次拆分与草稿整理不重复修改 Issue。2026-10-24 收尾授权仅交付当前文档改动，交付回执见 [功能索引](../README.md)，实际合入状态以该 PR 为准。
