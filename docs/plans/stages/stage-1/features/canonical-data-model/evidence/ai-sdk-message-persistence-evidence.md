# AI SDK 消息持久化与运行记录字段（证据）

日期：2026-10-24。来源：一次定点调研 agent 报告。该 agent 没有写文件权限，报告由主会话代为存档，内容按原报告整理，未做改写。

**主会话核对（2026-10-24，用 npm 包 `ai@7.0.153` 本地解包）：**
- `npm view ai dist-tags`：latest 为 7.0.153，ai-v6 为 6.0.315，ai-v5 为 5.0.281。
- CHANGELOG 第 48–52 行确有 `interrupted` 新增说明及兼容性提示。
- `dist/index.d.ts` 中有 `allowSystemInMessages`，注释写明“Default: false”；也有 `include.requestMessages` 选项。

其余源码行号与文档引用**未由主会话逐条复核**，采用前须对照锁定版本重新核对。标注：【文档】为官方文档；【源码】为 7.0.153 源码或类型；【推断】为调研 agent 的推理，不是官方表述。

源码前缀 `S` = `https://github.com/vercel/ai/blob/ai@7.0.153/packages/ai/src`（tag 指向 `612be2311464804d1e4897afacbf8f3fc2f6d9e3`）。

## 0. 版本基线

- 【源码】npm latest 为 7.0.153。ADR 0004 的本地验证基于 7.0.148，相差 5 个补丁版本。
- 【源码】7.0.149 新增 finishReason `interrupted`，CHANGELOG 明言：即使是补丁版，扩展公开联合类型也可能破坏类型检查。【推断】存储层不应用 Postgres enum 或 CHECK 穷举 finishReason、part type。

## 1. UIMessage 结构、存储形状、消息 id

- 【源码】`S/ui/ui-messages.ts#L45`：`UIMessage { id; role: 'system'|'user'|'assistant'; metadata?; parts }`。注释建议避免 system 消息，把系统提示放在服务端设置。
- 【源码】UIMessage **没有 `createdAt`**。持久化文档里提到 createdAt 的说法是 v4 遗留。【推断】时间戳需要 SayHear 自己建列。
- 【源码】part 共 11 种：text、custom、reasoning、`tool-${name}`、dynamic-tool、source-url、source-document、file、reasoning-file、`data-${name}`、step-start。TextUIPart 为 `{ type:'text', text, state?: 'streaming'|'done', providerMetadata?, citations? }`。
- 【文档】https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence 写着“We recommend storing the messages in the `useChat` message format”。但该页没有给数据库表结构，示例是整段 JSON 文件。
- 【文档】唯一的官方 Postgres 示例在 v5 数据迁移指南（https://ai-sdk.dev/docs/migration-guides/migration-guide-5-0-data ）：`messages_v5(id, chatId fk cascade, createdAt, parts jsonb, role)`，一条消息一行，**不拆 parts 子表**。Vercel 官方 chatbot 模板的表名是 `Message_v2(id, chatId, role, parts json, attachments json, createdAt)`，名字里的 `_v2` 就是一次格式迁移留下的痕迹（https://github.com/vercel/chatbot/blob/c2f8235e1f3ea903ad8b7f61447c4f74164b5c58/lib/db/schema.ts#L42-L51 ）。
- 【文档】Supabase（https://supabase.com/docs/guides/database/json ）：几乎所有场景都推荐 jsonb，但提醒“Don't go overboard with json/jsonb columns”。
- 【文档】消息 id 默认在客户端生成；用户消息 id 由 `useChat` 在发请求前生成。assistant 消息 id 可以在服务端用 `generateMessageId`（需传 `originalMessages`）生成，或在 `start` chunk 里写入 `messageId`。
- 【源码】`S/ui-message-stream/get-response-ui-message-id.ts#L15-L35`：不传 `originalMessages` 时，id 交由客户端生成。
- 【推断】客户端给的 id 不可信：可以只把它当作幂等键，用 `(owner_id, client_message_id)` 加唯一约束，数据库主键由服务端生成。assistant 消息 id 在流开始前由服务端确定。

## 2. 中断、错误、工具调用

- 【源码】UI 流里的 `abort` chunk 不会生成 part，也不会把 text part 的 state 改成 done。【推断】停止后的部分回答就是已有的 text part，可能带 `state:'streaming'`，**SDK 没有“已中断”标记**。
- 【源码】服务端 UI `onEnd` 的参数是 `{ messages, responseMessage, isContinuation, isAborted, isCancelled?, outcome: completed|failed|aborted|unknown, finishReason? }`。
- 【文档】https://ai-sdk.dev/docs/advanced/stopping-streams ：
  - 客户端断开时 `isCancelled` 为 true，`outcome` 为 unknown，所以要同时检查两个标志。
  - `useChat().stop()` 只中止客户端请求；在 Vercel 上要配置 `supportsCancellation: true`（仅限 Node runtime），服务端才会收到 abort，否则生成可能继续。
  - abort 与 `resume: true` 不兼容。
- 【文档】持久化指南：用 `consumeStream()` 去掉背压后，客户端断开仍会走到 `onEnd` 并保存。指南也建议把请求状态（进行中、完成）存进消息。
- 【源码】`interrupted` 表示 Provider 流在没有完成信号时就结束了，输出可能不完整。
- 【源码】错误在 UI 流里是 `{type:'error', errorText}`，默认被打码为“An error occurred.”，**不会写进消息 parts**；原始错误只能在服务端的 `onError` 里拿到。【推断】错误类型和出错位置只能存进 run/attempt，这与 ADR 0005 一致。
- 【源码】工具 part 有 7 种 state：input-streaming、input-available、approval-requested、approval-responded、output-available、output-error、output-denied。【文档】加载带工具的历史前，应先用 `validateUIMessages` 校验；工具 schema 变了，旧消息可能校验失败。
- 【文档】v7 起 `onFinish` 改名为 `onEnd`（旧名作为 deprecated 别名保留），`fullStream` 改名为 `stream`，result 上的 UI 流方法 deprecated。
- 【推断】UI `onEnd` 返回的 `messages` 是整段历史，SayHear 应该只 upsert `responseMessage`。如果整段覆盖，可能把单条删除时已经清空的原文写回去（ADR 0010）。

## 3. 纯文本加结构列、读取时再转换

- 【文档】官方有先例：v5 数据迁移的第一阶段就是读取时做运行时转换，同时说明这只是临时方案。
- 【推断】SayHear 自己组装上下文（ADR 0004），可以直接从数据库行构造 ModelMessage。UIMessage 只用于 `useChat` 展示。
- 只存文本的代价（【源码】+【推断】）：
  1. 丢掉 text part 的 providerMetadata。阶段 1 关闭思考（ADR 0007），影响小；以后开启 reasoning 时需要补存。
  2. 工具调用和结果的配对无法用纯文本表达，至少需要一个 jsonb 列或单独记录。
  3. 多步之间的 step-start 边界会丢失。
  4. `convertToModelMessages` 不看 text 的 state，部分回答会被当作完整回答，所以**状态列无论采用哪种存法都必须由 SayHear 自己存**。
  5. v7 默认拒绝 messages 里的 system 消息（【文档】migration-guide-7-0，主会话已核对默认值为 false），存下来的系统消息要映射到 `instructions`。
  6. 好处：单条删除时清空原文只需改一列；Data API 和 RLS 下的查询更简单；SDK 改格式时数据库不用动。
- 格式变更史（【文档】迁移指南 5.0/6.0/7.0）：
  - v4→v5 是破坏性最大的一次：去掉 content，改由 parts 作为唯一来源；工具 part 改名，字段名也改了；官方迁移方案是新建表、双写、回填数据、切换读路径。
  - v5→v6：工具 state 新增 3 种，`convertToModelMessages` 改为 async。
  - v6→v7：UIMessage 外形没有破坏性变化，但 `system` 改名为 `instructions`，`onFinish` 改名为 `onEnd`，request/response body 默认不保留。
- 【推断】迁移风险从高到低：
  1. 整条 parts 存 jsonb：大版本升级时要迁移数据。
  2. 纯文本加结构列：对 SDK 变化最不敏感。
  3. parts 拆成子表：不推荐。

## 4. 运行记录字段来源

| 字段 | 来源 |
| --- | --- |
| usage（input/output/total，含缓存与 reasoning 明细，`raw` 为 Provider 原始数据） | `streamText` 的 `onEnd` 或 `await result.usage`。v7 中 usage 是所有步骤的合计，单步用 `finalStep.usage` |
| 每步 finishReason、rawFinishReason、providerMetadata、`model{provider,modelId}`、performance、warnings | `onStepEnd`（StepResult）/ `finish-step` part |
| finishReason | stop、length、content-filter、tool-calls、error、interrupted、other |
| 实际模型与响应 id | `response.modelId`、`response.id`、`response.timestamp` |
| 实际发出的 messages/body | `StepResult.request`，但 **v7 默认不保留**，需要 `include` 显式开启（主会话已核对选项存在）。【推断】输入快照可以直接存 SayHear 自己组装的内容，不依赖 SDK 回传 |
| 中止、错误 | `onAbort {callId, steps, reason?}`（进行中的那一步不在 steps 里）；`onError {error}` |
| callId | SDK 为每次生成调用分配的 id，适合记在 attempt 上 |

v7 新增的 `streamRetries` 省略时默认关闭，不会和 ADR 0004 的 `maxRetries: 0` 及应用层 fallback 叠加。

## 5. 对 ADR 的影响（待主会话处理）

- ADR 0004 需修订两处表述：v7 的系统提示参数叫 `instructions`；`request.messages/body` 需要显式开启。
- 不要用 Postgres enum 穷举 SDK 的联合类型。

## 6. 调研 agent 给出的表结构倾向（推断，不是决定）

- 消息：服务端生成的 id、owner_id、会话 id、role、text（可清空）、status、run_id（assistant 消息）、created_at、deleted_at，外加一个可选的 parts jsonb，只在出现工具、reasoning 或文件时使用。
- run/attempt：provider、modelId、response.id、finishReason、rawFinishReason、usage 结构列加 raw jsonb、outcome、错误摘要、callId、providerMetadata jsonb。
