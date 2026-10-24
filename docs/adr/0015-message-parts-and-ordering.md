---
status: accepted
---

# 消息采用 AI SDK parts，使用独立 seq 排序并保留产品状态

Luke 于 2026-10-24 确认消息采用 AI SDK parts、保留 seq 排序，并在阶段 1 继续自建库内运行记录。本 ADR 固定已经达成共识的通用约定和消息存储选择，不表示完整 schema 已设计完成。剩余讨论见 [canonical 数据结构接续](../plans/stages/stage-1/features/canonical-data-model/session.md)。

## 决定

- 消息内容使用 AI SDK 的 parts，存于 jsonb，不提前定义 SayHear 自有 parts 或建立双向转换层。SDK 版本在实施时锁定。持久化格式识别需要可追溯，但具体版本字段尚未决定。
- 消息的 owner、身份、run 来源关联、删除与生成状态使用 SayHear 管理的列，沿用 [ADR 0010](0010-minimal-data-contract-and-owner.md)。选择 parts 不自动改变其来源与数量契约。
- Luke 在后续讨论中确认行粒度与 run 关联：每条用户输入各一行，role=user，不填写 run_id；run 引用触发它的用户消息，允许显式重试产生多个 run。一次 run 的 assistant 输出聚合为一行，role=assistant，run_id 必填且唯一，一个 run 至多一条 assistant 消息；首段前失败仍可没有消息。
- 一次 assistant 输出内的文本、工具调用与结果，以及未来启用后的可见推理，存于同一行的有序 parts。工具调用与结果可由同一个工具 part 的输入、输出及状态表示，不为每个工具步骤另建聊天消息行。存储行粒度不限制界面展开方式，也不要求与 Provider 协议消息一一对应。系统记录的具体角色规则与合成工具验收方式仍待讨论。
- id 使用 UUIDv7。通常由数据库生成，需要提前知道时由服务端生成；客户端 id 仅用作幂等键，不直接作为数据库主键。目标数据库是否内置 uuidv7() 实施时核实。
- 时间使用 timestamptz。自定义状态使用 text + CHECK，SDK 或 Provider 的原始值不以 CHECK 穷举；应用需要据此分支时，先映射到自定义状态。
- 消息使用自增 seq 专用于稳定排序。按消息出现顺序展示，用户消息和对应回答不必相邻，流式更新不重新排序。预生成 id 不等于提前占据展示位置。identity 不保证并发事务提交或网络到达顺序，序号分配与客户端合并规则须在实施规格中细化。
- 消息生成状态采用 generating、complete、interrupted，与 deleted_at 独立。Luke 后续确认删除清空与并发保护：parts 必须为 JSON 数组，不允许 SQL NULL；删除时在同一事务中将 parts 置为 [] 并设置 deleted_at，保留消息身份、seq 与来源关联。数据库约束 deleted_at 非空时 parts 必须为 []；其他承载内容的消息列也须清空。历史快照保留边界继续按 ADR 0005/0010。
- 所有流式与最终内容保存均须在原子更新中检查 deleted_at 为空，已删除则跳过内容更新；不得先查询再无条件保存，也不得通过普通生成保存清除 deleted_at。数据库清空约束与条件更新共同防止迟到写入恢复内容。生成中删除是否同时停止运行仍未决定。
- 阶段 1 不接外部观测工具，沿用 [ADR 0005](0005-chat-experience-and-run-record.md) 的库内运行记录及不向第三方观测平台发送内容的边界。未来接入可从新运行开始，不强制迁移全部历史；历史导入能力、缺失信息与成本届时评估。

## 取舍

有序 parts 能保留正文、推理和工具步骤的内部先后关系。直接使用 SDK 格式可避免现在承担字段映射和转换维护成本。自定义格式的自主性有价值，但目前没有足以抵消成本的明确需求。

未来 SDK 发生不兼容变化时，可迁移历史，或保留旧格式定义并在读取时转换。冻结旧格式不等于长期保留完整旧 SDK 依赖，也不保证转换没有成本。工具状态和 Provider 元数据须保真，不能因旧类型无法识别就静默丢弃。

seq 将排序与 UUID 的生成时间解耦。代价是必须定义分配时机及并发合并规则，不能只凭数据库自增列承诺所有客户端到达顺序一致。展示顺序不证明模型看过哪些消息，实际输入仍由运行快照记录。

## 未定与重评

系统记录的 role 与输入映射、生成中删除的取消行为、合成工具记录、会话列、run/attempt 状态机、快照物理布局、首次可见事件与排队功能范围均未定。本 ADR 不授权实现队列，也不采用旧草案的 tool_call/tool_result 独立行约束。

阶段 1 仍关闭 reasoning，不记录异常返回的思考原文。长期开启 reasoning 时，需要保存 Provider 实际提供的推理内容并支持检查；原文、摘要、加密块与签名的具体契约届时核实。reasoning 与工具调用是独立能力，不互为启用前提。

SDK 格式无法表达明确产品需求、多个运行 SDK 共存、实际迁移成本上升，或观测维护成本明显增加时重评。

依据：[AI SDK 调研](../plans/stages/stage-1/features/canonical-data-model/evidence/ai-sdk-message-persistence-evidence.md)、[框架比较](../plans/stages/stage-1/features/canonical-data-model/evidence/message-storage-frameworks-evidence.md)、[应用比较](../plans/stages/stage-1/features/canonical-data-model/evidence/message-storage-apps-evidence.md)。调研含抽查范围与校准，未实测部分不作运行保证。
