# 旧仓库 SayHear 聊天相关表结构证据（只读调研）

来源仓库：`/Users/lukemyself/Projects/SayHear`
来源 commit：`cce52bb107c35e7b8998f0dd2dd29632ea5b2591`（committer date 2026-10-18 23:27:58 +0000，"Merge pull request #402 from lukemyself-hub/agent/issue-386"）
调研日期：2026-10-24
迁移目录：`packages/data/migrations/`，共 84 个 `.sql` 文件；编号有重复（0005、0009、0019、0027、0044、0046、0049、0050 各有两个文件），迁移顺序靠文件名而非编号唯一性。

性质：旧仓库结论只是证据，不是 v2 决定。v2 契约见 ADR 0005、0006、0008、0010。本文区分「事实」（读到的代码/SQL/文档原文）与「推断」（我的判断）。

---

## 0. 一张对照表：v2 五类记录 → 旧仓库物理表

| v2 记录（ADR 0010） | 旧仓库表 | 定义位置 |
| --- | --- | --- |
| 连续会话 | `daily_sessions`（旧仓库是「按本地日期的会话」，不是连续单会话） | `packages/data/migrations/0002_user_text_conversation.sql:1-26` |
| 消息（用户/assistant/system/工具） | `conversation_events`（信封）+ `conversation_event_revisions`（正文） | `0002_user_text_conversation.sql:52-123` |
| — 额外：一次回答的多条 lineage | `conversation_event_generation_command_links` | `0052_proactive_followup_segment.sql:18-36` |
| 轮次 | `interaction_turns` | `0002_user_text_conversation.sql:28-50` |
| run | `generation_commands` | `0003_complete_assistant_response.sql:1-43` |
| attempt | `model_run_attempts` | `0003_complete_assistant_response.sql:45-92` |
| — 额外：Provider 出站处置 | `provider_egress_dispositions` | `0003_complete_assistant_response.sql:131-161` |
| 输入快照 | `compiled_contexts` + `compiled_context_revision_refs` | `0003_complete_assistant_response.sql:94-129` |

**事实**：旧仓库没有 `messages` 单表；一条消息拆成「事件信封 + 版本正文」两表，且事件行本身不带正文（`0002_user_text_conversation.sql:52-79` 中无正文列，正文只在 `0002:91` 的 `canonical_text`）。旧仓库也没有「一个持久 AgentRun wrapper」；`docs/architecture/07-01-06-conversation-data-model.md:376-378` 明确说 InteractionTurn 已承担父级，不再增加持久 wrapper。

**推断**：v2 的五类记录可以在旧仓库找到逐项对应，但旧仓库的每类都比 v2 阶段 1 需要多一到两张表；对照时要按「v2 需要什么」裁剪，而不是照搬表数。

---

## 1. 逐表：列、类型、约束、索引

### 1.1 `daily_sessions`（会话）

定义 `packages/data/migrations/0002_user_text_conversation.sql:1-22`：

| 列 | 类型 | 约束 |
| --- | --- | --- |
| `daily_session_id` | UUID | PK（`:2`） |
| `user_id` | UUID | NOT NULL，FK → `app_users`（`:3`） |
| `logical_date` | DATE | NOT NULL（`:4`） |
| `timezone_at_start` | TEXT | NOT NULL（`:5`） |
| `started_at` / `last_activity_at` | TIMESTAMPTZ | NOT NULL（`:6-7`） |
| `activity_state` | TEXT | NOT NULL DEFAULT `'active'`，CHECK `active/quiescent/finalized`（`:8-9`） |
| `current_continuous_exchange_no` | INTEGER | NOT NULL DEFAULT 1，CHECK > 0（`:10-11`） |
| `dialogue_revision` / `source_revision` | BIGINT | NOT NULL DEFAULT 0，CHECK >= 0（`:12-13`） |
| `next_turn_sequence_no` / `next_event_sequence_no` | BIGINT | NOT NULL DEFAULT 1，CHECK > 0（`:14-17`） |
| `created_at` / `updated_at` | TIMESTAMPTZ | NOT NULL，**无 DEFAULT**（`:18-19`） |

约束与索引（事实）：
- `UNIQUE (user_id, logical_date)`：每人每天一个会话（`:20`）。
- `UNIQUE (daily_session_id, user_id)`：供子表复合外键引用（`:21`）。
- 部分唯一索引 `daily_sessions_one_active_per_user_idx ON daily_sessions(user_id) WHERE activity_state='active'`：每用户最多一个活跃会话（`:24-26`）。
- 后续加列：`quiescent_at`、`quiescent_reason`（CHECK `explicit_user_end/inactivity_timeout`）在 `0005_continuous_exchange_end.sql:1-6`；`closure_policy_version` 外键到不可变策略表在 `0005_continuous_exchange_end.sql:40-43`。
- `logical_date` 与 `timezone_at_start` 由触发器强制不可变（`0005_continuous_exchange_end.sql:109-129`）。

**推断**：v2 采用连续会话（ADR 0008），旧仓库的「按本地日期唯一」正好是 v2 明确不选的方案；可借用的只有「时间字段用 TIMESTAMPTZ、本地日期另存 DATE、时区不可变」这组做法，而不是它的唯一键。

### 1.2 `interaction_turns`（轮次）

定义 `0002_user_text_conversation.sql:28-50`：

| 列 | 类型 | 约束 |
| --- | --- | --- |
| `interaction_turn_id` | UUID | PK（`:29`） |
| `user_id` | UUID | NOT NULL，FK → `app_users`（`:30`） |
| `daily_session_id` | UUID | NOT NULL（`:31`） |
| `client_turn_id` | TEXT | NOT NULL（`:32`） |
| `turn_sequence_no` | BIGINT | NOT NULL，CHECK > 0（`:33`） |
| `continuous_exchange_no` | INTEGER | NOT NULL，CHECK > 0（`:34`） |
| `status` | TEXT | NOT NULL，CHECK `open/responding/settled/interrupted/failed`（`:35-36`） |
| `retry_of_interaction_turn_id` | UUID | 可空，自引用（`:37`） |
| `started_at` | TIMESTAMPTZ | NOT NULL（`:38`） |
| `settled_at` | TIMESTAMPTZ | 可空（`:39`） |
| `created_at` / `updated_at` | TIMESTAMPTZ | NOT NULL，无 DEFAULT（`:40-41`） |

约束（事实）：`UNIQUE (user_id, client_turn_id)`（幂等键，`:42`）、`UNIQUE (daily_session_id, turn_sequence_no)`（`:43`）、`UNIQUE (interaction_turn_id, user_id)` 与三列唯一键供更深引用（`:44-45`）、`FOREIGN KEY (daily_session_id, user_id)`（`:46-47`）、`FOREIGN KEY (retry_of_interaction_turn_id, user_id)`（`:48-49`）。**除上述唯一约束自带的索引外没有额外索引**。

注意：`docs/architecture/07-01-06-conversation-data-model.md:151` 列了 `deleted_at`，但迁移里**没有**该列（grep 未命中）——文档与实现漂移，见 §5。

### 1.3 `conversation_events`（消息信封）

定义 `0002_user_text_conversation.sql:52-79`：

| 列 | 类型 | 约束 |
| --- | --- | --- |
| `conversation_event_id` | UUID | PK（`:53`） |
| `user_id` | UUID | NOT NULL，FK → `app_users`（`:54`） |
| `daily_session_id` | UUID | NOT NULL（`:55`） |
| `interaction_turn_id` | UUID | NOT NULL（`:56`） |
| `sequence_no` | BIGINT | NOT NULL，CHECK > 0（`:57`） |
| `client_event_id` | TEXT | NOT NULL（`:58`） |
| `actor` | TEXT | NOT NULL，CHECK `user/assistant/system`（`:59`） |
| `channel` | TEXT | NOT NULL，CHECK `text/realtime`（`:60`） |
| `event_type` | TEXT | NOT NULL，**无 CHECK**（`:61`） |
| `current_revision_id` | UUID | 可空（`:62`） |
| `lifecycle_status` | TEXT | NOT NULL，CHECK `active/superseded/deleted`（`:63-64`） |
| `created_at` | TIMESTAMPTZ | NOT NULL，无 DEFAULT（`:65`） |
| `deleted_at` | TIMESTAMPTZ | 可空（`:66`） |

后续加列：`generation_command_id UUID`（仅 assistant 行使用，`0003_complete_assistant_response.sql:163-169`）。

约束与索引（事实）：
- `UNIQUE (user_id, client_event_id)`：客户端重发幂等（`0002:67`）。
- `UNIQUE (daily_session_id, sequence_no)`：会话内顺序（`0002:68`）。
- `UNIQUE (conversation_event_id, user_id)` 供子表/命令引用（`0002:69`）。
- 复合 FK `(daily_session_id, user_id)`（`0002:70-71`）与 `(interaction_turn_id, daily_session_id, user_id)`（`0002:72-78`）。
- 部分唯一索引：每个 turn 只允许一条用户事件，`WHERE actor='user'`（`0002:81-83`）。
- 部分唯一索引：`current_revision_id` 全局唯一（`0002:121-123`）。
- 部分唯一索引：每个 `generation_command_id` 只允许一条 assistant 事件，`WHERE actor='assistant'`（`0003_complete_assistant_response.sql:171-173`）——**这就是「一个 run 至多一条 assistant 消息」的数据库强制**。
- 后续为近期上下文扫描加的 `(user_id, created_at)` 索引：`0069_recent_context_request_timezone.sql:16-17`。

**事实**：`actor` 允许 `system`，但代码里没有任何 `INSERT ... actor='system'`（grep `packages/data/src` 无命中）；`channel` 允许 `realtime`，但迁移里没有 voice 表（grep 无命中）。**推断**：这两个枚举值为未实现渠道预留，属「先占位后不用」的成本。

### 1.4 `conversation_event_revisions`（正文版本）

定义 `0002_user_text_conversation.sql:85-106`：

| 列 | 类型 | 约束 |
| --- | --- | --- |
| `conversation_event_revision_id` | UUID | PK（`:86`） |
| `user_id` | UUID | NOT NULL，FK → `app_users`（`:87`） |
| `conversation_event_id` | UUID | NOT NULL（`:88`） |
| `revision` | INTEGER | NOT NULL，CHECK > 0（`:89`） |
| `locale` | TEXT | NOT NULL，**无 CHECK**（`:90`） |
| `canonical_text` | TEXT | NOT NULL（`:91`） |
| `transcript_status` | TEXT | NOT NULL，CHECK `final/corrected`（`:92-93`） |
| `created_by` | TEXT | NOT NULL，CHECK `client/user_correction`（`:94`；`0003:175-180` 扩为含 `provider`） |
| `created_at` | TIMESTAMPTZ | NOT NULL（`:95`） |
| `content_purged_at` | TIMESTAMPTZ | 可空（`:96`） |

约束与索引（事实）：
- `UNIQUE (conversation_event_id, revision)`（`:97`）、`UNIQUE (conversation_event_revision_id, user_id)` 与三列唯一键（`:98-103`）。
- FK `(conversation_event_id, user_id)`（`:104-105`）。
- 不可变触发器：只允许一种 UPDATE——把 `content_purged_at` 从 NULL 置非 NULL 且 `canonical_text=''`，其余字段不变；DELETE 一律拒绝（`:125-155`）。
- 无独立索引；只有唯一约束索引。

**注意**：`0003_complete_assistant_response.sql:163-169` 之后，`conversation_events.current_revision_id` 通过复合 FK 指向该表（`0002:108-119`）。

### 1.5 `conversation_event_generation_command_links`（回答 lineage）

`0052_proactive_followup_segment.sql:18-36`：`(conversation_event_id, generation_command_id, user_id, role, created_at)`，PK `(conversation_event_id, role)`（`:28`），`UNIQUE (generation_command_id, user_id)`（`:29`），`role` CHECK `main_response/proactive_segment/action_finalization`（`:23-25`），两条复合 FK（`:30-33`），索引 `(user_id, conversation_event_id)`（`:34-35`）。**事实**：该表不存正文，只存 lineage。

### 1.6 `generation_commands`（run）

初始定义 `0003_complete_assistant_response.sql:1-43`，核心列：

| 列 | 类型 | 约束 |
| --- | --- | --- |
| `generation_command_id` | UUID | PK（`:2`） |
| `user_id` | UUID | NOT NULL，FK → `app_users`（`:3`） |
| `interaction_turn_id` | UUID | NOT NULL（`:4`，后于 `0044:145-148` 改为可空以容纳非对话角色） |
| `operation_type` | TEXT | NOT NULL，CHECK `='conversation.text'`（`:5`） |
| `intent_key` | TEXT | NOT NULL（幂等键，`:6`） |
| `subject_type` / `subject_id` | TEXT / UUID | NOT NULL，`subject_type` CHECK `='conversation_event'`（`:7-8`） |
| `input_revision_kind` / `input_revision_id` | TEXT / UUID | NOT NULL（`:9-11`） |
| `prompt_version` | TEXT | NOT NULL（`:12`） |
| `product_policy_version` / `safety_policy_version` / `relationship_policy_version` / `locale_policy_version` | TEXT | NOT NULL（`:13-16`） |
| `locale` | TEXT | NOT NULL（`:17`） |
| `provider` / `model` / `model_snapshot` / `model_config_version` | TEXT | NOT NULL（`:18-21`） |
| `freshness_policy` | TEXT | NOT NULL，CHECK `='source_valid:v1'`（`:22`） |
| `expected_data_epoch` | BIGINT | NOT NULL，CHECK > 0（`:23`） |
| `status` | TEXT | NOT NULL，CHECK `prepared/running/succeeded/failed/interrupted`（`:24-25`） |
| `compiled_context_id` / `authoritative_result_id` | UUID | 可空（`:26-27`） |
| `created_at` / `settled_at` | TIMESTAMPTZ | NOT NULL / 可空（`:28-29`） |

约束（事实）：`UNIQUE (user_id, intent_key)`（幂等，`:30`）、`UNIQUE (interaction_turn_id)`（一个 turn 一条命令，`:31`，后于 `0021_allow_action_finalization_per_turn.sql:4-9` 删除并替换为 `WHERE generation_stage='decision'` 的部分唯一索引）、`UNIQUE (generation_command_id, user_id)`（`:32`），FK `(interaction_turn_id, user_id)`（`:33-34`）、`(subject_id, user_id)` → events（`:35-36`）、`(input_revision_id, subject_id, user_id)` → revisions（`:37-42`）。

后续 15 个迁移改过这张表（事实，按文件顺序）：
- `0004:1-15` status 加 `compiling`。
- `0005_provider_egress_policy.sql:43-56` `provider_policy_version`（FK 到策略表）、`consent_policy_version`。
- `0006_compiled_context_manifest.sql:1-14` `output_format_version`、`persona_version`（先加可空、回填、再 NOT NULL）。
- `0007_text_response_recovery.sql:49-65` `recovery_policy_version`、`recovery_status`（6 值 CHECK）、`recovery_checked_at`、`next_recovery_at`；`:102-117` status 再加 `retry_pending`。
- `0009_conversation_decision_command_harness.sql:13-24` `harness_policy_version`、`conversation_action_catalog_version`。
- `0020:4-6` `generation_stage`（CHECK 2 值）+ `action_execution_id`。
- `0027:12-21` persona 版本列。
- `0044:134-143` `model_role`、`schema_version`、`role_policy_version`、`rollout_pin`、`source_revision`、`source_snapshot`、`input_manifest JSONB`、`parameter_snapshot JSONB`、`fallback_mode`；`0044:145-148` 三列改可空；`:158-200` 多个 CHECK 重写。
- `0052:9-16` `generation_stage` 加 `proactive_followup`。
- `0069:9-10` `request_timezone`。
- `0071:5-6` `generation_stage` 加 `history_answer`。
- `0080:14-15` `request_deadline_at`、`latest_input_fence_version`。

**事实**：最终 55 列（`packages/application/src/purge-surface-registry.ts:1591` 的列清单），共 37 处 `ALTER TABLE generation_commands`（grep 计数）。

### 1.7 `model_run_attempts`（attempt）

初始定义 `0003_complete_assistant_response.sql:45-92`：

| 列 | 类型 | 约束 |
| --- | --- | --- |
| `model_run_attempt_id` | UUID | PK（`:46`） |
| `user_id` | UUID | NOT NULL，FK → `app_users`（`:47`） |
| `generation_command_id` | UUID | NOT NULL（`:48`） |
| `attempt_no` | INTEGER | NOT NULL，CHECK > 0（`:49`） |
| `operation_type` | TEXT | NOT NULL，CHECK `='conversation.text'`（`:50`） |
| `provider` / `model` / `model_snapshot` / `prompt_version` | TEXT | NOT NULL（`:51-54`） |
| `status` | TEXT | NOT NULL，CHECK `prepared/running/succeeded/failed/interrupted/result_unknown`（`:55-65`） |
| `provider_request_id` | TEXT | 可空（`:66`） |
| `started_at` / `first_token_at` / `completed_at` | TIMESTAMPTZ | 可空（`:67-69`） |
| `input_tokens` / `output_tokens` / `cost_micros` | BIGINT | CHECK >= 0（`:70-72`） |
| `finish_reason` | TEXT | 可空（`:73`） |
| `error_category` | TEXT | CHECK 8 值（`:74-86`） |
| `created_at` | TIMESTAMPTZ | NOT NULL（`:87`） |

约束（事实）：`UNIQUE (generation_command_id, attempt_no)`（`:88`）、`UNIQUE (model_run_attempt_id, user_id)`（`:89`）、FK `(generation_command_id, user_id)`（`:90-91`）。

后续：`0007:75-92` `retry_of_model_run_attempt_id`（自引用）、`recovery_status`（7 值）、`retry_not_before`、`recovery_claimed_at`、`provider_completed_at`；`0007:119-136` error_category 加 `configuration`；`0007:161-163` 部分索引 `(created_at, started_at) WHERE status IN ('prepared','running','result_unknown')`；`0044:238-241` `attempt_kind`、`source_attempt_id`、`provider_egress_event_id`、`error_code`；`0044:244-265` status 加 `discarded`，`attempt_kind` CHECK `initial/technical_retry/schema_repair`；`0063:11-22` `reasoning_tokens`、`cached_tokens`、`total_tokens`。

**事实**：最终 32 列（`purge-surface-registry.ts:1620`）。

### 1.8 `compiled_contexts`（输入快照）

定义 `0003_complete_assistant_response.sql:94-111`：

| 列 | 类型 | 约束 |
| --- | --- | --- |
| `compiled_context_id` | UUID | PK（`:95`） |
| `user_id` | UUID | NOT NULL，FK → `app_users`（`:96`） |
| `generation_command_id` | UUID | NOT NULL（`:97`） |
| `compiler_version` | TEXT | NOT NULL（`:98`） |
| `dialogue_revision` / `source_revision` | BIGINT | NOT NULL，CHECK >= 0（`:99-100`） |
| `locale` | TEXT | NOT NULL（`:101`） |
| `section_budgets` | JSONB | NOT NULL（`:102`） |
| `total_tokens` | BIGINT | NOT NULL，CHECK >= 0（`:103`） |
| `degraded_reason` | TEXT | 可空，初始 CHECK `='raw_event_budget_exceeded'`（`:104`） |
| `content_hmac` | TEXT | NOT NULL（`:105`） |
| `created_at` | TIMESTAMPTZ | NOT NULL（`:106`） |

约束（事实）：`UNIQUE (generation_command_id)`（`:107`，**一个 run 一份快照**）、`UNIQUE (compiled_context_id, user_id)`（`:108`）、FK `(generation_command_id, user_id)`（`:109-110`）。

后续：`0006_compiled_context_manifest.sql:16-71` 加 `policy_versions JSONB`、`sections JSONB`、`integrity_algorithm`、`integrity_key_version`，并把旧行回填成 `sections` 数组；`:61-71` 加 `jsonb_typeof` CHECK；`0015:100-104` 加 `rolling_summary JSONB`；`0034:272-282`、`0037:306-317` 多次重写 `degraded_reason` CHECK；`0037:299-301` 加 `retrieval_manifest JSONB`。最终 18 列（`purge-surface-registry.ts:1529`）。

**关键事实**：快照里**不存发给模型的正文**。`sections` 的每个元素只有 `{budgetTokens, contentHmac, key, ordinal, reference, selectedTokens, truncatable}`（`packages/application/src/context-compiler.ts:307-315`）；正文由 `compiled_context_revision_refs` 指向的 revision 重读。`reference` 是版本号或编码后的选择元数据（`context-compiler.ts:2436-2604`），recent/history 的 reference 含查询线索（ADR 0131 `docs/adr/0131-every-private-data-surface-registers-its-purge-contract.md:12-20`）。

### 1.9 `compiled_context_revision_refs`（快照引用了哪些 revision）

定义 `0003_complete_assistant_response.sql:113-129`：`compiled_context_id`、`user_id`、`conversation_event_revision_id`、`ordinal`、`actor`、`estimated_tokens`；PK `(compiled_context_id, ordinal)`（`:120`），`UNIQUE (compiled_context_id, conversation_event_revision_id)`（`:121`），两条复合 FK（`:122-128`）。`0006:73-143` 加 `sequence_no`、`section`、`selection_order` 及互斥 CHECK；`0068:7-118` 加 `daily_session_id`、`expressed_at`、`occurred_at`、`selection_reason`，并加触发器校验 revision 确实属于该 session（`:31-60`）。

### 1.10 `provider_egress_dispositions`

`0003:131-161`：每 attempt 一条（`UNIQUE (model_run_attempt_id)`，`:158`），记录 `provider`、`model`、`role`、`provider_policy_version`、`expected_data_epoch`、`status`（`blocked/dispatched/completed/failed`）、`error_category`、`checked_at`、`dispatched_at`、`completed_at`；`0005_provider_egress_policy.sql:62-65` 加策略外键；`0007:138-155` 扩 error_category。

**推断**：v2 阶段 1 若不承诺「出站前策略/同意检查」，这张表可以完全不要；它存在是因为旧仓库要证明「哪些内容发给了哪个 Provider」。

---

## 2. 消息正文如何存

**事实**：
- 正文是**纯文本 `TEXT`**，一列 `canonical_text`（`0002_user_text_conversation.sql:91`），不是结构化 JSON。结构化只出现在快照/策略元数据的 JSONB 列上（`compiled_contexts.sections`、`policy_versions`、`rolling_summary`、`retrieval_manifest`，见 §1.8）。
- 消息信封与正文分离：`conversation_events` 只存 `actor/channel/event_type/lifecycle_status/sequence_no`，正文在 revision 行（`0002:52-106`）。
- 写入路径：用户消息先插 event 再插 revision `revision=1`，然后 CAS 设置 `current_revision_id`（`packages/data/src/postgres-user-text-conversation-repository.ts:1471-1533`）；assistant 回答在提交事务里插 event + revision `revision=1`、`created_by='provider'`（`packages/data/src/postgres-conversation-response-repository.ts:2336-2404`）。
- 用户更正：追加 `revision+1`，`transcript_status='corrected'`、`created_by='user_correction'`，再 CAS 指针（`postgres-user-text-conversation-repository.ts:130-143`）；旧 revision 正文不改（不可变触发器 `0002:125-155`）。
- `locale` 是纯 TEXT 且无 CHECK（`0002:90`），与知识域其它表的 `CHECK (locale IN ('zh','en'))` 不同（如 `0032_predicate_registry_v1.sql:47`）。

**部分回答 / 中断**（事实）：
- 旧仓库**不持久化部分正文**。模型调用前先落 User Event、Turn、Command、Attempt（`docs/architecture/07-01-06-conversation-data-model.md:348-349`）；流式 token 只 best-effort 给客户端，不写 chunk 表（`:350-351`）；完整成功才在一个事务里创建 Assistant Event/Revision（`:352-353`）；中断只把 Turn/Attempt 标 `interrupted`，**不创建 Assistant Event**（`:354-355`）。
- 代码印证：`settleResponseFailureOnce` 把 command 置 `interrupted`、attempt 置 `interrupted`/`result_unknown`，不写 revision（`postgres-conversation-response-repository.ts:2782-2830`）；应用层用 `possiblyVisible` 决定中断语义（`packages/application/src/conversation-response.ts:348-358`、`553-560`）。
- 迁移里没有任何 `assistant_delivery_chunks`、`partial`、`delivered_prefix` 表或列（grep 无命中）。ADR 0021 说的 `partially_delivered` 只存在于计划中（`docs/adr/0021-core-flow-1b-splits-transport-from-delivery-precision.md:8-10`），未实现。

**推断**：v2 ADR 0005 要求「保留已显示的部分回答并标注中断」，旧仓库**没有可复用形状**——旧仓库的答案是「中断即无回答」。v2 需要新设计（例如 assistant 行带 `interrupted` 标志 + 部分正文），不能从旧表推导。

**删除状态**（事实）：
- `lifecycle_status` 的 CHECK 允许 `superseded`、`deleted`（`0002:63-64`），`conversation_events.deleted_at` 也存在（`0002:66`），但 `packages/data/src` 里**没有任何写入**这两个值/列的 SQL（grep `SET lifecycle_status`、`event.deleted_at` 均无命中）。
- 旧仓库阶段 1 不提供单条消息删除（ADR 0002 `docs/adr/0002-phase-one-content-deletion-scope.md:5-7`；ADR 0022 `docs/adr/0022-deletion-capability-expands-with-data-surface.md:8-10`）。
- 唯一的内容清除是整账户 Full Purge：revision 被置 `canonical_text=''` + `content_purged_at`（`packages/data/src/postgres-purge-surface-adapters.ts:1047-1052`，注册为 `tombstone_conversation_revisions`，`packages/application/src/purge-surface-registry.ts:315-324`），并由 verifier 校验（`postgres-purge-surface-adapters.ts:1314-1320`）。

**推断**：v2 的「单条删除保留占位并清空原文」在旧仓库只有**部分**可借鉴形状（`lifecycle_status` 值域 + `content_purged_at` + 清空正文），但旧仓库从未真正跑过单条删除路径，v2 的 `deleted_at` 语义（ADR 0010）仍需自己定义。

**排序依据**（事实）：
- 会话内顺序用 `sequence_no`，不是时间戳：从 `daily_sessions.next_event_sequence_no` 取值，在锁住 session 行后递增（`postgres-user-text-conversation-repository.ts:1337`、`1384`、`1440-1441`、`1647-1661`；assistant 提交同样递增 `postgres-conversation-response-repository.ts:2474-2487`）。
- 读取按 `(logical_date, sequence_no)`（`postgres-user-text-conversation-repository.ts:367`、`418`），近期上下文按 `sequence_no DESC` 取再升序返回（`:600`、`:791`）。
- 跨会话/跨日期查询改用 `created_at`：`0069:12-17` 的 `(user_id, created_at)` 索引与 `packages/data/src/postgres-history-recall.ts:183`、`225`、`303` 的 `ORDER BY event.created_at, ...`。

**推断**：旧仓库实际上是「会话内序号 + 跨会话时间戳」双排序。v2 只有单一连续会话，按 ADR 0008 只需要一条主排序；但「日期导航」仍会按时间范围查，所以两个字段都可能需要。

**时区与日期字段**（事实）：
- 聊天相关表的时间列全部 `TIMESTAMPTZ`，没有 `TIMESTAMP WITHOUT TIME ZONE`（grep 无命中）。
- 本地日期另存 `DATE`（`daily_sessions.logical_date`，`0002:4`），由应用用 IANA 时区计算（`packages/application/src/user-text-conversation.ts:806-815` 的 `localDateAt`，`Intl.DateTimeFormat`）。
- 会话开始时区 `timezone_at_start` 不可变（`0005:109-129`）；后来发现旅行场景会读错本地日，于是把**当次请求时区**冻结到 command 上：`0069:1-10` 加 `generation_commands.request_timezone`，注释明说「不能用 session 开始时的时区」。
- 聊天表的 `created_at/updated_at` **没有数据库 DEFAULT**（`0002`、`0003` 中 `DEFAULT CURRENT_TIMESTAMP` 计数为 0），时间由应用 `input.now` 传入；只有治理/策略类表用 `DEFAULT CURRENT_TIMESTAMP`（如 `0001_foundation.sql:5`、`0005:11`）。

**推断**：v2 若沿用 Supabase 默认，可能想用 `now()` DEFAULT；旧仓库刻意让应用时钟成为唯一时间源（可测试、可重放）。这是一个明确的取舍点，不是必然。

---

## 3. ID 类型与生成方式、状态字段形态

**ID（事实）**：
- 全部主键 `UUID`，由**应用服务端生成 UUIDv7**：`packages/data/src/uuid-v7.ts:3-26`（把毫秒时间戳写进前 6 字节，再用 `randomBytes` 填充）。没有 `gen_random_uuid()` 默认值（grep 迁移无 `DEFAULT gen_random_uuid`）。
- 生成点示例：`postgres-user-text-conversation-repository.ts:1435-1439`（turn/event/revision/command/attempt 一次生成）、`postgres-conversation-response-repository.ts:2336-2337`（assistant event + revision）。
- TypeScript 侧用 branded ID：`packages/domain/src/ids.ts:1-40`（`UserId`、`DailySessionId`、`InteractionTurnId`、`ConversationEventId`、`ConversationEventRevisionId`、`GenerationCommandId`、`ModelRunAttemptId`、`CompiledContextId`…）。
- 契约文档：`docs/adr/0085-persistent-ids-are-opaque-and-semantic-ids-are-versioned.md:8-10`；`docs/architecture/07-01-06-conversation-data-model.md:52-68`。
- `node:crypto` 的 `randomUUIDv7` 只用于 purge/CLI 等边缘路径（`packages/data/src/postgres-owner-purge-repository.ts:435-437`、`packages/data/src/cli/record-backup-policy.ts:31`），不是聊天主路径。

**状态字段（事实）**：
- 全部是 `TEXT + CHECK (...)`，迁移里**没有 `CREATE TYPE`**（grep 无命中），没有 Postgres enum。
- 代价可见：每加一个状态值都要 `DROP CONSTRAINT` + `ADD CONSTRAINT`，同一约束被反复重写（`0004:1-15`、`0007:102-117`、`0044:244-265`、`0052:9-16`、`0071:5-6`）。
- 后期甚至为了避免改受保护的 CHECK 而新增列：ADR 0083 明说 `latest_input_fence_version` 做成「无 CHECK 的版本文本列」，因为 `freshness_policy` 的 CHECK 属于 G1 schema 守卫范围（`docs/adr/0083-generation-commands-use-versioned-freshness-policies.md:19-23`；守卫实现见 `packages/application/src/schema-extension.ts:1-33`）。

**推断**：旧仓库选 `TEXT+CHECK` 而不是 enum，迁移期更灵活，但每次扩值仍要改约束；v2 若状态集合在阶段 1 就稳定，`TEXT+CHECK` 足够；若预期频繁扩值，可考虑版本化文本列（旧仓库后期正是这么做的）。

---

## 4. 与字段相关的踩坑与教训（文档/ADR 记录）

### 4.1 revision 表为什么存在（事实）
- `conversation_events` 是稳定信封，不存可修正正文；`conversation_event_revisions` 是 append-only 正文历史（`docs/architecture/07-01-06-conversation-data-model.md:269`、`298-312`）。
- 修正/重转写/用户纠错**追加新 revision**并 CAS `current_revision_id`，旧 revision 不动（`07-01-06:326-330`；代码 `postgres-user-text-conversation-repository.ts:130-143`）。
- 下游（CompiledContext、Evidence、Journal、Reflection、Claim、Replay）必须引用 `conversation_event_revision_id`，不能只引用可变的 Event ID（`07-01-06:331-332`）。ADR 0086 进一步要求 Interaction/Voice/Revision 三种身份不可互相推导（`docs/adr/0086-interaction-voice-and-event-identities-are-distinct.md:8-13`）。
- 首次落地该形状的提交是 `e6bb50d`（"persist idempotent user text turns"，2026-07-27），提交说明把「immutable revisions」「monotonic sequences」「current-revision CAS」「owner-bound FKs」列为设计取舍（`git log -1 e6bb50d`）。

**推断**：revision 表在旧仓库有**真实产品理由**（转写修正、用户纠错、Evidence 精确引用、删除后审计）。v2 阶段 1 若不提供消息编辑/语音转写/证据引用，revision 层可能只为一件事服务：单条删除时保留占位。若如此，v2 用「消息表一行 + 删除时清空正文」即可，不必预先建 revision 表——这是「是否过度结构化」的核心判断点，应由 v2 的删除契约和未来编辑需求决定。

### 4.2 不可变 + 整账户删除会打架（事实）
- revision 不可变触发器（`0002:125-155`）原本连 DELETE 都拒绝；为了 Full Purge，`0019_owner_full_purge.sql:10-13` 引入 `sayhear.purge_pass` 事务标记，并在 `:121-131` 用 `CREATE OR REPLACE FUNCTION` 给证据/日志类触发器开「仅在已验证 purge pass 中允许 DELETE」的例外。
- 为了让 tombstone 在事件被硬删后仍留存，`0019:266-287` **主动删除了 `conversation_event_revisions → conversation_events` 的外键**，注释说明这是有意为之（tombstone 证明删除并阻止旧任务复活）。

**推断**：v2 ADR 0010 选择「对 auth.users 级联删除」而不是 tombstone，已经绕开了这个坑；但若以后要「删除后保留无正文 lineage」，就会重新遇到同一冲突——不可变约束与级联删除不能同时成立。

### 4.3 输入快照的粒度：按 run，不按 attempt（事实）
- `compiled_contexts` 对 `generation_command_id` 唯一（`0003:107`），一个 run 只有一份快照。
- 技术重试复用同一 command，读取时若 `compiled_context_id` 已存在就直接返回旧快照（`postgres-conversation-response-repository.ts:1393-1398`）；重试只新增 attempt（`:704-738`）。
- 旧仓库从未实现 fallback：`generation_commands.fallback_mode` 的 CHECK 恒为 `'disabled'`（`0044:191-192`），没有 `continuous_exchange_model_bindings` 表（grep 迁移无命中），`attempt_kind` 只有 `initial/technical_retry/schema_repair`（`0044:264-265`）。fallback 只存在于 ADR 与架构文档（`docs/adr/0059-text-fallback-handover-precedes-visible-output.md:8-16`；`07-01-06:359-366`）。

**推断**：v2 契约要求「输入快照 → attempt，每次实际发送一份」（ADR 0010）。旧仓库给不出这个形状的证据，只给出反面：按 run 存快照会让 fallback 的第二次发送与第一次共用同一份记录，无法区分实际发给了哪个 Provider。v2 若要按 attempt 存，属于**新设计**，旧仓库不能当先例引用。

### 4.4 文档领先于 schema，别把文档当实现（事实）
架构文档列了但迁移里不存在的字段/表：`conversation_events.correlation_id`、`daily_sessions.deleted_at`、`interaction_turns.deleted_at`、`conversation_event_revisions.based_on_revision_id`/`supersedes_revision_id`、`daily_sessions.journal_id`、`voice_sessions`/`voice_turns`/`transcript_segments`（分别见 `07-01-06:271-312`、`151`、`214-247`；grep 迁移均无命中）。另外文档说 `sections` 保存「发给模型的完整正文」（ADR 0131 `:18-20`），代码里 `sections` 只有引用与 HMAC（`context-compiler.ts:307-315`），正文在被引用的 revision 行。

**推断**：引用旧仓库时必须以迁移 + 代码为准，文档只能说明意图。v2 调研若直接引用架构文档，会把未实现的设计当成已踩过的坑。

### 4.5 表结构随功能线性膨胀（事实）
- 84 个迁移、编号重复 8 组；`generation_commands` 55 列、被 37 处 ALTER；`model_run_attempts` 32 列、9 处 ALTER；`compiled_contexts` 18 列，`degraded_reason` CHECK 被重写 4 次以上（`0003:104`、`0015:101-104`、`0034:272-282`、`0037:306-317`、`0016:132-137`）。
- 迁移 `0023_preserve_journal_regeneration_workflow_types.sql:1-5` 是「修复已被记录的旧迁移」的前向修补，说明共享 CHECK 被某次迁移重写后遗漏了值。
- 旧仓库自己的复盘把「有些复杂度保护用户，有些只是没有证据的设计假设」列为教训（`docs/research/2026-10-20-harness-memory-retrospective.md:83-91`）。

**推断**：v2 ADR 0005 明确要求运行记录「初期只保存定位问题所需的少量字段，避免过度结构化」（`docs/adr/0005-chat-experience-and-run-record.md:12`），这条正是对旧仓库 `generation_commands`/`compiled_contexts` 膨胀的回应；阶段 1 若照搬 55 列的命令表，会直接违反 v2 自己的契约。

---

## 5. 对 v2 表结构讨论的直接提示（推断，非决定）

1. **消息表可以更简单**：旧仓库的「信封 + revision」两表是因为要支持编辑/转写/证据引用；v2 阶段 1 若无这些需求，一张 `messages`（role、正文、`generation_run_id` 可空、删除时间、删除后正文清空）可能就够，且更贴合 ADR 0010 的「消息 → 会话」「assistant 消息 → run」两条引用。
2. **排序用序号更稳**：旧仓库在会话内用 `sequence_no`（锁行分配）而不是时间戳，避免同一毫秒并列；v2 单会话可以用单调序号 + `created_at` 并存（时间用于日期导航）。
3. **时区按请求冻结**：旧仓库的教训是「会话开始时的时区不足以判断当次本地日期」（`0069:1-10`），v2 若记录日期就必须在写入时冻结请求时区或本地日期，而不是事后用服务器时区推算。
4. **状态字段用 TEXT+CHECK**：旧仓库没有 enum；但每扩一个值要改约束。阶段 1 应一次把状态集合定准，或采用「无 CHECK 的版本化文本列」避免约束迁移。
5. **快照粒度要显式决定**：旧仓库按 run 存快照，导致 fallback 无法区分每次实际发送；v2 ADR 0010 已定为按 attempt，这是一次有意的偏离，不要以旧仓库为反例。
6. **删除语义先定，再定不可变**：旧仓库先做不可变 revision，后为整账户删除加 purge pass 例外并拆外键。v2 若采用级联删除 + 单条删除占位，应一开始就让「不可变」与「删除」兼容，避免二次迁移。

---

## 6. 未解问题（需要旧仓库之外的信息）

- 旧仓库为什么把 `event_type` 留成无 CHECK 的 TEXT？只在代码里看到 `'message'` 与 `'retry_action'` 两个值（`postgres-user-text-conversation-repository.ts:1064`、`1484`；`postgres-conversation-response-repository.ts:2355`）。是否有第三个值在别处写入，需要查旧仓库 CI/评测脚本才能确认。
- `lifecycle_status` 的 `superseded`/`deleted` 与 `deleted_at` 是纯预留还是曾经实现后被移除？`git log -S "lifecycle_status"` 可定位；本次未做历史追查。
- 旧仓库是否有「单条消息删除」的产品讨论被否决的记录？现有 ADR 0002/0022 只说「阶段 1 不提供」，未给出原因细节。
