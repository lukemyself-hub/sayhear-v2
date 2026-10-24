# 主流 Agent 框架持久化层如何存消息与工具调用（证据）

日期：2026-10-24。范围：OpenAI Agents SDK、OpenAI Responses / Conversations API、Letta、Mastra、LangGraph checkpointer、LangChain Postgres chat history、Pydantic AI。只回答四个问题：存储粒度、工具调用/结果/推理的落点、调试"一次回答经过哪些步骤"靠什么、格式迁移史。

标注约定：

- 【文档】= 官方文档原文（含官方 API 参考页）。
- 【源码】= 固定 tag 或固定 release 的源码；URL 里带 tag。
- 【推断】= 我根据源码结构得出的判断，不是官方表述。

证据边界：所有源码链接都锁定到 2026-10 当时的最新版本（下表）。凡"查不到"的，明确写查不到。

**主会话抽查（2026-10-24）：** 以下三条与原文一致：Letta `messages` 表含 `text`、`content`（parts）、`tool_calls`、`tool_returns`、`step_id`、`run_id`、`sequence_id`；Mastra `MessageMerger` 就地把 tool-call part 更新为结果；OpenAI Agents `SQLAlchemySession` 的 `message_data` 为 Text 列。其余条目未逐条复核。

**主会话校准：** 第 0 节“没有一家把工具调用、结果、推理拆成独立行”的说法过满。OpenAI Agents SDK 和 Conversations 中，每个 item（含工具调用、工具结果、推理）各占一行；LangChain 的 ToolMessage、Letta 的 tool 消息也是独立行。没有先例的只是“每步一行，且把正文与工具数据拆成结构列，用 kind 区分”这一具体形状。另外，Letta 的 `steps` 与 `provider_traces`（完整请求和响应）是库内的步骤表和输入快照表，可作为 run/attempt/快照设计的先例；应用报告第 0 节“无一家有此类产品表”只适用于终端应用。

| 项目 | 锁定版本 |
| --- | --- |
| openai-agents-python | v0.24.0（2026-10-15） |
| openai-python（Responses/Conversations 类型） | v3.37.0（2026-10-22） |
| Letta | 0.16.8（2026-05-14，最新 release） |
| Mastra | `@mastra/core@1.79.0`（2026-10-21） |
| LangGraph | 1.2.17（2026-10-24） |
| LangChain Postgres chat history | 见第 5 节 |
| Pydantic AI | v2.61.0（2026-10-24） |

---

## 0. 一句话结论（先给答案）

这七家里，**没有一家把"工具调用 / 工具结果 / 推理"拆成独立表行、用 kind 列区分**。它们分成三种形状：

1. **item 流（每行一个 Responses API item，整条 item 序列化进一个 JSON/TEXT 列）**：OpenAI Agents SDK 的 Session、OpenAI Conversations API。工具调用、工具结果、推理都是**各自独立的 item，各自一行**，但行内是 JSON blob，不是拆列。
2. **一条消息一行 + 消息内 parts 数组（json/jsonb 一列）**：Letta（`content` 列存 content parts）、Mastra（`content` 列存 `{format:2, parts:[...]}`）、AI SDK 官方示例（背景已确认）。工具调用与结果通常是**同一个 part 的两次状态更新**或**同一行里的两个 part**。
3. **整段图状态序列化**：LangGraph checkpointer（channel values 按 channel 分 blob）、Pydantic AI（整段 message history 序列化成 JSON 数组，官方不提供表结构）。

调试"一次回答经过哪些步骤"：**三家都另有独立的 trace/span 或 step/run 记录**（OpenAI Agents 的 tracing span、Letta 的 steps + provider_traces、Mastra 的 `mastra_ai_spans`）。消息表本身只承载"模型下一轮要看到的内容"，不承载步骤耗时与父子关系。这条一致性很高，对 ADR 0010 的 run/attempt 设计是正面支持。

---

## 1. OpenAI Agents SDK 的 Session

### 1.1 存储粒度：一行一个 item，item 整体 JSON 序列化

- 【源码】`SQLiteSession` 建两张表：
  - `agent_sessions(session_id TEXT PRIMARY KEY, created_at, updated_at)`
  - `agent_messages(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, message_data TEXT NOT NULL, created_at, FOREIGN KEY(session_id) … ON DELETE CASCADE)`
  - 写入是 `message_data = [(self.session_id, json.dumps(item)) for item in items]`，逐条 `INSERT`。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/memory/sqlite_session.py#L231-L259 、同文件 `#L261-L275`
- 【源码】`SQLAlchemySession`（Postgres 用 `postgresql+asyncpg://`）表结构完全相同：`session_id` 主键 + `message_data Text NOT NULL`；序列化 `json.dumps(item, ensure_ascii=self._ensure_ascii, separators=(",", ":"))`。没有 jsonb 类型，也没有拆列。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/extensions/memory/sqlalchemy_session.py#L206-L248 、`#L287-L289`
- 【源码】`message_data` 的类型是 `TResponseInputItem = ResponseInputItemParam`（来自 openai-python），即**Responses API 的 input item 联合类型**。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/items.py#L79
- 【文档】"After each run: All new items generated during the run (user input, assistant responses, tool calls, etc.) are automatically stored in the session."
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/docs/sessions/index.md#L57

所以粒度是：**user 消息、assistant 消息、每次工具调用、每次工具输出、每个 reasoning item，各自一行**。这不是"一条 assistant 回答一行"，而是"模型 API 的 item 流一行一个"。

### 1.2 工具调用、工具结果、推理存在哪

- 【源码】item 的联合类型里，工具调用是 `ResponseFunctionToolCallItem`（`type: "function_call"`，含 `call_id`、`arguments`、`status`），工具结果是 `ResponseFunctionToolCallOutputItem`（`type: "function_call_output"`，含 `call_id`、`output`），推理是 `ResponseReasoningItem`（`type: "reasoning"`，含 `summary`、`content`、`encrypted_content`）。
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/responses/response_item.py#L330-L365
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/responses/response_reasoning_item.py#L31-L65
- 【源码】SDK 侧把它们包装成 `ToolCallItem` / `ToolCallOutputItem` / `ReasoningItem` / `MessageOutputItem`，持久化时再 `run_item_to_input_item()` 转回 Responses item。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/items.py#L383-L455 、`#L493-L498`
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/run_internal/items.py#L179-L205
- 【源码】推理 item 的 `id` 可以被 `reasoning_item_id_policy="omit"` 剥掉；默认 `None` 等于 `"preserve"`。也就是说**推理 item 是一等持久化对象**，且其 id 会影响下一轮回放。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/run_config.py#L485-L490
- 【源码】OpenAI 侧 reasoning item 的 `encrypted_content` 默认随响应返回，`store:false` 时必须靠它回放。
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/responses/response_reasoning_item.py#L51-L60

### 1.3 调试"一次回答经历了哪些步骤"

- 【文档】SDK 自带 tracing，默认开启；一次 `Runner.run` 一个 trace，里面是 `task_span` → `turn_span` → `agent_span` → `generation_span` / `function_span` / `guardrail_span` / `handoff_span`。span 有 `parent_id`、`started_at`/`ended_at`、`span_data`。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/docs/tracing.md
- 【源码】`GenerationSpanData` 带 `input`/`output`/`model`/`model_config`/`usage`；`FunctionSpanData` 带 `input`/`output`。usage 与模型原始请求/响应都在 span 里，而不是在 session 表里。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/tracing/span_data.py#L135-L210
- 【源码】只有 `AdvancedSQLiteSession`（扩展、非默认）额外建了 `message_structure(message_id, message_type, sequence_number, user_turn_number, tool_name, …)` 和 `turn_usage(…)` 两张辅助表，用来做"按 turn 查询 / 工具使用统计 / 分支"。基础 `SQLiteSession` 与 `SQLAlchemySession` 都没有。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/extensions/memory/advanced_sqlite_session.py#L292-L331
  - 【文档】该扩展的定位是 "conversation branching, detailed usage analytics, and structured conversation queries"。
    https://github.com/openai/openai-agents-python/blob/v0.24.0/docs/sessions/advanced_sqlite_session.md

结论：**步骤追溯靠 trace/span，不靠消息表**。消息表是给模型回放用的 item 流。

### 1.4 迁移史

- 【源码】Session 表没有任何 schema version 列，也没有迁移框架；`create_tables` 的文档字符串直接写 "Set to True for development and testing when migrations aren't used"，即生产环境由用户自己管迁移。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/extensions/memory/sqlalchemy_session.py#L181-L184
- 【源码】表结构自引入以来只加过列（`AdvancedSQLiteSession` 的 `message_structure` 是新建表），没看到改列型的迁移。
- 【源码】真正带版本号的是**另一个东西**：`RunState`（HITL 暂停/恢复快照）。它有 `CURRENT_SCHEMA_VERSION = "1.21"` 和从 `1.0` 到 `1.21` 的逐版本摘要，策略是"新快照写当前版本、旧 SDK 拒绝新版本（fail-fast）"。
  - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/run_state.py#L242-L315
  - 【推断】这是"运行状态快照要版本化、消息 item 流不需要"的明确先例：item 流本身是 Responses API 的稳定契约，版本化压力落在 run 快照上。

---

## 2. OpenAI Responses API / Conversations API 的 item 模型

### 2.1 item 是唯一的存储单位

- 【文档】"Conversations store items, which can be messages, tool calls, tool outputs, and other data."
  - https://developers.openai.com/api/docs/guides/conversation-state
- 【文档】Conversation 是"long-running object with its own durable identifier"；挂在 conversation 上的 response 的 items 会被持久化，且不受 30 天 TTL 限制；独立 response 默认存 30 天，`store:false` 可关。
  - 同上
- 【源码】`ConversationItem` 是 29 个成员的判别联合，`discriminator="type"`：`Message`、`ResponseFunctionToolCallItem`、`ResponseFunctionToolCallOutputItem`、`ResponseReasoningItem`、`ResponseCompactionItem`、`McpCall`、`LocalShellCall`、`Program`/`ProgramOutput` 等。
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/conversations/conversation_item.py#L334-L367
- 【源码】列表接口按 `after`/`limit`/`order` 分页，返回 item 列表；`order` 默认 `desc`。
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/resources/conversations/items.py#L148-L195

粒度：**每个 item 一条记录**。一条 assistant 文本消息是一个 `message` item，内部 `content` 是 `ResponseOutputText | ResponseOutputRefusal` 数组；工具调用、工具输出、推理各自是独立 item，不是 message 的 part。

### 2.2 工具调用 / 结果 / 推理

- 工具调用：`function_call` item，`call_id` + `arguments`（JSON 字符串）+ `status`。
- 工具输出：`function_call_output` item，用同一个 `call_id` 关联；`output` 可以是字符串或 `input_text`/`input_image`/`input_file` 数组。
- 推理：`reasoning` item，`summary[]`（`summary_text`）、可选 `content[]`（`reasoning_text`）、可选 `encrypted_content`。
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/responses/response_output_message.py#L16-L48
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/responses/response_reasoning_item.py#L31-L65
- 【文档】无状态（`store:false`）时必须把整个 `output` 数组原样回放，包含 encrypted reasoning items 与 assistant `phase` 字段；`phase` 用来区分 `commentary`（中间说明）与 `final_answer`，丢掉会降低效果。
  - https://developers.openai.com/api/docs/guides/conversation-state

【推断】这对 SayHear 的含义：如果照抄 item 模型，"一次回答"会变成多行（N 个 reasoning + N 个 function_call + N 个 function_call_output + 1 个 message），且推理 item 需要保存加密串才能续轮。这正是候选 A 的形状；但它也带来"用户可见的 assistant 消息"与"模型 item 流"不一致的问题——OpenAI 用 `phase` 字段解决，AI SDK 用 `step-start` part 解决。

### 2.3 调试依据

- 【文档】OpenAI 平台侧另有 Traces / Logs 产品；Conversations item 列表本身不提供耗时、模型、token 字段（`Message`/item 只有 `id`、`status`、内容）。
  - https://developers.openai.com/api/docs/guides/conversation-state
- 【推断】item 流给的是"重放顺序"，不是"执行性能"。

### 2.4 迁移史

- 【源码】item 联合类型在持续扩张（v3.37.0 里已有 `program`/`program_output`、`apply_patch_call`、`shell_call`、`tool_search_call`、`compaction` 等），新增都是**加新 `type`**，不改旧类型字段——判别联合 + 未知类型容忍是它的兼容策略。
  - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/responses/response_item.py#L330-L365
- 【文档】`previous_response_id` 链与 conversation 两种续轮方式并存，官方建议二选一。
  - https://developers.openai.com/api/docs/guides/conversation-state

---

## 3. Letta（原 MemGPT）

### 3.1 存储粒度：一条"消息"一行，行内 content 是 parts 数组（JSON）

- 【源码】`messages` 表（SQLAlchemy，Postgres/SQLite 同构）：
  - `id` 主键、`role`（user/assistant/tool/function/system/approval/summary）、`text`（legacy 纯文本）、`content`（`MessageContentColumn`，JSON 存 content parts 列表）、`tool_calls`（`ToolCallColumn`，JSON，OpenAI 风格）、`tool_call_id`、`tool_returns`（`ToolReturnColumn`，JSON）、`step_id`、`run_id`、`otid`、`sequence_id`（全局单调）、`is_err`、`approvals` 等。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/orm/message.py#L23-L100
- 【源码】`MessageContentColumn` 是 `TypeDecorator(impl=JSON)`，`serialize_message_content()` 把每个 part `model_dump(mode="json")` 后存成 JSON 数组。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/orm/custom_columns.py#L129-L139
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/helpers/converters.py#L361-L382
- 【源码】content part 类型：`text`、`image`、`tool_call`、`tool_return`、`reasoning`、`redacted_reasoning`、`omitted_reasoning`、`summarized_reasoning`。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/schemas/letta_message_content.py#L226-L320
- 关键细节：**工具调用同时存在于两处**——legacy 的 `tool_calls` JSON 列（OpenAI `ChatCompletionMessageToolCall` 形状），以及新的 `content[].type='tool_call'` part。源码里有 `# TODO: Use ToolCallContent instead of tool_calls` 两处注释，说明迁移未完成。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/server/rest_api/utils.py#L420-L441
- 【源码】并行工具调用：**一条 assistant 消息装下所有 `tool_calls`，一条 tool 消息装下所有 `tool_returns`**（`create_parallel_tool_messages_from_llm_response` 的文档字符串明确写 "One assistant message with ALL tool_calls populated / One tool message with ALL tool_returns populated"）。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/server/rest_api/utils.py#L518-L546

所以 Letta 的粒度是"**一次 LLM 调用的产物 = 1 条 assistant 消息（含 reasoning parts + tool_calls）+ 1 条 tool 消息（含 tool_returns）**"，不是每个工具一行，也不是一条回答一行。

### 3.2 推理（reasoning / thinking / 签名）

- 【源码】`ReasoningContent(reasoning, signature, is_native)`、`RedactedReasoningContent(data)`、`OmittedReasoningContent(signature)`、`SummarizedReasoningContent(id, summary[], encrypted_content)`——**Anthropic 与 OpenAI 的推理分别建型**，`encrypted_content`（OpenAI Responses 风格）与 `signature`（Anthropic 风格）都在 content part 里，与消息同一行。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/schemas/letta_message_content.py#L261-L320
- 【文档】API 层把同一行拆成多种 `message_type` 返回：`reasoning_message`、`hidden_reasoning_message`（state = redacted / omitted）、`tool_call_message`、`tool_return_message`、`assistant_message`。也就是说**存储是一行、API 读出来是多个"消息"**（`to_letta_messages()` 做这层展开，并用 `otid` 生成稳定序号）。
  - https://docs.letta.com/v1-sdk/messages/message-types （旧路径 /guides/agents/messages 现 308 跳转到此）
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/schemas/message.py#L480-L570
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/schemas/message.py#L2648-L2663（`generate_otid_from_id`，把 id 低 7 位改成 part 序号）

这是本次调研里对 SayHear 最有参考价值的一处：**存储粒度按"LLM 调用"聚合，展示粒度按 part 展开**，两者解耦。

### 3.3 调试依据：独立的 steps + provider_traces

- 【源码】`steps` 表：`id`、`run_id`、`agent_id`、`provider_name`、`model`、`model_handle`、`model_endpoint`、`completion_tokens`/`prompt_tokens`/`total_tokens`、`cached_input_tokens`/`cache_write_tokens`/`reasoning_tokens`、`completion_tokens_details`/`prompt_tokens_details`（JSON）、`stop_reason`、`trace_id`、`request_id`、`error_type`、`error_data`（JSON，含 traceback）、`status`。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/orm/step.py#L17-L96
- 【源码】`step_metrics` 表按 `step_id` 一对一存时间线（`step_start_ns` 等）。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/orm/step_metrics.py
- 【源码】`provider_traces` 表存 `request_json` + `response_json`（完整 provider 请求/响应），带 `step_id`、`run_id`、`call_type`。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/orm/provider_trace.py#L15-L50
- 【源码】消息通过 `step_id` / `run_id` 外键挂到步骤与运行上；`Step` 的 pydantic 模型里 `messages` 字段已标注 "Deprecated: use `GET /v1/steps/{step_id}/messages`"。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/schemas/step.py#L55-L60
- 【文档】`GET /v1/steps/` 返回每个 step 的 model/token/stop_reason/error/trace_id；`messages` 字段同样标注 deprecated。
  - https://docs.letta.com/api-reference/steps/list （2026-10-24 抓取成功；若失效，等价信息见 `letta/schemas/step.py` 与 `letta/orm/step.py` 源码）
- 【源码】另有 OpenTelemetry 集成（`letta/otel/tracing.py`，FastAPI 中间件 + OTLP exporter）。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/otel/tracing.py

结论：**步骤追溯靠 steps / step_metrics / provider_traces 三张表 + 可选 OTel**；消息表只靠 `step_id` 关联。

### 3.4 迁移史：Alembic，167 个迁移，消息表多次改形

- 【源码】仓库有 `alembic/versions/` 下 167 个迁移文件（0.16.8）。与消息/步骤直接相关的包括：
  - `2cceb07c2384_add_content_parts_to_message`（2025-03-13）：给 `messages` 加 `content` 列（content parts），**这是"从 text 走向 parts"的关键一步**。
    https://github.com/letta-ai/letta/blob/0.16.8/alembic/versions/2cceb07c2384_add_content_parts_to_message.py
  - `2f4ede6ae33b_add_otid_and_tool_return_to_message`（2025-03-05）：加 `otid` 与 `tool_returns`。
    https://github.com/letta-ai/letta/blob/0.16.8/alembic/versions/2f4ede6ae33b_add_otid_and_tool_return_to_message.py
  - `95badb46fdf9_migrate_messages_to_the_orm`（2024-12-05）：加 `organization_id`、`is_deleted`、`updated_at` 等，删 `user_id`。
    https://github.com/letta-ai/letta/blob/0.16.8/alembic/versions/95badb46fdf9_migrate_messages_to_the_orm.py
  - `2c059cad97cc_create_sqlite_baseline_schema`（2025-07-16）：为 SQLite 建基线快照。
    https://github.com/letta-ai/letta/blob/0.16.8/alembic/versions/2c059cad97cc_create_sqlite_baseline_schema.py
- 【源码】兼容策略是**双写/并存 + 读时兜底**，而不是一次性回填：`Message.to_pydantic()` 里 `if self.text and not model.content: model.content = [TextContent(...)]`，以及 "Handle legacy case of tool message with single tool return + single text content"。
  - https://github.com/letta-ai/letta/blob/0.16.8/letta/orm/message.py#L101-L120
- 【文档】升级方式：`uv run alembic upgrade head`；改模型后 `alembic revision --autogenerate`。
  - https://github.com/letta-ai/letta/blob/0.16.8/CONTRIBUTING.md#L111-L123
- 查不到：面向终端用户的"消息格式 v1→v2"迁移指南。只有 Alembic 迁移史 + 代码内 TODO/legacy 分支。

---

## 4. Mastra memory 存储（含 message format v2）

以下源码 URL 均锁定 `@mastra/core@1.79.0`。

### 4.1 存储粒度：一条消息一行，`content` 列存 `{format:2, parts:[...]}` 的 JSON 文本

- 【源码】表名 `mastra_messages`、`mastra_threads`、`mastra_resources`、`mastra_ai_spans`。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/storage/constants.ts#L7-L20
- 【源码】`TABLE_SCHEMAS[TABLE_MESSAGES]`：`id`（text, PK）、`thread_id`、`content`（**type: 'text'**）、`role`、`type`、`createdAt`、`resourceId`。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/storage/constants.ts#L940-L948
- 【源码】Postgres 写入：`INSERT INTO … (id, thread_id, content, "createdAt", "createdAtZ", role, type, "resourceId")`，`content` 为 `typeof message.content === 'string' ? message.content : JSON.stringify(message.content)`；`ON CONFLICT (id)` 时更新 `content/role/type/resourceId`。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/stores/pg/src/storage/domains/memory/index.ts#L1814-L1835
- 【文档】Storage 参考写明 `content` 是 "JSON of the message content in V2 format. Example: `{ format: 2, parts: [...] }`"，并且 "designed to align closely with the AI SDK `UIMessage` message shape"。
  - https://mastra.ai/reference/storage/overview.md
- 【推断】注意 `content` 声明为 `text` 而不是 `jsonb`：Postgres 侧无法直接对 parts 建 GIN 索引，按 `toolCallId` 查询要应用层解析。

### 4.2 message format v1 → v2

- 【源码】v2 = `MastraMessageContentV2 = { format: 2; parts: MastraMessagePart[]; … }`，注释写 "format 2 === UIMessage in AI SDK v4"。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/state/types.ts#L112-L126
- 【源码】判定：`isMastraDBMessage` 检查 `content.format === 2`；`isMastraMessageV1` = 非 format 2 且带 `threadId`/`resourceId`。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/detection/TypeDetector.ts
- 【源码】**没有存量数据迁移脚本，靠读时转换**：`inputToMastraDBMessage` 先判 v1，再 `mastraMessageV1ToMastraDBMessage(...)` 把 v1 content 转成 v2 parts。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/conversion/input-converter.ts
- 【源码】反向转换器 `convertToV1Messages`（`messageList.get.all.v1()` 用）把 parts 拍平成 v1：text 合并、`tool-invocation` → `{type:'tool-call', …}`、结果 → `role:'tool'` + `{type:'tool-result'}`、reasoning → `{type:'reasoning'|'redacted-reasoning'}`。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/prompt/convert-to-mastra-v1.ts
- 【文档】v1 升级指南的 Storage/Memory 页只说移除了 `format: 'v1'|'v2'` 重载、`MastraMessageV2` 更名 `MastraDBMessage`，**没提存量消息需要转换**。
  - https://mastra.ai/reference/migrations/upgrade-to-v1/storage.md
  - https://mastra.ai/reference/migrations/upgrade-to-v1/memory.md
- 【源码/PR】中间还短暂有过 `MastraMessageV3`（PR #6674，2025-08，AI SDK v5 镜像），后被 PR #9094（2025-10）删除；`MastraMessageV2` 在 v1 发布时更名 `MastraDBMessage`（PR #9255）。
  - https://github.com/mastra-ai/mastra/pull/9094 、https://github.com/mastra-ai/mastra/pull/9255

【推断】Mastra 的经验是：**格式换了两代，靠"读时转换 + 双形态读取"顶住，没有做数据回填**。代价是转换逻辑长期留在热路径上（`input-converter`、`convert-to-mastra-v1` 两套并存）。

### 4.3 工具调用 / 结果 / 推理

- 【源码】工具调用与结果是**同一个 part（`type: 'tool-invocation'`）的不同 state**：`state: 'call' | 'result' | 'partial-call' | 'approval-requested' | …`，结果写在同一 part 的 `result` 字段，`isError` 与 `errorText` 也在里面。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/state/types.ts
- 【源码】结果回填：`MessageMerger.merge()` 按 `toolCallId` 找到 `state:'call'` 的 part，就地改成 `state:'result'`（注释 "Update the existing tool-call part with the result"）。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/merge/MessageMerger.ts
- 【源码】推理是 part 类型 `'reasoning'`（`reasoning`、`details`），由 `reasoning-start/delta/end`、`redacted-reasoning` 流式 chunk 折叠而来。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/message-part-spans.ts
- 【源码】步骤边界用 `{ type: 'step-start', model? }` part 表示。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/message-list/message-list.ts
- 【源码】落库前过滤：丢弃 system 消息、`transient:true` 信号、`state==='partial-call'` 的流式调用、working-memory 调用；保留 `state:'call'`。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/agent/filter-messages-for-persistence.ts

### 4.4 调试依据：独立的 span 表

- 【源码】`SpanType` 含 `agent_run`、`model_generation`、`model_step`、`model_inference`、`model_chunk`、`tool_call`、`mcp_tool_call`、`workflow_run`、`processor_run` 等；`AGENT_RUN` 是根 span，`MODEL_STEP` 是"one API call"。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/packages/core/src/observability/types/tracing.ts
- 【源码】Postgres 用单表 `mastra_ai_spans`（`traceId, spanId, parentSpanId, name, spanType, entityType, entityId, name, startedAt, endedAt, attributes jsonb, input jsonb, output jsonb`），无独立 trace 表，trace = `parentSpanId IS NULL` 的根 span。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/stores/pg/src/storage/domains/observability/index.ts
- 【源码】迁移测试里能看到 span 表新增的关联列：`entityType, entityId, entityName, userId, organizationId, resourceId, runId, sessionId, threadId, requestId, environment, source, serviceName, tags`。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/stores/pg/src/storage/migration.test.ts
- 【文档】`agent.generate`/`agent.stream`/`run.start` 返回 `traceId`，Studio 可查；采样丢弃时为 `undefined`。
  - https://mastra.ai/docs/observability/tracing/overview.md
- 【推断】消息表的 `step-start` part 只给"分段位置"，没有时间戳、没有 runId、没有父子关系；步骤审计必须读 span 表。

### 4.5 迁移史（除 v1→v2 外）

- 【文档】v1 升级（2026-01）Storage 迁移：`mastra_scorers.runtimeContext` → `requestContext`；`mastra_spans` 加唯一约束 `(traceId, spanId)`，有重复时需 `npx mastra migrate`；Postgres 的 `mastra_threads.metadata` 与 `mastra_workflow_snapshot.snapshot` 从 TEXT 改 JSONB。
  - https://mastra.ai/reference/migrations/upgrade-to-v1/storage.md
- 【源码】`init()` 时对 `mastra_messages` 做 `alterTable({ ifNotExists: ['resourceId'] })`；Pg 还给每个 timestamp 列补 `*Z`（TIMESTAMPTZ）镜像列。这是向后兼容加列，不是版本迁移。
  - https://github.com/mastra-ai/mastra/blob/%40mastra/core%401.79.0/stores/libsql/src/storage/domains/memory/index.ts
- 查不到：针对存量 v1 消息的一次性 backfill 脚本；`mastra_traces` 常量在 1.79.0 运行时的实际使用点；v2 引入的确切版本号与 changeset。

---

## 5. LangGraph checkpointer 与 LangChain Postgres chat history

版本锚点：LangGraph tag `1.2.17`（2026-10-24）；`langchain-postgres` tag `v0.0.14`（GitHub 最新 tag；PyPI 0.0.19 的该文件与 `main` SHA `c531676` 逐字节相同）。

### 5.1 LangGraph checkpointer：整张图状态序列化，不按消息建表

- 【源码】`libs/checkpoint-postgres/langgraph/checkpoint/postgres/base.py` 的 `MIGRATIONS` 注释原文："To add a new migration, add a new string to the MIGRATIONS list. The position of the migration in the list is the version number." 共 10 条（v0–v9）：
  - v1 `CREATE TABLE IF NOT EXISTS checkpoints (thread_id TEXT NOT NULL, checkpoint_ns TEXT NOT NULL DEFAULT '', checkpoint_id TEXT NOT NULL, parent_checkpoint_id TEXT, type TEXT, checkpoint JSONB NOT NULL, metadata JSONB NOT NULL DEFAULT '{}', PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id));`
  - v2 `CREATE TABLE IF NOT EXISTS checkpoint_blobs (thread_id, checkpoint_ns TEXT DEFAULT '', channel TEXT NOT NULL, version TEXT NOT NULL, type TEXT NOT NULL, blob BYTEA, PRIMARY KEY (thread_id, checkpoint_ns, channel, version));`
  - v3 `CREATE TABLE IF NOT EXISTS checkpoint_writes (thread_id, checkpoint_ns TEXT DEFAULT '', checkpoint_id TEXT NOT NULL, task_id TEXT NOT NULL, idx INTEGER NOT NULL, channel TEXT NOT NULL, type TEXT, blob BYTEA NOT NULL, PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx));`
  - v4 `ALTER TABLE checkpoint_blobs ALTER COLUMN blob DROP not null;`；v5 是源码注释自述的 "no-op migration to ensure that the versions in the migrations table are correct"；v6–v8 是三条 `CREATE INDEX CONCURRENTLY IF NOT EXISTS …_thread_id_idx`；v9 `ALTER TABLE checkpoint_writes ADD COLUMN IF NOT EXISTS task_path TEXT NOT NULL DEFAULT '';`
  - v0 建 `checkpoint_migrations (v INTEGER PRIMARY KEY)`
  - https://github.com/langchain-ai/langgraph/blob/1.2.17/libs/checkpoint-postgres/langgraph/checkpoint/postgres/base.py#L46-L93
- 【源码】`Checkpoint` TypedDict 字段：`v`（"The version of the checkpoint format"）、`id`、`ts`、`channel_values: dict[str, Any]`、`channel_versions`、`versions_seen`、`updated_channels`——**整张图的 channel 值都在 `checkpoints.checkpoint` 这一行的 JSONB 里**。
  - https://github.com/langchain-ai/langgraph/blob/1.2.17/libs/checkpoint/langgraph/checkpoint/base/__init__.py
- 【源码】`metadata` JSONB 存 `source`（input/loop/update/fork）、`step`、`parents`，且源码显式 `pop("writes")`；langgraph 内部键在 `EXCLUDED_METADATA_KEYS` 里不进 metadata。
- 【源码】primitive/非 primitive 分流（`PostgresSaver.put`）：
  ```python
  # inline primitive values in checkpoint table
  # others are stored in blobs table
  for k, v in checkpoint["channel_values"].items():
      if isinstance(v, _DeltaSnapshot): ...  # 哨兵 True，真值进 blobs
      elif v is None or isinstance(v, (str, int, float, bool)): pass
      else: blob_values[k] = copy["channel_values"].pop(k)
  ```
  - 判据是**类型，不是大小**。消息列表（`list[AnyMessage]`）必然进 `checkpoint_blobs`（BYTEA，默认 `JsonPlusSerializer` 走 msgpack）。
  - https://github.com/langchain-ai/langgraph/blob/1.2.17/libs/checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py#L314-L324
- 【源码】`checkpoint_writes` 每 `(thread_id, checkpoint_ns, checkpoint_id, task_id, idx)` 一行；`put_writes` 的 `writes: Sequence[tuple[str, Any]]` 是 `(channel, value)`，`_dump_writes` 展开成每 task/channel 一行；`WRITES_IDX_MAP = {ERROR: -1, SCHEDULED: -2, INTERRUPT: -3, RESUME: -4}` 用负数 idx 避免冲突。
  - 所以**工具调用结果（ToolMessage）就是该 task 对 `messages` channel 的一次 write，作为 BYTEA msgpack 存在 `checkpoint_writes.blob`**，superstep 提交后才合并进下一行的 `checkpoint_blobs`。
- 【源码】消息侧：`MessagesState.messages: Annotated[list[AnyMessage], add_messages]`——**没有独立消息表**，消息是 state 的一个 channel；`AIMessage.tool_calls`/`usage_metadata` 嵌在 AIMessage 行里，`ToolMessage.tool_call_id`/`artifact`/`status` 是独立一条消息。
  - https://github.com/langchain-ai/langgraph/blob/1.2.17/libs/langgraph/langgraph/graph/message.py
  - https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D1.7.0/libs/core/langchain_core/messages/tool.py

【推断】LangGraph 完全放弃了"按消息查询"的 SQL 能力：要按 message 查必须反序列化 blob。这是"整段状态序列化"路线的代价。

### 5.2 调试依据：快照链 + LangSmith，两条线

- 【文档】checkpointer 被定义为 "a snapshot of the graph state saved at each super-step"；super-step 是 "a single 'tick' of the graph where all nodes scheduled for that step execute (potentially in parallel)"；用途明确列 "Time travel: allowing users to replay prior graph executions to review and / or debug specific graph steps."
  - https://docs.langchain.com/oss/python/langgraph/checkpointers
- 【文档】`get_state_history(config)` 返回 "History is in reverse chronological order."；Replay "re-executes nodes—it doesn't just read from cache"；`update_state` "does not roll back a thread"，而是 "creates a new checkpoint that branches from the specified point"。
  - https://docs.langchain.com/oss/python/langgraph/use-time-travel
- 【文档】LangSmith："Traces are a series of steps that your application takes to go from input to output."、每个 step 是 "a run"；需 `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY`。
  - https://docs.langchain.com/oss/python/langgraph/observability
- 【推断】checkpoint 链给"图分了几步/每步的状态"，LangSmith 给"每次 LLM/工具调用的耗时、token、input/output"。官方把它们当不同机制分开描述，checkpointers 页面建议用 LangSmith 追踪 checkpointed state。
- 查不到：官方 checkpointers 文档对 `checkpoint_blobs` 表的任何描述（只有源码）；`parent_checkpoint_id`/"链表"的文档表述（只在自定义 checkpointer 一节以 `parent_config` 形式出现）。

### 5.3 迁移史

- 【源码】`checkpoint_migrations` 只记录已应用版本；`setup()` 先建表，再 `SELECT v … ORDER BY v DESC LIMIT 1`，然后逐条执行 `MIGRATIONS[version + 1:]`。
- 【源码】**没有 DROP / 删数据的迁移**：全部是 `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX CONCURRENTLY IF NOT EXISTS` / `ALTER … ADD COLUMN IF NOT EXISTS` / 一次 `DROP not null` / 一次 no-op。`CONCURRENTLY` 要求 autocommit（README 明确要求 `autocommit=True` 与 `row_factory=dict_row`）。
  - https://github.com/langchain-ai/langgraph/blob/1.2.17/libs/checkpoint-postgres/README.md
- 【源码】另有 `prune()`（v1.2.17 新增，`keep_latest` / `delete`）与 `delete_thread()`（三张表分别 DELETE）。
- 【源码】`v < 4` 且有 parent 的 checkpoint 会触发 pending sends 迁移（`_migrate_pending_sends`），说明 checkpoint 格式 `v` 到过 4+；当前 `LATEST_VERSION = 2`，属旧数据兼容路径。

### 5.4 LangChain `PostgresChatMessageHistory`：一条消息一行，整条消息 JSONB

- 【源码】当前实现在 `langchain-postgres` 包的 `chat_message_histories.py`（注意文件名是复数）：
  ```sql
  CREATE TABLE IF NOT EXISTS {table_name} (
      id SERIAL PRIMARY KEY,
      session_id UUID NOT NULL,
      message JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  CREATE INDEX IF NOT EXISTS idx_{table_name}_session_id ON {table_name} (session_id);
  ```
  - 读取 `SELECT message FROM {table} WHERE session_id = %(session_id)s ORDER BY id;`
  - `session_id` 必须是合法 UUID（否则 `ValueError`）；`table_name` 必须匹配 `^\w+$`
  - https://github.com/langchain-ai/langchain-postgres/blob/v0.0.14/langchain_postgres/chat_message_histories.py#L27-L39
  - 【源码】旧 `langchain-community` 实现（`@deprecated(since="0.0.31")`）默认表名是 `message_store`，schema 略不同（`session_id TEXT`、无 `created_at`）——网上常见的 `message_store` 形状指的是那个废弃实现。
    https://github.com/langchain-ai/langchain/blob/langchain-community%3D%3D0.3.22/libs/community/langchain_community/chat_message_histories/postgres.py
- 【源码】一条消息一行，整条 `BaseMessage` 序列化：`values = [(self._session_id, json.dumps(message_to_dict(message))) for message in messages]`，而 `message_to_dict = {"type": message.type, "data": message.model_dump()}`。
  - 因此 `data` 含 `content`、`additional_kwargs`、`response_metadata`、`id`、`name`；AIMessage 还有 `tool_calls`/`invalid_tool_calls`/`usage_metadata`；ToolMessage 还有 `tool_call_id`/`artifact`/`status`。
  - https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D1.7.0/libs/core/langchain_core/messages/base.py
- 【源码】`ToolMessage` 是独立一行（`type == "tool"`），与 HumanMessage/AIMessage 平级；`tool_calls` 不单独成行，嵌在对应 AIMessage 那一行的 `data.tool_calls` 里。**同一 session 内顺序只靠 `id SERIAL`，没有 thread/turn 概念。**
- 推理落点（都在同一个 JSONB 里）：
  - 【源码】标准路径：Anthropic `thinking` block 原样进 `AIMessage.content`，`content_blocks` 翻译层转成 `{"type":"reasoning","reasoning":...,"extras":{"signature":...}}`。
    https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D1.7.0/libs/core/langchain_core/messages/block_translators/anthropic.py
  - 【源码】兼容路径：`additional_kwargs["reasoning_content"]`（Ollama/DeepSeek/XAI/Groq）；`ChatOpenAI` 的 `output_version='v0'` 会把 reasoning 搬进 `additional_kwargs["reasoning"]`。
    https://github.com/langchain-ai/langchain/blob/langchain-openai%3D%3D1.7.2/libs/partners/openai/langchain_openai/chat_models/_compat.py
- 【源码】**没有迁移/版本化机制**：`chat_message_histories.py` 里 grep 不到 migration/version/ALTER 逻辑，只有 `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS` 与 `drop_table`；没有 schema version 列，旧表列不同时 `create_tables` 不会改它。
- 【源码】生命周期信号：`BaseChatMessageHistory` 在 langchain-core 1.6.4 起已 `@deprecated(removal="2.0.0")`，官方短期记忆文档只讲 `PostgresSaver`，完全没提 `PostgresChatMessageHistory`。
  - https://docs.langchain.com/oss/python/langchain/short-term-memory
- 查不到：docs.langchain.com 上 `PostgresChatMessageHistory` 的专页（返回 404），只有 GitHub README 与源码 docstring。

---

## 6. Pydantic AI 的 message history 序列化

版本锚点：tag `v2.61.0`（2026-10-23）。源码基址 `pydantic_ai_slim/pydantic_ai/messages.py`；文档基址 `https://pydantic.dev/docs/ai/`（`ai.pydantic.dev` 已 301 跳转至此）。

### 6.1 序列化边界：`ModelMessagesTypeAdapter`，一条消息 = 一个 request/response 对象

- 【源码】`ModelMessage = Annotated[ModelRequest | ModelResponse, pydantic.Discriminator('kind')]`。
  - `ModelRequest`：`parts`、`timestamp`、`instructions`、`kind`、`run_id`、`conversation_id`、`metadata`、`state`（`complete|interrupted`）。
  - `ModelResponse`：`parts`、`usage`（含 `cost`）、`model_name`、`timestamp`、`kind`、`provider_name`、`provider_url`、`provider_details`、`provider_response_id`、`finish_reason`、`run_id`、`conversation_id`、`metadata`、`workspace_ref`、`history_digest`、`state`。
  - 便利属性 `text`/`thinking`/`tool_calls`/`cost()` 都是派生 property，**不是序列化字段**。
  - https://github.com/pydantic/pydantic-ai/blob/v2.61.0/pydantic_ai_slim/pydantic_ai/messages.py
- 【源码】`ModelRequestPart`（用 `part_kind` 判别）：`system-prompt`、`user-prompt`、`speech`、`tool-return`、`retry-prompt`（v2 已弃用，v3 删）、`retry-feedback`、`tool-availability-delta`、`instruction-delta`、`instruction-baseline`、`legacy-retry-tool-return`、`legacy-retry-feedback`（后两者是 `BeforeValidator(_translate_legacy_retry_part)` 的读入升级入口）。
- 【源码】`ModelResponsePart`：`text`、`tool-call`、`builtin-tool-call`、`builtin-tool-return`、`thinking`、`compaction`、`file`、`speech`、`tool-search-call`、`capability-load-call` 等。
  - 命名注意：`BuiltinToolCallPart`/`BuiltinToolReturnPart` 是 **v1 类名**，v2.61.0 已改名 `NativeToolCallPart`/`NativeToolReturnPart`，但**线上 `part_kind` 值保留 `builtin-tool-call`/`builtin-tool-return`**，V1 存的 JSON 仍能读。
- 【源码】`ModelMessagesTypeAdapter = pydantic.TypeAdapter(list[ModelMessage], config=ConfigDict(defer_build=True, ser_json_bytes='base64', val_json_bytes='base64'))`。
  - https://github.com/pydantic/pydantic-ai/blob/v2.61.0/pydantic_ai_slim/pydantic_ai/messages.py#L4529-L4533
- 【源码】`all_messages_json()` / `new_messages_json()` 返回 JSON bytes，内部就是 `ModelMessagesTypeAdapter.dump_json(...)`；`bytes` 字段在 JSON 里以 base64 字符串往返。
- 【文档】官方文档原文："The intended way to do this is using a `TypeAdapter`."，给出 `to_jsonable_python` + `validate_python` 与 `to_json` + `validate_json` 两条等价路线。
  - https://pydantic.dev/docs/ai/core-concepts/message-history/
- 【源码】测试里的 JSON 字面量就是数组，元素形如 `{"parts":[{"content":"Hello",...,"part_kind":"user-prompt"}],"kind":"request"}` 与 `{"parts":[{"tool_name":"my_tool","args":"{}","tool_call_id":"call_1","part_kind":"tool-call"}],"model_name":"test",...,"kind":"response"}`。
  - https://github.com/pydantic/pydantic-ai/blob/v2.61.0/tests/test_messages.py

### 6.2 工具调用 / 工具结果 / 推理

- 【源码】三者都是**同一个 JSON blob 里** request/response 对象的 `parts` 元素，用 `part_kind` 判别：
  - `ToolCallPart`（response 侧）：`tool_name`、`args`、`tool_call_id`。
  - `ToolReturnPart`（request 侧）：`tool_name`、`content`（可多模态）、`tool_call_id`、`tool_kind`、`metadata`、`outcome`（`success|failed|denied|interrupted|retried`）。
  - `ThinkingPart`：`content`、`id`、`signature`、`provider_name`、`provider_details`。`signature` 的 provider 映射：Anthropic=`signature`、Bedrock=`signature`、Google=`thought_signature`、OpenAI=`encrypted_content`；**签名只回送同一 provider**。
  - `NativeToolReturnPart` 属 **ModelResponsePart**（response 侧），不是 request part。
- 【文档】**官方没有给出任何数据库表结构/DDL**。persistence 文档原话："Pydantic AI is deliberately unopinionated about your database. It gives you a full-fidelity serialization boundary and leaves the schema to you"，并建议 "a `jsonb` column is enough for that"。
  - https://pydantic.dev/docs/ai/persistence/
- 【源码】官方最小可运行示例只有 SQLite 单表：`CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY, message_list TEXT);`，写入 `result.new_messages_json()`，读取 `ModelMessagesTypeAdapter.validate_json(row[0])` 后 extend。
  - https://github.com/pydantic/pydantic-ai/blob/v2.61.0/examples/pydantic_ai_examples/chat_app.py#L178-L181
- 【文档】v2.55.0 起推荐改为存整份 `Conversation`（`ConversationTypeAdapter.dump_json`），仍是一个 `jsonb` 列，键为 `conversation_id`。
- 【文档】有官方表结构的是**独立的 Pydantic AI Harness** `StepPersistence`：SQLite 有 `runs`/`events`/`snapshots`/`snapshot_messages`/`snapshot_message_refs`/`snapshot_idempotency_keys`/`tool_effects`/`media`；Postgres 为 `{table}_runs`/`_events`/`_snapshots`/`_keys`/`_messages`/`_tool_effects`/`_media`；消息按 SHA-256 内容寻址只存一份。
  - https://pydantic.dev/docs/ai/harness/step-persistence/

### 6.3 调试依据：消息历史 + OTel span + 步骤快照

- 【文档】`result.all_messages()` / `new_messages()`；`agent.iter()` 逐节点迭代 `ModelRequestNode` / `CallToolsNode` / `End`，文档称 "Each node represents a step in the agent's execution"；`capture_run_messages()` 用于异常路径（含 `state='interrupted'` 的部分消息）。
  - https://pydantic.dev/docs/ai/agent/
- 【文档】Logfire/OTel 是官方主推观测路径："A trace is generated for the agent run, and spans are emitted for each model request and tool call." 消息内容落在 span 属性：`gen_ai.input.messages` / `gen_ai.output.messages`（model request span）、`pydantic_ai.all_messages`（agent run span）；运行级 token 在 `gen_ai.aggregated_usage.*`。instrumentation format 默认 `version=5`，`version=6` opt-in（工具结果改用 `role: "tool"`）。
  - https://pydantic.dev/docs/ai/integrations/logfire/
- 【文档】Harness `StepPersistence` 在每个 settled tool-call 边界存 snapshot + 事件日志 + 工具副作用账本，用于崩溃后续跑/分叉。

### 6.4 迁移史：两次大重构 + 显式的"无版本号"策略

- 【源码】v0.0.12 及更早：扁平消息联合，用 `role` 判别（`SystemPrompt`/`UserPrompt`/`ToolReturn`/`RetryPrompt`/`ModelTextResponse(content)`/`ModelStructuredResponse(calls)`），adapter 名为 `MessagesTypeAdapter`。
- 【文档】**v0.0.13（2024-12-16）是最大的一次破坏性重构**，release notes 原文："The format of messages has changed significantly since the last release"，指向 PR #232 "Unify model responses" 与 PR #259 "Reformat messages so messages become simple `list[ModelRequest | ModelResponse]`"。此后才有 `parts`/`part_kind`/`kind`，adapter 改名 `ModelMessagesTypeAdapter`。
  - https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.13
  - 【源码】修正一处常见说法：查不到 `ModelResponse.data` 这个序列化字段；`ModelResponse.tool_calls` 从 v0.0.48 起就是 property，不是字段。被 `parts` 真正取代的是 pre-0.0.13 的 `ModelTextResponse.content` + `ModelStructuredResponse.calls` 拆分模型。
- 【文档】后续确认的变更：
  - v0.2.0：`ModelResponse` 加 `usage` 字段，带 default factory，注明 "so it'll work to load data that doesn't have usage"（向后兼容）。
  - v0.3.0：新增 `ThinkingPart`（当时选择不回传 provider）。
  - v0.6.0→v0.7.0：`ModelResponsePart` 联合扩为加上 `BuiltinToolCallPart`/`BuiltinToolReturnPart`。
  - v1.0.0（2025-09-04）：`parts` 由 `list` 改 `Sequence`；大量 dataclass 改 kw_only。
  - v1.1.0（2025-10-15）：`ThinkingPart` 加 `provider_name`，`signature` 语义扩展到 Bedrock/Google/OpenAI；`signature` 字段本身从 v0.3.0 起一直存在，无破坏性变更。
  - v2.0.0（2026-06-23）：`BuiltinToolCallPart`→`NativeToolCallPart` 等重命名；`vendor_details`→`provider_details`；`Usage`→`RunUsage`；`request_tokens`/`response_tokens`→`input_tokens`/`output_tokens`。**官方明确："The serialized `part_kind` wire values and the old field names' validation aliases are retained, so message history written by V1 still deserializes in V2."**
    https://pydantic.dev/docs/ai/migration/
  - v2.55.0（2026-10-09，PR #8337）：新增 `Conversation`/`ConversationTypeAdapter`。
  - V2 新弃用（v3 删除）：`RetryPromptPart` 拆成 `ToolReturnPart(outcome='retried')` + `RetryFeedbackPart`，旧 JSON 读入时自动翻译。
- 【源码】**`ModelMessagesTypeAdapter` 没有版本字段**：对 `messages.py` 与 `conversation.py` 全文 grep `version`，只命中 OTel `InstrumentationSettings.version` 与 instruction 命名空间版本等无关项。
- 【文档】官方靠三条机制替代显式版本号：
  - Version Policy 明确把"新增 message part / stream event / 可选字段"列为非破坏性变更："Adding new message parts, stream events, or optional fields (including fields with default values) on existing message (part) and event types... use the `ModelMessagesTypeAdapter` to (de)serialize message histories."
    https://pydantic.dev/docs/ai/project/version-policy/
  - 保留 `part_kind` 线上值 + 旧字段名 `validation_alias`（`vendor_details`→`provider_details`）。
  - 读入时 `BeforeValidator` 翻译旧 part。
  - persistence 文档直接说 "No schema migration is needed when Pydantic AI adds a message part, because a conversation serialized by an older version still deserializes."
- 【推断】含义：不要自己给 message blob 加 version 列去兼容上游格式；要版本化的是你自己包在外层的信封（官方 "Storing complete run results" 一节的 `StoredRun(result=...)` 就是这个做法）。
- 查不到：独立的 "message format migration guide" 页面（迁移入口就是 `docs/migration` 的 V1→V2 映射表与 changelog）。

---

## 7. 对比表

| 项目 | 粒度 | 工具调用位置 | 推理位置 | 调试依据 | 迁移史 |
| --- | --- | --- | --- | --- | --- |
| OpenAI Agents SDK Session | 一行一个 Responses item（user/assistant/function_call/function_call_output/reasoning 各自一行），`message_data` 存整条 item JSON | 独立 item（`function_call`，`call_id`+`arguments`），一行 | 独立 `reasoning` item（`summary`/`encrypted_content`），一行；`reasoning_item_id_policy` 控制 id 回放 | 独立 tracing span（trace→task/turn/agent/generation/function span，带 usage、输入输出）；扩展版另有 `message_structure`/`turn_usage` 辅助表 | 无表版本号、无迁移框架（生产自管）；`RunState` 快照另有 1.0→1.21 版本策略 |
| OpenAI Responses / Conversations | 一行一个 item，29 种判别 `type` | 独立 `function_call` item | 独立 `reasoning` item（`encrypted_content` 必须回放） | item 流只给重放顺序；性能/调用看平台 Traces | 只加新 `type`，不改旧字段 |
| Letta | 一行 = 一次 LLM 调用的产物（assistant 消息含 reasoning parts + tool_calls；tool 消息含 tool_returns），`content` 列存 parts JSON | 同一行：legacy `tool_calls` JSON 列 + 新 `content[].type='tool_call'` part 并存；并行调用全塞进一条消息 | 同一行：`content[]` 里 `reasoning`/`redacted_reasoning`/`omitted_reasoning`/`summarized_reasoning`（含 `signature`、`encrypted_content`） | 独立 `steps` + `step_metrics` + `provider_traces`（完整请求/响应）+ OTel；消息靠 `step_id`/`run_id` 关联 | Alembic 167 个迁移；`2cceb07c2384` 加 `content` parts 列；`text` 字段 legacy 兜底 |
| Mastra | 一条消息一行，`content`（text 列）存 `{format:2, parts:[...]}` JSON | 同一 part `type:'tool-invocation'`，结果就地改 `state:'result'` 写 `result` 字段 | 同一行 `type:'reasoning'` part（`details` 含 redacted） | 独立 `mastra_ai_spans`（traceId/spanId/parentSpanId，`agent_run`→`model_step`/`tool_call`），消息里只有 `step-start` part | v1→v2 靠读时转换（无回填）；短暂 v3 后删除；`MastraMessageV2`→`MastraDBMessage`；v1 升级有 `npx mastra migrate`（span 唯一约束） |
| LangGraph checkpointer | 一个 superstep 一行 `checkpoints`（整图 channel values 序列化）；primitive 内联 JSONB，其余（含消息列表）按 channel 拆进 `checkpoint_blobs`（BYTEA msgpack）；pending writes 每 (task_id, channel) 一行 `checkpoint_writes` | 消息列表是 `messages` channel 的值，无独立消息表；工具结果 = task 对 `messages` channel 的一次 write，先在 `checkpoint_writes.blob`，提交后并入 `checkpoint_blobs` | 跟随消息对象序列化进 blob（AIMessage 的 `additional_kwargs`/`response_metadata`），无专门字段 | checkpoint 快照链（`get_state_history`，`parent_checkpoint_id` + `metadata.step/source`）+ LangSmith run trace（官方分开描述） | `MIGRATIONS` v0–v9，`checkpoint_migrations` 记录版本；无 DROP/删数据迁移；只有 `IF NOT EXISTS` 加列与加索引；v4 曾 `DROP not null` |
| LangChain Postgres chat history | 一条消息一行，`message JSONB` 存整条 `BaseMessage`（`message_to_dict` = `{type, data}`） | `tool_calls` 嵌在对应 AIMessage 行的 `data.tool_calls`；`ToolMessage` 是独立一行（`data.tool_call_id`/`artifact`/`status`） | 同一 JSONB：`data.content` 里的 reasoning block（标准路径）或 `data.additional_kwargs['reasoning_content'/'reasoning']`（v0 兼容路径）；`signature` 进 `extras` | 无。`BaseChatMessageHistory` 已 deprecated（`removal="2.0.0"`）；官方短期记忆文档只推 `PostgresSaver` | 无迁移机制、无 schema version 列，只有 `CREATE TABLE IF NOT EXISTS` |
| Pydantic AI | 一条消息 = 一个 request/response 对象（含 `parts` 数组），整段 history 序列化成 JSON **数组**（官方不给定表结构，只给 `TypeAdapter` 契约） | response 的 `parts[]` 里 `part_kind:'tool-call'`；request 的 `parts[]` 里 `part_kind:'tool-return'`（带 `outcome`），同一个 blob | response 的 `parts[]` 里 `part_kind:'thinking'`（`signature` 按 provider 映射到 Anthropic/Bedrock `signature`、Google `thought_signature`、OpenAI `encrypted_content`） | 消息历史本身（`all_messages()`/`agent.iter()` 节点迭代）+ Logfire/OTel span（`gen_ai.input.messages`、`pydantic_ai.all_messages`）+ Harness `StepPersistence` 快照 | 无 schema version 字段；靠保留 `part_kind` 线上值、旧字段 `validation_alias`、读入 `BeforeValidator` 翻译 + Version Policy 声明"加 part 非破坏性"；两次大重构：v0.0.13（扁平 role → parts）、v2.0.0（重命名但 V1 JSON 仍可读） |
