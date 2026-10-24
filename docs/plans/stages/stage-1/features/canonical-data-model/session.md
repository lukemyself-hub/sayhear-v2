# 阶段 1 功能接续：canonical 数据结构与消息存储

更新：2026-10-24。来源：Luke 本次会话与 [Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1)。按 Luke 要求，从 [身份与数据归属](../identity-data-ownership/session.md) 拆出。共用当前讨论分支，不代表授权创建新分支或实现。

## 目标与边界

- 明确连续会话、消息、run、attempt 与实际输入快照的物理结构、约束和生命周期，为阶段 1 canonical 闭环准备规格。
- 继承 [ADR 0010](../../../../../adr/0010-minimal-data-contract-and-owner.md) 的 owner、同 owner 引用、幂等和删除契约。身份来源、RLS 路径、登录与环境边界由兄弟 feature 管理，本功能只细化数据形状。
- Luke 于 2026-10-24 收尾时明确授权整理本 worktree 文档、提交、推送并通过 PR 合入 main。本次授权不包含产品实现、云资源、用户库连接、部署或修改 Issue #1。后续 session 不继承新的发布授权。
- 尚未完成完整数据结构设计或 SPEC。完整阶段执行范围以 Issue #1 为准；本功能细化仍需后续发布。

## 已确认

以下由 Luke 于 2026-10-24 确认，已汇总进 [ADR 0015](../../../../../adr/0015-message-parts-and-ordering.md)；原始依据与理解证据见 [讨论历史](discussion-history.md)。

- id 用 UUIDv7，通常由数据库生成，需要提前知道时由服务端生成。客户端 id 不直接作为数据库主键，仅用作幂等键。目标 Supabase/Postgres 是否内置 uuidv7() 在实施时核实。
- 时间用 timestamptz。自定义状态用 text + CHECK；SDK/Provider 原始值不以 CHECK 穷举，逻辑依赖前先映射到自定义状态。
- 消息增加 seq 专用于稳定排序。用户消息与回答不必相邻，按消息出现顺序展示；序号一经确定，流式更新不重新排序。identity 不保证事务提交或网络到达顺序，实施时须明确分配规则与客户端合并行为。
- 消息内容采用 AI SDK parts，存 jsonb，不提前设计自有 parts 或转换层。未来实际不兼容时，再选择保留旧格式并读取时转换或迁移。格式版本标签的具体列尚未确定。
- 消息生成状态为 generating / complete / interrupted，与 deleted_at 分开。
- 阶段 1 不接外部观测工具，继续按 ADR 0005 将运行记录存于 SayHear。未来可仅对新运行接入，无须强制迁移历史；历史导入能力、费用与耗时届时按目标平台评估。
- 阶段 1 关闭 reasoning，不保存异常返回的思考原文；将来开启 reasoning 时需要保存 Provider 实际提供的推理内容并支持检查。工具调用和 reasoning 是独立能力，不互为启用前提。

## 当前进度与下一步

原议程为通用约定 → 消息 → 会话 → run/attempt → 输入快照。

1. 通用约定已定。
2. 消息的 parts、状态、排序原则，以及行粒度和用户/assistant 的 run 关联已定。Luke 在后续讨论中确认：用户输入各一行，role=user，不填 run_id，由 run 引用触发消息；一次 run 的 assistant 输出聚合一行，role=assistant，run_id 必填且唯一，工具过程放在该行 parts 内。完整消息表尚未收口；删除清空表示与并发保护已确认，下一步核对系统记录和合成工具记录，替换旧 content/tool_payload 草案。
3. 会话表的最小列与约束尚未讨论。继承连续会话、非每日会话的 ADR 0008。
4. run/attempt 的字段与状态机、卡在 generating 的恢复规则尚未讨论完成。
5. 输入快照作为 attempt 的一列是初步倾向，未接受；必须保存实际发送内容的副本而非消息 id 引用，不能作为后续上下文来源。
6. 已接受的通用约定与消息存法已登记 ADR 0015；剩余结构讨论收口后补充相应 ADR，再整理本功能 SPEC 草稿。

## 待定、依赖与冲突

- 首次出现事件是正文、可见推理还是其他内容；生成中继续发送的排队功能是否纳入阶段 1、逐条还是合并执行、删除取消及失败后续策略均未定。讨论存储兼容性不等于授权实现队列。
- 不得用聊天展示顺序推断某次 run 的输入。排队消息不能因已落库而自动混入当前 run 后续工具步骤。
- 行粒度已核对并保持 ADR 0010 的“一个 run 至多一条 assistant 消息”；不得因 SDK 便利自行改变来源与数量契约。
- 删除清空及并发保护已获 Luke 确认，见 ADR 0015：parts 为 JSON 数组且不允许 SQL NULL，删除时原子清为 [] 并设置 deleted_at；数据库约束 deleted_at 非空时 parts 必须为 []。所有流式与最终保存须在原子更新中检查 deleted_at 为空，已删除则跳过内容更新，不得清除删除标记。其他含内容的消息列也须清空。生成中删除是否同时停止运行仍未定。
- 系统记录候选规则待确认：消息表允许 role=system，保留阶段 1 合成系统记录的表达能力，不关联生成 run；系统指令不自动作为每轮聊天消息重复插入。服务端明确组装实际系统指令，并在每次实际发送的输入快照中保存；历史记录即使标为 system，也不能仅凭 role 自动获得指令权限。系统记录的创建权限、选择和版本来源须在组装规格中明确，SDK 顶层参数名按锁定版本核实。
- Issue #1 要求合成工具记录；采用 parts 后需明确表达方式与测试，不能继续机械使用 tool_call/tool_result 独立行草案。需变更已发布 SPEC 时另获授权。
- 附件表和对象存储只是此前建议，不作为已接受结构。阶段 1 不因此增加多模态实现。
- ADR 0004 的 system/instructions、request.messages opt-in 表述与所查 v7 不一致，相关源码证据见 AI SDK 报告；修订时明确验证版本，不把历史实验改写为已测新版行为。
- 外部观测未来接入涉及 ADR 0005 数据外送与清理边界重评；不因平台支持导入就推定应迁移历史。

## 证据与学习

- [AI SDK 消息持久化](evidence/ai-sdk-message-persistence-evidence.md)。主会话已抽查 3 项；其余使用前核对。
- [旧仓库聊天结构](evidence/legacy-chat-schema-findings.md)。固定旧提交，非 v2 决定。
- [开源应用](evidence/message-storage-apps-evidence.md)与[框架](evidence/message-storage-frameworks-evidence.md)。保留主会话校准，不能沿用“行业没有独立工具行”等过满结论；Conversations API item 不证明服务端物理表结构。
- [历史讨论与理解证据](discussion-history.md)。含一对一拆表、实际输入副本、PostgreSQL、排序与格式迁移的讲解。
- 外部学习笔记尚待同步，当前 worktree 没有 study-notebook 符号链接；不因此把仓库历史当永久笔记。

## 接续

本轮讨论已暂停。停点是上文“系统记录候选规则”，Luke 尚未接受或拒绝；不得从收尾发布授权推断方案已获确认。下一会话先解释系统指令、系统记录与输入快照的职责，再讨论是否采用 role=system 及创建/选择规则，一次一个概念。

恢复步骤：先查 git status，从最新 origin/main 建立新讨论分支，读取 AGENTS.md、CONTEXT.md、本文件和 Issue #1，通过 docs/decisions.md 定位 ADR 0010/0015；身份与环境问题再按需读取 ADR 0009–0014 和兄弟 feature。不要重启已完成的消息存储调查，也不要重新询问 seq、SDK parts、行粒度、run 关联和删除清空决定。

后续顺序：系统记录 → 合成工具记录及完整消息约束 → 会话 → run/attempt 与中断恢复 → 输入快照布局 → 本功能 SPEC。尚未决定的生成中删除取消语义、首次可见事件与队列范围保持待定。身份功能设计已收口并单独整理 SPEC 草稿，发布本轮讨论文档不等于发布该草稿为执行 Issue。

无活跃调研。产品实现、数据库迁移与产品验收均未执行；本轮只进行文档一致性、相对链接、格式与独立审查。Git 交付回执见 [功能索引](../README.md)，实际合入状态以该 PR 为准。
