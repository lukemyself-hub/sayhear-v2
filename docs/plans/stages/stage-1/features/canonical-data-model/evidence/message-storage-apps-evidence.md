# 开源终端 AI 聊天 / companion 应用如何存消息、工具调用与推理（证据）

日期：2026-10-24。只读调研，不修改仓库任何其他文件。

**主会话抽查（2026-10-24）：** 以下三条与原文一致：LobeChat `0014_add_message_reasoning.sql` 全文只有一句 ADD COLUMN；`ModelReasoning` 含 `content` 与原样保存的 `responseItems`（含 `encrypted_content`）；Open WebUI #11467 于提出当日以 NOT_PLANNED 关闭。其余条目未逐条复核。
动机：SayHear v2 在两条候选之间选消息存储形状——
A）每条消息一行，正文 text 列，工具调用/结果各自成行（kind 列区分），工具数据 jsonb，运行过程另有 run/attempt/输入快照；
B）每条消息一行，整条消息的 parts 数组（text/reasoning/tool/step-start）存一个 jsonb 列（AI SDK UIMessage 官方示例做法）。
现有约束见 [ADR 0010](../../../../../../adr/0010-minimal-data-contract-and-owner.md)。

标注约定：

- 【文档】= 官方文档、issue/PR 正文、release notes 等人类书写材料。
- 【源码】= 固定 commit 的源码；URL 里带完整 sha。
- 【推断】= 我根据源码结构得出的判断，不是官方表述。

证据边界：所有源码链接都锁定到 2026-10-24 当时的最新 `main`/`release`，下表给出锁定 sha。凡"查不到"的，明确写查不到。

| 项目 | 锁定版本 |
| --- | --- |
| LibreChat | `a378657583567310c841d652b0f6b00c83e2bd6b`（2026-10-24） |
| Open WebUI | `91ea4e3421d1d8069f13d4a463fcb5986d94ea60`（v0.12.3，2026-10-16） |
| LobeChat | `49204982cab98bfa2f2fb6831a34d5018a2af6be`（20261018 release，2026-10-18） |
| Vercel `ai-chatbot` | `main`（2026-10-24） |
| SillyTavern | `06bde939fb1e9c4c8d8641d810f0a916b5bce127`（release，2026-09-14） |

另有一份同目录的 `message-storage-frameworks-evidence.md` 覆盖 Agent 框架持久化层（OpenAI Agents SDK、Letta、Mastra、LangGraph、Pydantic AI 等），本文件只覆盖终端用户产品，两份互补。

---

## 0. 一句话结论

**没有一个项目采用候选 A 的"工具调用 / 工具结果 / 推理各自独立成行 + kind 列 + 独立 run/attempt 表"形状。** 真实世界的做法全部收敛到"一条消息一行 + 消息内 parts/content 数组存 json/jsonb"，只是数组的规范化程度、以及工具结果是否顺手拆到伴随表上，各有差异：

- LibreChat、Vercel chatbot 是"一条消息一行 + `content`/`parts` 数组（Mixed/json，无 schema 约束）"。
- LobeChat 是"一条消息一行 + `content` text 列 + `reasoning`/`tools`/`search`/`usage`/`metadata` 等 jsonb 列"，**是五家里唯一把 reasoning 与工具调用提升为具名列的**；工具调用本身仍是一个 jsonb 数组（`messages.tools`），工具执行的插件状态另有一对一伴随表 `message_plugins`。
- Open WebUI 历史上是"整段会话一个 JSON blob（`chat.chat`）"，2026 年起新增 `chat_message` 表做行级镜像，双写共存；工具调用、工具结果、推理都活在 blob 内同一个 `output` 数组里。
- SillyTavern 是"整段会话一个 JSONL 文件"，工具调用与推理都塞在消息行的 `extra` 对象里。

调试一次回答的过程：**五家全部靠消息存储本身 + 独立的可观测性设施（Langfuse/OpenTelemetry/PromptManager）**，没有任何一家有"run/attempt/输入快照"这样的第一等产品表。这与 ADR 0010 要求的 run/attempt/输入快照不同，属于 SayHear 自己的增值契约，不是行业基线。

---

## 1. LibreChat（MongoDB，content parts 数组）

### 1.1 存储粒度：一条消息一行，`content` 是 Mixed 数组

【源码】`packages/data-schemas/src/schema/message.ts` 的 Mongoose schema（锁定 commit `a378657…`）：

- 主键/归属：`messageId`（String, required, indexed）、`conversationId`（indexed）、`user`（String, indexed）、`tenantId`（indexed）。
- 正文：`text`（String）与 `content`（`type: [{ type: mongoose.Schema.Types.Mixed }], default: undefined, meiliIndex: true`）。
- `files`：同样是 `[{ type: Mixed }]`；`attachments`：Mixed。
- `expiredAt` + TTL index `{ expiredAt: 1 }, { expireAfterSeconds: 0 }`。

https://github.com/danny-avila/LibreChat/blob/a378657583567310c841d652b0f6b00c83e2bd6b/packages/data-schemas/src/schema/message.ts

要点：**MongoDB 侧 `content` 是 `Schema.Types.Mixed` 数组，没有任何 schema 校验**；parts 的"类型定义"只存在于 TypeScript 侧 `TMessageContentParts` 判别联合。也就是说结构约束在应用层，不在数据库层。

【源码】`packages/data-provider/src/types/content.ts` 定义 `TMessageContentParts`，成员按 `type` 判别：`error`、`think`（推理）、`steer`、`text`、`tool_call`、`image_file`、`summary`、`activity_label`，以及 agent 相关的 `image_url`/`video_url`/`input_audio`。text part 带 `tool_call_ids?: string[]`；tool_call part 是 `tool_call: (CodeToolCall | RetrievalToolCall | FileSearchToolCall | FunctionToolCall | AgentToolCall) & PartMetadata`。**没有独立的 tool_result part**——code_interpreter 的结果是 `CodeToolCall.outputs`，function 的结果是 `FunctionToolCall.output`（nullable）。

https://github.com/danny-avila/LibreChat/blob/a378657583567310c841d652b0f6b00c83e2bd6b/packages/data-provider/src/types/content.ts

【源码】落盘路径在 `api/app/clients/BaseClient.js`：assistant 响应最终 `responseMessage.content = completion`（数组，agents/参数化端点路径）或 `responseMessage.text = completion.join('')`（传统端点只有纯文本）；随后 `saveMessageToDatabase` 调 `db.saveMessage`。

https://github.com/danny-avila/LibreChat/blob/a378657583567310c841d652b0f6b00c83e2bd6b/api/app/clients/BaseClient.js#L1095-L1130 、`#L1355-L1400`

【源码】用户消息只有 `text`（String），没有 `content` parts；`content` 是 assistant 侧才有的数组。

### 1.2 工具调用、工具结果、推理分别在哪

- **工具调用/结果**：同在 `content` 数组的一个 `tool_call` part 里（`function.arguments` + `function.output`）。LibreChat 还对单个 part 做**数据库内定点更新**：`packages/data-schemas/src/methods/message.ts` 用 `'content.$[part].tool_call.output' = output` 这样的 MongoDB positional 更新把工具结果写回原 part，而不是另起一行。
  https://github.com/danny-avila/LibreChat/blob/a378657583567310c841d652b0f6b00c83e2bd6b/packages/data-schemas/src/methods/message.ts
- **推理原文**：`content` 里的 `think` part，字段是 `think`（`string | TextData`）＋ `reasoning_label`、`reasoning_label_step_id`、`_attempts`、`_revision`、`_submitted_chars`、`reasoning_unavailable` 等。**保存推理原文**（明文字符串），同时另有 `reasoningOverride`（`{key: reasoning_effort|effort|thinkingLevel|thinkingBudget, value: Mixed}`）记录这一轮用的推理档位，存在消息行上。
- 另有一个只读字段 `select: false` 的 `privateText`（String 数组）与 `privateTextTokens`，用于不进入常规投影的私有内容。

### 1.3 调试一次回答的过程靠什么

- 消息存储本身承载 UI 渲染所需的全部 parts（`ContentParts.tsx` 按 part type 渲染）。
- 另有 Langfuse 集成字段挂在消息行上：`langfuseSampled`、`langfuseDestinationIds`、`langfuseRunId`；`api/server/services/LangfusePromptSync.js`。
- 【推断】还有一组 `select: false` 的 subagent 投影字段（`subagentTranscript.messagesJson`、`subagentActivityProjection.activityJson`、`subagentTriggerProjection`、`subagentTask`），用于把子 agent 的运行过程以 JSON 字符串形式挂在消息行内，是"过程信息"而非"用户可见消息内容"。

### 1.4 迁移史与问题

- **content parts 化是一次显式迁移**：【文档】PR #8171 "feat: Save & Submit Message Content Parts"（2025-07-01 合并）说明"removed the legacy `generation` user message field for message and agent histories""refactored message update APIs to support updating either TEXT or THINK content"，并自我标注为 breaking change。
  https://github.com/LibreChat-AI/LibreChat/pull/8171
  当前 schema 里仍留着 `/** @deprecated */ generation` 字段作兼容，以及把 reasoning 与 tool 活动统一进一个 activity 系统的 PR #14546。
  https://github.com/LibreChat-AI/LibreChat/pull/14546
- **MongoDB 16MB 单文档上限撞过墙**：【文档】PR #14157 "Guard HITL checkpoint size against MongoDB 16MB limit"——LangGraph HITL checkpoint 把整段序列化消息历史塞进一个 BSON 文档，"Large conversations — inlined base64 media, big tool outputs, long histories — can serialize past MongoDB's 16 MB document ceiling"，加了 8MB 软告警 / 15MB 硬限制。
  https://github.com/LibreChat-AI/LibreChat/pull/14157
- **围绕 reasoning 反复出渲染/导出 bug**（都是 Mixed 数组 + 无 schema 校验的直接后果）：#14102 "Markdown export dumps raw JSON for reasoning/THINK content parts"、#16674 / #14750 / #11381 "TTS reads reasoning content aloud"、#13541 "Answer text duplicated in content[]"。
  https://github.com/LibreChat-AI/LibreChat/issues/14102
  https://github.com/LibreChat-AI/LibreChat/issues/16674
- 【推断】2026 年的趋势是把"必须原样回传给 provider 的 provider 输出项"从 `content` 里搬到 `select:false` 的 `providerItems`（PR #17149），理由是 Responses API 的 tool round 需要把 ids/status/encrypted reasoning 原样送回。这说明"content parts 数组"承载不了所有需求，需要伴随字段。
  https://github.com/LibreChat-AI/LibreChat/pull/17149

---

## 2. Open WebUI（SQLite/Postgres，先整段 JSON blob，再补 chat_message 表）

### 2.1 存储粒度：一个 chat 一个 JSON blob + 一张行级镜像表（双写）

【源码】`backend/open_webui/models/chats.py`：`chat` 表列 = `id`(PK)、`user_id`、`title`、`chat`(JSON)、`created_at`、`updated_at`、`share_id`、`archived`、`pinned`、`meta`(JSON, default `{}`)，以及 `variables`/`folder_id`/`tasks`/`summary`/`current_message_id`/`last_read_at`/`timer_at`。消息活在 `chat.history.messages`（按 messageId 索引的 map，每项 `parentId`/`childrenIds`/`role`/`content`/`timestamp`），旧布局是 `chat.messages` 数组，代码两处都读。当前指针从 `history.currentId` → `chat.currentId` → `branchPointMessageId` 依次回退。

https://github.com/open-webui/open-webui/blob/91ea4e3421d1d8069f13d4a463fcb5986d94ea60/backend/open_webui/models/chats.py

【源码】`backend/open_webui/models/chat_messages.py`：`chat_message` 表，列 = `id`(Text PK)、`chat_id`(FK→chat.id cascade)、`user_id`、`role`、`parent_id`、`content`(JSON，"Can be str or list of blocks")、`output`(JSON)、`model_id`、`files`/`sources`/`embeds`/`meta`(JSON)、`done`、`status_history`(JSON)、`error`(JSON)、`usage`(JSON)、`context_summary`(Text)、`created_at`、`updated_at`。主键 id 是代码拼的 `f'{chat_id}-{message_id}'`；`DB_TO_JSON_KEY_MAP` 做列名↔JSON 键映射（`parent_id`↔`parentId` 等）；没有行时返回 None，"caller should fall back to the embedded JSON blob for legacy chats"。

https://github.com/open-webui/open-webui/blob/91ea4e3421d1d8069f13d4a463fcb5986d94ea60/backend/open_webui/models/chat_messages.py

【源码】这张表的来历：commit `599cd2eeeb` "feat: analytics backend API with chat_message table"（2026-02-01），"Add chat_message table for message-level analytics with usage JSON field / Add migration to backfill from existing chats"，同时加了 `/analytics` 路由。也就是说**动机是分析统计，不是渲染路径**。
https://github.com/open-webui/open-webui/commit/599cd2eeeb898b9b313abf137f860d1abb62c836

【源码】迁移 `8452d01d26d7_add_chat_message_table.py` 的 docstring 只有 "Add chat_message table"，内联注释 "Step 2: Backfill from existing chats"，**没有任何一句说明为什么弃用 blob 或 blob 慢**。
https://github.com/open-webui/open-webui/blob/91ea4e3421d1d8069f13d4a463fcb5986d94ea60/backend/open_webui/migrations/versions/8452d01d26d7_add_chat_message_table.py

### 2.2 工具调用、工具结果、推理在哪

都在消息的 **`output` 列表**里，按 `type` 判别，**与 `content` 并列而不是混在正文里**：

- 工具调用：`{'type': 'function_call', 'id', 'call_id', 'name', 'arguments', 'status': 'in_progress'}`。
- 工具结果：`{'type': 'function_call_output', ...}`。
- 推理：`{'type': 'reasoning', 'id', 'status', 'start_tag': '<think>', 'end_tag': '</think>', 'attributes': {'type': 'reasoning_content'}, 'content': [{'type': 'output_text', 'text': ...}], 'summary', 'started_at', 'ended_at', 'duration'}`——**保存推理原文**，并带 `reasoning_details` 键（流式增量按 index 归并）。
- 普通正文：`{'type': 'message', ...}`。
- 另有 `open_webui:code_interpreter` 自定义 item type。

https://github.com/open-webui/open-webui/blob/91ea4e3421d1d8069f13d4a463fcb5986d94ea60/backend/open_webui/utils/middleware.py（`L370 merge_streamed_reasoning_details`、`L1876 MESSAGE_REPLAY_KEYS`、`L1923 strip_reasoning_details`、`L5058 function_call`、`L5176 reasoning`、`L3268 function_call_output`）

【源码】`MESSAGE_REPLAY_KEYS = ('id','role','content','output','files','contextSummary','usage','model','meta')`；重放时 `convert_output_to_messages(message['output'], raw=True)` 产出 OpenAI 风格的 `tool_calls + tool results`，然后把 `output` 等键从发给 LLM 的消息里剥掉（`L1987`）。`reasoning_details` 只在同一 model/支持时回放，否则 `strip_reasoning_details` 剥掉（`L2171-2175`、`L2992-2993`）。**这是"provider 绑定的推理摘要不能跨模型回放"的显式处理**，与 SayHear 输入快照按 attempt 隔离的设计动机一致。

### 2.3 调试一次回答的过程靠什么

- 消息存储本身：`output` 数组保序、带 `status`/`started_at`/`ended_at`/`duration`；`status_history`（JSON）与 `usage`（JSON，tokens/timing）在 `chat_message` 行上。
- 另有一条 `context_summary`（Text，"Context compaction checkpoint"）——上下文压缩检查点存在消息行上。
- 独立的可观测设施：`backend/open_webui/utils/telemetry/`（OpenTelemetry metrics + traces，`ENABLE_OTEL_TRACES`/OTLP exporter），**不在消息表里**。
  https://github.com/open-webui/open-webui/blob/91ea4e3421d1d8069f13d4a463fcb5986d94ea60/backend/open_webui/utils/telemetry/setup.py

### 2.4 迁移史与问题（最丰富的一家）

**(a) 结构性问题从 2024 年就有人提**：【文档】issue #3620 "enh/issue: performance optimisation"（2024-07-04）："The performance of long chat threads is really bad"，用户靠开新对话绕开。
https://github.com/open-webui/open-webui/issues/3620

**【文档】issue #11467（2025-03-09）"feat: Chat Database Schema Update for Better Design, Performance, and Scalability"**：明确说"All chat messages for a chat live in a single JSON field in the Chat table, one row per chat""can be slow and when the number of messages get large, the json is getting very big and slow"，提议照搬 Vercel ai-chatbot 的 Chat/Message 两表。**同日被维护者以 not planned 关闭，无任何说明。** 结果项目自己两年后走了同一条路（先分析、再镜像表）。
https://github.com/open-webui/open-webui/issues/11467

**(b) blob → chat_message 的迁移在生产上炸过多次**：

- 【文档】issue #23134（2026-03-27）"Database migration chat → chat_message OOM-kills on large datasets (PostgreSQL/AlloyDB, ~75 GB)"，v0.8.5。
  https://github.com/open-webui/open-webui/issues/23134
- 【文档】issue #23273（2026-03-31）"Migration 8452d01d26d7 fails on large PostgreSQL datasets due to single-transaction backfill with FK/index maintenance"。
  https://github.com/open-webui/open-webui/issues/23273
- 修复：【文档】PR #24059 "fix(migration): batch chat_message backfill to prevent OOM"（2026-04-24）。
  https://github.com/open-webui/open-webui/pull/24059
- 前置修复：【文档】PR #22588 "handle non-dict history/messages in chat_message migration"（2026-03-11）、PR #21887 "handle non-numeric timestamp values in chat_message migration"（2026-02-26）——都是"旧 blob 里什么脏数据都有"的直接成本。

**(c) 双写导致的正确性问题**：

- 【文档】issue #28742（2026-08-18，v0.11.0）"unlocked chat-blob read-modify-write silently drops messages under concurrency (chat_message table diverges from chat.chat)"：正文直说"OWUI stores chat history in two places: the `chat.chat` JSON blob (`history.messages`, what `GET /api/v1/chats/{id}` returns to the frontend) and the normalized `chat_message` table (what generates LLM context…)… whole-blob read-modify-write functions in `chats.py` that take no row lock"，列出 5 个函数（`update_chat_by_id`、`update_chat_title_by_id`、`upsert_message_to_chat_by_id_and_message_id`、`add_message_status_to_chat_by_id_and_message_id`、`add_message_files_by_id_and_chat_by_id_and_message_id`）。
  https://github.com/open-webui/open-webui/issues/28742
- 【文档】issue #29501（2026-09-01）"SQLite 'chat_message' table 'updated_at' timestamp is overwritten with the latest message's timestamp"。
  https://github.com/open-webui/open-webui/issues/29501
- 【文档】issue #23152（2026-03-27）"Follow Ups corrupt usage statistic in chat_message table"，后续一串修复 PR。
  https://github.com/open-webui/open-webui/issues/23152

**(d) blob 的读路径与搜索性能**：

- 【文档】issue #23192（2026-03-29）"Runtime OOM: chat.chat JSON blob fully loaded into memory on every chat open — no column projection in read path"。
  https://github.com/open-webui/open-webui/issues/23192
- 【文档】issue #27221（2026-07-20）"perf: Slow chat search in PostgreSQL backend due to unindexable JSON deserialization (OR + EXISTS with json_array_elements)"。
  https://github.com/open-webui/open-webui/issues/27221
- 【文档】issue #27187（2026-07-18，仍 open）"feat: load long branched chats page by page instead of sending the whole history tree"，正文引用 #23733（流式期间反复全量传输，O(N²)）与 #24182（大聊天永远加载不完）。
  https://github.com/open-webui/open-webui/issues/27187
- 【源码】反过来也有一条：PR #23159 "perf: load chat message map from chat_message rows"（2026-03-27）**最终未合并**（closed, merged=false）——连"读路径改成走镜像表"这件事都推进得很艰难。
  https://github.com/open-webui/open-webui/pull/23159

**对 SayHear 的直接教训**：候选 A 的"工具调用/结果/推理各自成行"与候选 B 的"parts 一个 jsonb"都不是 Open WebUI 问题的根因；根因是**一份真相（blob）+ 一份镜像（行表）双写且无行锁**。SayHear 若选 B，需要保证 RLS 下单行更新是原子的；若选 A，需要保证一次 run 的多行写入也是原子的。

---

## 3. LobeChat（Postgres + Drizzle，一条消息一行 + 多个 jsonb 列）

### 3.1 存储粒度：一条消息一行，`content` 是 text 列，其余结构列都是 jsonb

【源码】`packages/database/src/schemas/message.ts`（锁定 `4920498…`）的 `messages` 表：

- `id` text PK（`idGenerator('messages')`）、`role` varchar255 notNull
- **`content` text 列**（纯文本正文；注意 `message_groups.content` 的注释说明它另有压缩摘要用途）
- `editorData` jsonb、`summary` text
- **`reasoning` jsonb（`$type<ModelReasoning>`）**
- `search` jsonb（`GroundingSearch`，搜索落地）
- `metadata` jsonb、**`usage` jsonb**（注释："Token usage + cost for this message, promoted out of `metadata.usage` into a dedicated column. New writes target this column exclusively; readers may temporarily fall back to `metadata.usage` for legacy rows."）
- `model`、`provider`、`favorite`、**`error` jsonb**、**`tools` jsonb**（工具调用在这里）
- `traceId`、`observationId`、`clientId` text
- 外键：`userId`(cascade)、`sessionId`(cascade)、`topicId`(cascade)、`threadId`、`parentId`(set null)、`quotaId`(set null)、`agentId`(cascade)、`groupId`(set null)、`messageGroupId`(cascade)、`workspaceId`(cascade)
- soft-delete 列 + timestamps
- 索引：`created_at`、unique(`client_id`,`user_id`)、`topic_id`、(`topic_id`,`updated_at`)、`parent_id`、`user_id`、`session_id`、`thread_id`、`agent_id`、`group_id`、`message_group_id`、`workspace_id`，以及两个表达式索引 `("usage"->>'cost')`、`("usage"->>'totalTokens')`。

https://github.com/lobehub/lobe-chat/blob/49204982cab98bfa2f2fb6831a34d5018a2af6be/packages/database/src/schemas/message.ts

【源码】`0000_init.sql` 里 `messages` 的 `tools` 与 `error` 从一开始就是 jsonb；`message_plugins` 的 `id` 是 `messages(id)` 的一对一 FK（`ON DELETE cascade`），所以**工具调用/插件状态不是"另一张多行表"，而是"同消息 id 的一对一伴随行"**。
https://github.com/lobehub/lobe-chat/blob/49204982cab98bfa2f2fb6831a34d5018a2af6be/packages/database/migrations/0000_init.sql

### 3.2 工具调用、工具结果、推理在哪

- **工具调用**：`messages.tools` jsonb，元素类型 `ChatToolPayload[]`（`{apiName, arguments, executor?, id, identifier, intervention?, result_msg_id?, source?, thoughtSignature?, type}`），合并结果后是 `ChatToolPayloadWithResult`（多一个 `result: ChatToolResult{content, contentLength?, error?, id, state?}`）。**调用与结果在同一个 jsonb 数组的同一元素里**，不是两行。
  https://github.com/lobehub/lobe-chat/blob/49204982cab98bfa2f2fb6831a34d5018a2af6be/packages/types/src/message/common/tools.ts
- **工具执行的插件状态**：`message_plugins` 一对一伴随行，列 `toolCallId`、`type`(default `'default'`)、`apiName`、`arguments`、`identifier`、`state` jsonb、`error` jsonb、`intervention` jsonb（`ToolIntervention`，人审批准/拒绝/中止的状态机）。写入路径：`packages/database/src/models/message.ts` `insertMessageRelationsInTransaction` 里 `if (message.role === 'tool')` 才插一行。
  https://github.com/lobehub/lobe-chat/blob/49204982cab98bfa2f2fb6831a34d5018a2af6be/packages/database/src/models/message.ts
  **注意**：`role === 'tool'` 的工具结果**确实是一条独立的 `messages` 行**（`toolCallId`/`tool_call_id` 指回调用方），但查询时刻意 `not(eq(messages.role, 'tool'))` 把它当"内联子节点"排除，渲染时作为调用方的子项挂回去。这是**最接近候选 A 的形状**：调用与结果各一行，但用父子内联语义而不是 kind 列平铺。
- **推理**：`messages.reasoning` jsonb，`ModelReasoning{content?: string, duration?, isMultimodal?, responseItems?: ModelReasoningResponseItem[], signature?, tempDisplayContent?}`。**保存推理原文（`content` 字符串）**；`responseItems` 注释写明"Original OpenAI Responses reasoning output item persisted verbatim so multi-turn stateless requests can replay it unchanged"，`encrypted_content` 存的是"scope-serialized envelope… never the raw provider payload"；`signature` 存 provider 签名。
  https://github.com/lobehub/lobe-chat/blob/49204982cab98bfa2f2fb6831a34d5018a2af6be/packages/types/src/message/common/base.ts
- **正文**：`content` text 列。压缩摘要另有 `summary` 列与 `message_groups.content`。

### 3.3 调试一次回答的过程靠什么

- 消息行上的 `traceId` / `observationId` 是 Langfuse/可观测系统的**外键式引用**（`packages/database/src/models/message.ts` 的 visitor allowlist 注释称其为"opaque ids scoped to THIS execution"），**过程数据本身不在数据库里**。
- 源码里另有 `packages/database/src/schemas/` 之外的性能/阶段计时（`runTimedStage`、`ModelTimingContext`）只进日志与 trace，不进产品表。

### 3.4 迁移史与问题

- 【源码】reasoning 列的来历可精确定位：migration `0014_add_message_reasoning.sql` 全文只有一句 `ALTER TABLE "messages" ADD COLUMN "reasoning" jsonb;`，来自 commit `f98bb5abc1` "✨ feat: support display thinking for DeepSeek R1 (#5558)"（2025-01-24），同 commit 把 `src/database/schemas/message.ts` 加上 `reasoning: jsonb('reasoning').$type<ModelReasoning>()`，并在 `src/types/message/base.ts` 新增 `ModelReasoning{content?, duration?}`。**这是一次纯增列、零回填、零旧数据迁移的 schema 演进**——jsonb 可空列天然支持"老消息没有 reasoning"。
  https://github.com/lobehub/lobe-chat/blob/49204982cab98bfa2f2fb6831a34d5018a2af6be/packages/database/migrations/0014_add_message_reasoning.sql
- 【源码】`usage` 列是第二次同类演进：从 `metadata.usage` 提升为独立 jsonb 列，读者暂时回退到 `metadata.usage` 兼容旧行（schema 注释原文见 3.1）。**"新列 + 读时回退"是它反复使用的迁移手法。**
- 【源码】迁移目录（`packages/database/migrations/`，0000–0081）显示大量增列/加索引型迁移：`0015_add_message_search_metadata`、`0016_add_message_index`、`0036_add_group_messages`、`0045_add_tool_intervention`（人审干预）、`0046_add_parent_id`、`0063_add_columns_for_several_tables`、`0073_add_message_group_metadata`、`0076_add_message_group_index`、`0081_switch_forgien_key_to_id_nanoid`。**没有一次是"改变消息存储形状"的重写。**
- 【推断】`0014` 这个"加一个 jsonb 列就支持一整类新内容"的模式，正是 SayHear 在候选 A 里用 `kind` 列 + jsonb 能达到的效果；LobeChat 的选择说明**先加列、后视需要拆表**在这类产品里是可接受且低成本的路。
- 【文档】未找到公开的、由存储格式变化引发的用户级数据迁移事故或社区抱怨（搜 issue/PR 未见对应条目）。性能相关多为索引类 PR（如 `81e56d462a` "perf: add more sql to improve performance"、`8abfdecd54`），非格式迁移。

---

## 4. Vercel `ai-chatbot` 模板（只需简述）

【源码】`lib/db/schema.ts`：`Message_v2` 表 = `id` uuid PK、`chatId` uuid FK→Chat、`role` varchar notNull、**`parts` json notNull**、**`attachments` json notNull**、`createdAt`。`Vote_v2` 复合 PK (`chatId`,`messageId`) 指向 `Message_v2.id`。
https://github.com/vercel/ai-chatbot/blob/main/lib/db/schema.ts

【源码】`lib/db/migrations/0000_initial.sql` 里就是 `Message_v2`，没有 `Message` 旧表——即当前 main 已把旧表删净。
https://github.com/vercel/ai-chatbot/blob/main/lib/db/migrations/0000_initial.sql

【文档】迁移过程记录在 PR #868 "refactor: replace message.content with message.parts"（2025-03-17 合并）："create tables `Message_v2` and `Vote_v2` with updated schema / update `components/message.tsx` to render content based on parts / add migration script and guide / replace `Message` type with `UIMessage`"。配套 `docs/04-migrate-to-parts.md` 给出三步：建新表并标记旧表 deprecated → 改渲染 → 跑 `lib/db/helpers/01-core-to-parts.ts` 回填。
https://github.com/vercel/ai-chatbot/pull/868

【源码】回填脚本 `lib/db/helpers/01-core-to-parts.ts` 按 chat 分批（`BATCH_SIZE = 50`），把旧 `Message.content` json 用 AI SDK 的 `appendResponseMessages` 重建成 `UIMessage[]` 再切出 `parts`。
https://github.com/vercel/ai-chatbot/blob/47a630fd53/lib/db/helpers/01-core-to-parts.ts

【文档】触发原因是 AI SDK 的 `parts` 属性引入（`@ai-sdk/react@1.1.10`，"The parts property supports different message types, including text, tool invocation, and tool result"）；文档示例的 `message.parts` 里含 `type === "reasoning"` 分支（`part.reasoning`）。
https://github.com/vercel/ai-chatbot/blob/47a630fd53/docs/04-migrate-to-parts.md

【文档】另有一次相关的反复：PR #1168 "chore: cleanup context window ui, adjust for reasoning + added db migration" 在 2025-09-08 被 PR #1169 **完整 revert**（同日），说明该仓库对"为 reasoning 改 schema"也做过回退。
https://github.com/vercel/ai-chatbot/pull/1169

【文档】AI SDK 侧对 parts 持久化的官方建议（2026-10-24 抓取）：存 `useChat` 的 UI 格式而非 model 格式；"Persist the full message, including its `parts`"；存工具调用时用 `validateUIMessages` 校验；`rawInput` 已废弃、下个大版本移除，需迁移到 `input`。
https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence

---

## 5. SillyTavern（整段会话一个 JSONL 文件）

### 5.1 存储粒度：一个聊天一个 `.jsonl` 文件，一行一个消息

【源码】`src/endpoints/chats.js`：写路径 `const jsonlData = chatData?.map(m => JSON.stringify(m)).join('\n');`——**无字段白名单，客户端送来什么就持久化什么**。第一行是 header 对象（importers 产出 `chat_metadata: {}` / `user_name: 'unused'` / `character_name: 'unused'`），后续每行一个消息对象（`name`、`is_user`、`send_date`、`mes`、`extra: {}`）。读路径 `lines.map(line => tryParse(line)).filter(x => x)` 逐行解析、坏行丢弃；`chat_items` = 行数减 header。文件路径 `chats/{avatar}/{character_name} - {humanizedISO8601DateTime}.jsonl`。
https://github.com/SillyTavern/SillyTavern/blob/06bde939fb1e9c4c8d8641d810f0a916b5bce127/src/endpoints/chats.js

【推断】消息行字段（`swipes` 数组、`swipe_id` 当前选中下标、`swipe_info` 每条 swipe 的元数据、`extra` 自由对象）属于事实上的 schema，散落在前端各处代码，无集中定义文件。

### 5.2 工具调用、工具结果、推理在哪

全部塞进消息行的 **`extra`** 对象：

- **工具调用与结果**：【源码】`public/scripts/tool-calling.js` `saveFunctionToolInvocations`——**把一次工具调用造成一条 `is_system: true` 的系统消息**，`mes` 是渲染好的 `<details><summary>Tool calls: …</summary><pre><code class="language-json">…</code></pre></details>` HTML，`extra` 里存结构化数据 `{isSmallSys: true, tool_invocations: invocations, api, model}`；每个 invocation 是 `{id, displayName, name, parameters(JSON string), result, error, signature, reasoning}`。**工具调用与工具结果在同一个 invocation 对象里，调用与结果不分行。**
  https://github.com/SillyTavern/SillyTavern/blob/06bde939fb1e9c4c8d8641d810f0a916b5bce127/public/scripts/tool-calling.js#L898-L917
- **推理原文**：【源码】`public/scripts/reasoning.js` 写到 `message.extra.reasoning`（明文）、`extra.reasoning_duration`、`extra.reasoning_type`（`Model`/`Parsed`/`Edited`/`Manual`）、`extra.reasoning_signature`（"Encrypted signature of the reasoning text"）；swipe 级推理写 `swipeInfoArray[i].extra.reasoning`。**保存推理原文**，并保留 provider 签名以便同模型回放。
  https://github.com/SillyTavern/SillyTavern/blob/06bde939fb1e9c4c8d8641d810f0a916b5bce127/public/scripts/reasoning.js
- **回放时的模型绑定**：【源码】`public/scripts/openai.js` 读 `chat[j]?.extra?.tool_invocations` 与 `chat[j]?.extra?.reasoning_signature` / `extra.reasoning`，且**只在 `isSameModel && !isOtherGroupMember` 时才带入**；API/模型不匹配时删除 invocation 的 `signature`/`reasoning`。
  https://github.com/SillyTavern/SillyTavern/blob/06bde939fb1e9c4c8d8641d810f0a916b5bce127/public/scripts/openai.js#L627-L644

### 5.3 调试一次回答的过程靠什么

- 消息存储本身：`swipes`/`swipe_info` 保存同一问题的多个候选生成与各自的元数据（这是 SillyTavern 独有的"答案版本管理"能力，等价于把重试历史留在消息行内）。
- 另有 `public/scripts/itemized-prompts.js`：把 prompt 按条目拆开存进 IndexedDB（`localforage` instance `SillyTavern_Prompts`，key 是 chatId），**与聊天文件分离**；`public/scripts/PromptManager.js` 提供查看/编辑。
  https://github.com/SillyTavern/SillyTavern/blob/06bde939fb1e9c4c8d8641d810f0a916b5bce127/public/scripts/itemized-prompts.js
- 服务端只做文件读写 + 节流备份（`getBackupFunction`），无独立 trace 表。

### 5.4 迁移史与问题

- 【文档】格式演进主要体现在读路径的宽容度：`getChatData` 逐行 `tryParse` + 丢弃坏行；header 校验失败时降级为"degraded preview"而非报错；importers 反复做格式适配（Chub 的 `swipes` 需 `flattenSwipe`、CAI 的 `msg.src.is_human`、Agnai 的 `!!message.userId`）。**没有集中式 schema 迁移机制，靠"读时兼容"吸收历史。**
- 【源码】`/tmp` 检索确认仓库内**没有** chat 格式迁移脚本目录（`grep -iE "migrat"` 只命中 `migrateInstructPrompt.html`）。
- 查不到：SillyTavern 官方没有发布过聊天格式变更导致的用户数据丢失 issue（搜索 `repo:SillyTavern/SillyTavern chat format jsonl migration` 仅得一条不相关的 swipes PR #4573）。
  https://github.com/SillyTavern/SillyTavern/pull/4573

---

## 6. AI companion 商业产品（Character.ai、Replika、Kindroid、Nomi 等）

**结论：未公开。** 逐一检索（2026-10-24）均未找到这些公司公开的消息存储设计、数据库 schema 或相关工程博客：

- Character.ai：官方博客 `blog.character.ai` 首页 5 篇最新文章分别是破产/出售更新、PipSqueak 3 模型发布、娱乐与粉丝内容形态、角色图像模型 post-training、创作者访谈；**没有任何一篇涉及数据存储、数据库、聊天历史或消息 schema**（第 1 页，共 15 页）。
  https://blog.character.ai/
- Replika：只检索到官方隐私政策（说明对话数据会共享给第三方 provider，无架构细节）。未找到 Luka/Replika 的公开工程博客覆盖对话存储设计。
  https://replika.ai/legal/privacy
- Kindroid / Nomi：检索仅得学术论文（AI & SOCIETY 的 companion AI 影响研究，把这些产品列为流行应用）、市场分析文章与第三方盘点，**没有任何一手工程材料**。
  https://link.springer.com/article/10.1007/s00146-025-02318-6
- 补充：多轮搜索"engineering blog / message storage / database schema / infrastructure"组合均只返回部署教程、竞品分析、成本估算类二手内容。

【推断】这些公司对消息存储不做公开披露，与"对话内容是核心资产 + 未成年人保护/诉讼风险（Character.ai 的诉讼与破产程序）"一致。对 SayHear 而言，这一档**没有可借鉴的公开证据**，只能参考上面的开源产品。

---

## 7. 对比表

| 项目 | 粒度 | 工具调用位置 | 推理位置 | 调试依据 | 迁移或问题 |
| --- | --- | --- | --- | --- | --- |
| LibreChat | 一条消息一行；`content` Mixed 数组 + `text` 列 | `content[].tool_call`（调用与结果同一 part；MongoDB positional 定点回写 `tool_call.output`） | `content[].think`（存原文）；另有 `reasoningOverride` 记档位 | 消息 parts 本身 + Langfuse 字段挂在行上 + subagent 投影 JSON | content parts 化是 breaking 迁移（PR #8171）；MongoDB 16MB 文档上限（PR #14157）；reasoning 渲染/导出/TTS 反复出 bug（#14102、#16674、#13541） |
| Open WebUI | 整段会话一个 JSON blob（`chat.chat`）+ `chat_message` 行级镜像（双写） | 消息 `output[]` 的 `function_call` / `function_call_output` item | 消息 `output[]` 的 `reasoning` item（存原文 + `reasoning_details`，按模型绑定回放） | `output` 保序 + `status_history`/`usage`/`context_summary`；OTel traces/metrics 独立 | 结构性问题 2024 即有人提（#3620）；2025 的拆表提议当天被 not planned（#11467）；2026 加镜像表后迁移 OOM/失败多次（#23134、#23273、PR #24059、#22588）；双写无行锁丢消息（#28742）、时间戳被覆盖（#29501）、统计损坏（#23152）；blob 读路径 OOM（#23192）、JSON 搜索不可索引（#27221）、长对话分页未做（#27187）；读路径切镜像表的 PR 未合并（#23159） |
| LobeChat | 一条消息一行；`content` text 列 + `reasoning`/`tools`/`search`/`usage`/`error`/`metadata` jsonb 列 | `messages.tools` jsonb 数组（调用与结果同一元素）；插件状态走一对一 `message_plugins` 伴随行；`role='tool'` 结果行作内联子节点 | `messages.reasoning` jsonb（存原文 + `responseItems` 原样 provider item + `signature`） | 行上 `traceId`/`observationId` 指向外部可观测系统，过程数据不入库 | `0014_add_message_reasoning.sql` 纯增列零回填；`usage` 从 `metadata.usage` 提列 + 读时回退；未找到用户级数据迁移事故或社区抱怨 |
| Vercel chatbot | 一条消息一行；`parts` json notNull + `attachments` json notNull | `parts[]` 的 tool 调用与 tool result part | `parts[]` 的 `reasoning` part（`part.reasoning`） | 消息 parts 本身 | `Message`/`content` → `Message_v2`/`parts` 的显式迁移（PR #868 + `docs/04-migrate-to-parts.md` + 回填脚本，按 chat 分批）；PR #1168 的 reasoning schema 改动当天被 revert |
| SillyTavern | 整段会话一个 `.jsonl` 文件，一行一消息 | `extra.tool_invocations`（调用与结果同一对象），并落成一条 `is_system` 系统消息，`mes` 是渲染好的 HTML | `extra.reasoning`（存原文）+ `reasoning_signature` + `reasoning_duration`；swipe 级在 `swipe_info[i].extra` | `swipes`/`swipe_info` 保存多候选生成；PromptManager/IndexedDB 的 itemized prompts 与聊天文件分离 | 无集中迁移机制，靠读时兼容（逐行 `tryParse`、坏行丢弃、header 失败降级 preview）；查不到格式变更致数据丢失的 issue |
| Character.ai / Replika / Kindroid / Nomi | 未公开 | 未公开 | 未公开 | 未公开 | 未公开 |

---

## 8. 对 SayHear 的两个直接观察（非证据，标注为【推断】）

1. **候选 A 的"工具调用/工具结果/推理各自成行 + kind 列"在开源产品里没有对应实现**；最接近的是 LobeChat 的 `role='tool'` 独立行（但语义是内联子节点，查询时显式排除）和 OpenAI Agents SDK Session 的"item 一行"（见同目录 frameworks 证据文件）。选 A 意味着自建一套行业不存在的形状，验证成本与后续对接 AI SDK 工具都要自己写。
2. **候选 B 的 parts jsonb 是主流形状**，且五家里四家（LibreChat、LobeChat、Vercel、SillyTavern）都把推理原文与工具结果放进消息行内。共同教训是：**jsonb/json 列本身不是问题，"一份真相 + 一份镜像双写"和"无 schema 校验的 Mixed 数组"才是**（Open WebUI 的 #28742/#23192/#27221、LibreChat 的 #14102/#16674 都源于这两点）。ADR 0010 已要求每表直接带 `owner_id` + 组合外键，若选 B，需要额外明确：(a) 单行 jsonb 更新是否足够承载工具结果的增量回写；(b) `reasoning` 是否要与 provider 绑定（LibreChat 的 `reasoningOverride`、LobeChat 的 `responseItems`/`signature`、Open WebUI 的 `strip_reasoning_details`、SillyTavern 的 `isSameModel` 都是同一问题的四种答案）；(c) run/attempt/输入快照若独立成表，与消息行的 `traceId` 式引用（LobeChat 做法）相比，哪种更符合 ADR 0010 的"一个 run 至多一条 assistant 消息"来源链。
