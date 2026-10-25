# 输入记录、消息引用与行业实践核查

日期：2026-10-24。来源：Luke 要求对“终态正文固定、引用消息并保留当次最终结构”的候选再做最佳实践搜索。该方案仍 Proposed，不将“看上去合理”视为接受。

## 结论

后续接受（2026-10-24）：Luke 阅读本调查后同意“保留引用方向，限定功能，不提前建设复杂工具和场景”。ADR 0010 已更新为有限纯文本引用方向 Accepted；本文其余“尚未接受”均为调研时状态，保留事实与当时推荐，不将后续接受伪装为行业通用结论。具体字段与并发契约继续细化。

公开一手资料支持两个原则：不要把历史变化误当作原输入；大内容的重复记录需要按用途控制。但没有足够证据把 SayHear 当前完整组合称为行业通用方案。聊天消息保存、运行追踪、执行状态检查点是不同任务，不能互相替代证明。

有直接的增量去重实践，也有明确逐次记录完整历史的追踪实践。推荐依据应是本项目对成本、删除和可追溯性的取舍，而不是“行业都这样做”。本调查不是采用率统计，没有以未找到案例证明不存在。

## 调查范围与停止条件

核查官方标准草案、官方产品/框架文档和固定提交源码：OpenTelemetry GenAI、Langfuse、LangSmith、Vercel AI SDK/Chatbot、LangGraph。停止条件为能区分：普通消息存储、追踪引用、增量状态保存，以及当前引用方案自行承担的部分。不安装、执行框架、运行产品测试、连接数据库、注册服务或采用外部观测平台。第三方镜像、论坛与搜索摘要不作结论依据。

源码基线：

- OpenTelemetry GenAI `9ffc7e00c639be7712e544e3e54331e885dccf84`。
- Vercel Chatbot `c2f8235e1f3ea903ad8b7f61447c4f74164b5c58`。
- LangGraph `4c52e129eb1ab69a3da58b799f67929f77d81149`。
- 产品文档是本次实时读取，保留访问日期，不等于验证其内部数据库实现。Langfuse v4 的存储描述以官方文档为依据，未对部署实例取证。

## 1. OpenTelemetry：不捕获、内容内联、内容另存并引用均有适用场景

GenAI 约定认为指令及消息既敏感又可能很大，默认不捕获正文，允许按需启用。对正文量大或敏感的生产环境，提出将内容另外保存、追踪记录保留引用。外部上传 hook 接收的是该次实际指令和输入输出，而非仅收到原应用消息 ID。

这支持“运行元数据与大正文可分离”，没有规定必须重复存全文，也没有规定必须直接引用聊天表或采用不可变 canonical 消息。引用格式仍留有 TODO，且本文档状态为 Development。不能把它描述成已稳定的具体数据库标准。

来源：[固定提交的捕获与外部存储章节](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/gen-ai-spans.md#capturing-instructions-inputs-and-outputs)。原 OpenTelemetry 网站入口已提示迁移到该独立仓库，本次使用迁移后来源。

## 2. Langfuse：明确逐次记录历史，是对“只存消息引用已属惯例”的反证

官方最佳实践要求每次 generation 的输入输出按角色记录，后续 generation 的输入包含先前历史和新消息，以形成连贯 session 视图，并忠实反映模型看到的内容。该文档没有用 canonical 消息 ID 清单替代这些内容。

v4 官方迁移文档描述 `events_full` 保存完整事件，`events_core` 提供截短 input/output/metadata 的查询投影。最终已摄入 trace/observation 不再可靠更新，但这是运行事件的不可变性，不是外部聊天数据库正文的不可变性，也不是跨请求正文去重的证据。

来源：[最佳实践](https://langfuse.com/docs/observability/best-practices#sessions)、[v4 存储模型](https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v3-to-v4)、[已摄入记录的更新限制](https://langfuse.com/faq/all/tracing-data-updates)。这里只能证明其公开记录契约，不能从页面推断底层是否压缩或复用任意重复文本。

## 3. LangSmith：输入输出内容是追踪对象，隐藏内容也是明确选择

官方手工 LLM 追踪文档将消息内容作为 inputs/outputs 传入，可配置屏蔽或处理后再发送。隐藏正文可以减少捕获，但不等于通过消息引用保留原始输入的准确回看。它支持“按需选择观测内容”的取舍，未为候选的最终协议重建提供现成保证。

来源：[记录 LLM 调用](https://docs.langchain.com/langsmith/log-llm-trace)、[输入输出屏蔽](https://docs.langchain.com/langsmith/mask-inputs-outputs)。不从 SDK 公共接口推断其私有数据库结构。

## 4. AI SDK / Chatbot：独立消息保存有先例，终态不可变不是默认保证

AI SDK 官方持久化示例保存 UIMessage，包括稳定 ID 与 parts；示例明确不覆盖完整授权和错误处理。它讲的是聊天保存，没有实现“最终 Provider 请求以引用形式留证”的机制。

固定提交 Chatbot 的 Message_v2 逐消息保存 role、parts 等。查询函数既可插入也可按 ID 更新 parts；聊天路由在工具审批继续流程更新已保存消息，编辑动作还会删除从指定时间起的后续消息。因此不能从“一条消息一行”推导“所有已存消息永久不可变”。工具审批中的已有行也不等于已经结束的纯文本回复，本调查没有据此声称后者普遍改写。

来源：[官方持久化示例](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence)、[Message_v2 schema](https://github.com/vercel/chatbot/blob/c2f8235e1f3ea903ad8b7f61447c4f74164b5c58/lib/db/schema.ts)、[插入与更新](https://github.com/vercel/chatbot/blob/c2f8235e1f3ea903ad8b7f61447c4f74164b5c58/lib/db/queries.ts#L231-L257)、[工具审批继续](https://github.com/vercel/chatbot/blob/c2f8235e1f3ea903ad8b7f61447c4f74164b5c58/app/%28chat%29/api/chat/route.ts#L348-L377)、[编辑删除路径](https://github.com/vercel/chatbot/blob/c2f8235e1f3ea903ad8b7f61447c4f74164b5c58/app/%28chat%29/actions.ts)。

## 5. LangGraph：存在真实增量保存与稳定版本引用，但针对执行状态

官方 DeltaChannel 文档明确将长期消息列表重复写入每个 checkpoint 视为优化对象，只保存各步增量并在读取时重建。当前标为 beta，要求 reducer 满足确定的组合性质；随时间、随机数变化的重建会造成不一致。不能把“有机制”当作所有部署已使用它。

Postgres saver 固定源码将 channel 内容按版本存于 checkpoint_blobs；checkpoint 以 channel_versions 连接对应版本，相同版本 blob 冲突时不重新插入。这是“引用稳定版本而非重复存所有内容”的直接工程先例。但变化了的消息列表仍可能产生新版本，所以版本引用本身也不保证按单条消息去重。

DeltaChannel 保存和还原的是框架执行状态，不是 SDK 转换后的原始 HTTP 请求。它没有替 SayHear 实现 Provider 转换映射、用户删除后的缺失展示或 owner 约束，也不要求 SayHear 引入 LangGraph。

来源：[运行时 DeltaChannel 文档](https://docs.langchain.com/oss/python/langgraph/pregel#deltachannel)、[官方设计介绍](https://www.langchain.com/blog/delta-channels-evolving-agent-runtime)、[固定提交 Postgres schema 与读取/写入](https://github.com/langchain-ai/langgraph/blob/4c52e129eb1ab69a3da58b799f67929f77d81149/libs/checkpoint-postgres/langgraph/checkpoint/postgres/base.py#L56-L139)。官方 benchmark 不对应本项目预算有限的聊天上下文，本报告不引用其倍数预测 SayHear 节省。

## 对当前候选的判断与推荐

可采用的成熟思路是：稳定身份和来源、准确记录实际选择、对有历史回看要求的内容使用稳定版本或不可变记录，以及按用途限制正文重复。当前“终态 canonical 正文只存一次，attempt 中记录最终请求结构并引用正文”的完整方案仍是针对 SayHear 的定制组合。

它可以成立，条件是终态写保护确实成立、引用指向当时使用的部分、记录覆盖动态时间和 Provider 转换、删除后明确标记缺失，以及 SDK 升级不悄悄改变历史读取。hash 只能发现变化，不能恢复原文或证明原请求。

推荐保留该候选，但不以行业惯例跳过设计审阅，也不在阶段 1 提前建设支持任意工具/多模态/Provider 的通用重建系统。若采用，先限定已确认纯文本的可验证映射，未知形状不能静默当作已记录；具体失败或表示方案须另行定稿。工具合成存储验收不等于它们已可作为真实历史发送。

## 独立核查与验证回执

delegate-claude investigator session `e1f255a4-d0e1-46b1-a20f-e0def5cb1931`，配置 `sonnet` / `group/regular`，实际返回模型 `step-5-preview`，300 秒后以 `timed_out` / `TIMED_OUT` 结束，没有完整报告。最终状态 warnings、blockers 为 null；result.txt 仅有准备开始探索资料的说明，没有可采纳的研究结论。没有活跃委派，未使用 fallback，也不把本轮算作独立审查通过。

以上结论均由主 Agent 直接核对一手资料、固定源码及 Chatbot 更新函数调用点；LangGraph 的补充调查由主 Agent 完成，不冒称 worker 已覆盖。修改文档的本地文件链接和 diff 格式检查通过；未进行产品实现、构建或测试。方案未接受，未新增发布授权。
