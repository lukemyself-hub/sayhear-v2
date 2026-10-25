# 阶段 1 功能接续：canonical 数据结构与消息存储

更新：2026-10-24。来源：Luke 本次会话与 [Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1)。按 Luke 要求，从 [身份与数据归属](../identity-data-ownership/session.md) 拆出。共用当前讨论分支，不代表授权创建新分支或实现。

## 本次恢复（2026-10-24）

Luke 本次要求按最新版 learning-stage 补齐全阶段记录，再从系统记录方案继续。已从 fetch 后的 `origin/main` 提交 `c306c6ba46fabe9be59295ac5238b0e60be36be7` 建立 `codex/stage-1-learning-resume`。全局目标、授权及模块进度改由[阶段总接续](../../session.md)维护；先读[总计划](../../plan.md)，本文件只承接 M2 的细节。

Luke 已确认总计划九个模块及先继续本模块、再按依赖细化其余模块的安排，已有 Accepted 决定保持不变。系统记录仍待确认，先区分当前指令、存储记录及实际输入副本，不把方案解释或无回应记作接受。下一决定须明确创建权限、选择规则及版本来源，再关联 ADR；不开始产品实现。

Luke 随后询问 Tolan 每轮重建上下文是否意味着每次带 system prompt，以及对产品规则一致性的作用。已核查[公开资料](evidence/tolan-per-turn-context-and-system-instructions.md)：案例明确每轮重建并重新放入人格与语气指导，未公开完整请求体或角色映射。主 Agent 澄清此前“不按轮次重复插入系统消息”只指不新增重复存储行。Luke 回复“好，没问题，继续”，每次模型请求显式提供有效指令的原则已记录为 [ADR 0016](../../../../../adr/0016-per-request-system-instructions.md) Accepted；指令来源及 system 记录规则没有同时获得确认。

Luke 随后回复“认可这个决策，继续”，确认阶段 1 以仓库内独立文本文件随应用部署维护，并接受修改规则需要重新部署的代价。替代数据库配置方案及取舍见 ADR 0016。具体路径、格式、版本标识、同一 run 的版本选择以及 role=system 的创建/选择规则仍待讨论，不创建产品文件。

Luke 追问真实聊天何时会产生 system 记录。已澄清当前聊天无需独立 system 消息行，产品指令由部署文件读取，实际内容随请求快照留存。此前保留独立行只为合成验收的建议没有获接受。Luke 同意若该验收无必要则不做，并要求重新建议。重新建议的方向是以实际指令链路覆盖原验收目的，不再为该验收保留消息类型。

Luke 回复“没问题”，确认阶段 1 不保留独立 system 聊天记录，已写入 [ADR 0016](../../../../../adr/0016-per-request-system-instructions.md) 的“不保留独立 system 聊天记录”一节。原合成系统消息验收改为核对实际请求携带指令、指令随快照保存、运行详情可读，覆盖 fallback 与预算裁剪；普通历史内容不因其文字提升角色。Issue #1 与 ADR 0010 的措辞尚未修订，需另获发布授权。合成工具记录另行讨论，不据此一并删除。

## 目标与边界

- 明确连续会话、消息、run、attempt 与实际输入快照的物理结构、约束和生命周期，为阶段 1 canonical 闭环准备规格。
- 继承 [ADR 0010](../../../../../adr/0010-minimal-data-contract-and-owner.md) 的 owner、同 owner 引用、幂等和删除契约。身份来源、RLS 路径、登录与环境边界由兄弟 feature 管理，本功能只细化数据形状。
- Luke 于 2026-10-24 收尾时明确授权整理本 worktree 文档、提交、推送并通过 PR 合入 main。本次授权不包含产品实现、云资源、用户库连接、部署或修改 Issue #1。后续 session 不继承新的发布授权。
- 尚未完成完整数据结构设计或 SPEC。完整阶段执行范围以 Issue #1 为准；本功能细化仍需后续发布。

## 已确认

每次模型请求携带有效指令、阶段 1 使用仓库内独立文本文件随应用部署、不设独立 system 聊天记录，见 [ADR 0016](../../../../../adr/0016-per-request-system-instructions.md)。版本机制尚未收口。

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
- 阶段 1 不设独立 system 聊天行，实际指令经请求快照保存、检索和展示，已由 Luke 确认并记录 ADR 0016。此前 role=system 合成行候选已撤回，未曾接受。Issue #1 与 ADR 0010 的措辞待修订；SDK 参数按锁定版本核实。
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

此前一轮停在“系统记录候选规则”。本次已解释每轮输入与系统记录的区别，并确认 ADR 0016 的每次请求携带指令原则及文件随部署维护的来源。系统记录已收口。下一项是版本追踪（指令文件路径、格式、版本标识与同一 run 多次尝试的选择），再讨论合成工具记录，一次一个概念。原有收尾发布授权不证明这些新方案获确认。

恢复步骤：先查 git status，读取 AGENTS.md、CONTEXT.md、阶段总计划、总接续、本文件和 Issue #1，通过 docs/decisions.md 定位 ADR 0010/0015；身份与环境问题再按需读取 ADR 0009–0014 和兄弟 feature。本次已按 Luke 指令从最新 origin/main 建立新讨论分支，之后沿用，不在模块切换时自动新建。不要重启已完成的消息存储调查，也不要重新询问 seq、SDK parts、行粒度、run 关联和删除清空决定。

后续顺序：系统记录 → 合成工具记录及完整消息约束 → 会话 → run/attempt 与中断恢复 → 输入快照布局 → 本功能 SPEC。尚未决定的生成中删除取消语义、首次可见事件与队列范围保持待定。身份功能设计已收口并单独整理 SPEC 草稿，发布本轮讨论文档不等于发布该草稿为执行 Issue。

无活跃调研。产品实现、数据库迁移与产品验收均未执行；本轮只进行文档一致性、相对链接、格式与独立审查。Git 交付回执见 [功能索引](../README.md)，实际合入状态以该 PR 为准。
