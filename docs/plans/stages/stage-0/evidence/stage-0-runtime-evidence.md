# 阶段 0 运行层证据：AI SDK 与 Mastra

状态：Draft，运行层证据草稿。本文件不构成选型结论，也不替代 ADR。原文调研日期 2026-10-21 UTC，记录的是当日的文档与源码核对。本地 mock 实测已于 2026-10-21 执行，结果见 `docs/plans/stages/stage-0/evidence/stage-0-runtime-validation.md`（下称 validation）；本文中与实测冲突的结论以 validation 为准，正文已就地修订并标注证据层级。真实 Provider、Vercel 运行时与数据库仍未执行。

配套文件：主计划 `sayhear-build-and-learning-plan.md`，数据与交付层证据由另一份草稿维护。本文只回答运行层证据：自定义 OpenAI-compatible baseURL、额外 thinking 参数、关闭 memory 时是否读写存储、真实 HTTP 请求观测、AbortSignal、步骤上限、默认重试、默认遥测。

## 版本与证据层级

| 对象 | 固定版本 | 证据类型 |
| --- | --- | --- |
| AI SDK | `ai@7.0.148`，`@ai-sdk/openai-compatible@3.0.75` | npm registry 当前版本，官方文档 `ai-sdk.dev/llms.txt` 于 2026-10-21 抓取；本地 mock 实测见 validation |
| Mastra | `@mastra/core@1.79.0`（2026-10-21 发布） | 官方文档为滚动版本；源码固定到 tag `@mastra/core@1.79.0` 对应 commit `4c22623ea342a0ce611e15f89f4ab8b377bf7ee8`；本地 mock 实测见 validation |

引用规则：源码行号属于上述 commit。`mastra.ai/docs` 页面没有版本号，升级后必须重核。两者不是同一层：Mastra 的模型路由内部依赖 AI SDK provider 包，`@mastra/core@1.79.0` 的依赖包含 `@ai-sdk/provider-v7`（`@ai-sdk/provider@4.0.29`）和 `@ai-sdk/provider-utils-v7`。

证据标记：**实测** = 本地 mock 运行观测（validation）；**源码** = 固定版本源码阅读；**文档** = 官方文档，未运行；**判断** = 主 Agent 的取舍意见。

## 结论摘要

自定义 baseURL 在两边都能落地，但入口不同。AI SDK 用 `createOpenAICompatible({ baseURL })`。Mastra 的推荐路由字符串 `provider/model` 不携带 baseURL，必须改用对象形式 `{ id, url, apiKey, api }` 或自定义 gateway。Mastra 官方文档自身不一致：`docs/agents/overview` 明确要求字符串且不要传 provider 对象，`models/providers/deepseek` 又给出 `{ url, id, apiKey, headers }` 对象示例。源码确认对象形式受支持，本地 mock 实测也确认对象形式发出正确请求，因此按源码与实测判断，不按单页文档判断。

关闭 memory 时，AI SDK 无状态，只使用传入的 `messages`；Mastra 未配置 `memory` 时 `getMemory()` 返回 `undefined`，不创建 thread，也不保存消息（源码）。实测两边都能用自定义 baseURL、`thinking` 参数与显式 history 完成生成，Mastra 工作目录无新增会话文件。这只说明当前工作目录与本次运行未落盘，Mastra 会惰性建立一个内部内存快照存储，且未检查 `~/.mastra` 等全局路径，不能扩大为“全局没有任何存储”。

真实 HTTP 请求观测两边都可行但成本不同。AI SDK 有官方开关 `include: { requestBody, responseBody }`，也可在 provider 上注入自定义 `fetch` 抓取原始请求。Mastra 的模型 span 记录消息、参数和工具定义，不保证记录原始 HTTP body；要拿到 wire 级请求，需要在自定义 gateway 里注入 `fetch`，或包装全局 fetch。

Mastra 有一个必须显式处理的默认行为。`MASTRA_TELEMETRY_DISABLED` 未设置时，源码显示 `posthog-node` 默认向 `https://us.posthog.com` 发送功能使用与模型 token 用量事件（源码）。本地 mock 用网络拦截做了一次对照运行，未观测到任何外发尝试，但这既不证明发送，也不证明不发送（validation E12）。AI SDK 自身不主动外发，只有注册了 telemetry integration 才发事件，且可按调用关闭。

## 对等表

| 维度 | AI SDK 7.0.148 | Mastra 1.79.0 | 证据 |
| --- | --- | --- | --- |
| 自定义 OpenAI-compatible baseURL | `createOpenAICompatible({ name, apiKey, baseURL, headers, fetch, includeUsage, supportsStructuredOutputs, transformRequestBody })` | 对象形式 `{ id: 'provider/model', url, apiKey, headers, api }` 或自定义 gateway；纯字符串只能走内置 gateway 或 models.dev 注册表 | AI SDK 文档 `providers/openai-compatible-providers`；Mastra `packages/core/src/llm/model/shared.types.ts` 第 36-51 行，`router.ts` 第 590-607 行；实测 E1/E2 |
| 模型名传递 | `provider.chatModel('model-id')` | 对象 `id` 的斜杠后段，或 `{ providerId, modelId }` | 同上；实测 E1/E2 body 中 model 一致 |
| 额外 thinking 或自定义 body 参数 | `providerOptions: { <providerName>: {...} }` 中不认识的键被展开进请求 body | 同机制，键必须匹配解析出的 providerId | `openai-compatible-chat-language-model.ts` 第 163-165、304-318 行；Mastra `provider-options.ts`；实测 E1/E2 原样进入 body |
| 未配置 memory 时使用显式 messages | 无状态，不写任何存储 | 不创建 thread，不保存消息；有内部内存快照存储，仅用于暂停或恢复查询 | `agent.ts` 第 2769-2824 行 `getMemory()`；`agent.ts` 第 8513-8545 行 ephemeral Mastra；实测 E2/E10 仅覆盖工作目录 |
| 显式传入 memory 但未配置 memory | 不适用 | 记录警告 `No memory is configured but resourceId and threadId were passed in args`，不持久化 | `agent.ts` 第 8727 行 |
| 原始 HTTP 请求观测 | `include: { requestBody: true, responseBody: true }`；流式只支持 requestBody；也可自定义 `fetch` | 模型 span 记录 messages、modelSettings、tools；原始 body 需自定义 fetch 或 gateway | AI SDK `generating-text` 文档；Mastra `model.loop.ts` 第 190-205 行 |
| AbortSignal | `generateText` 与 `streamText` 接受 `abortSignal`，并提供 `onAbort`；客户端断开需运行时把 `req.signal` 传进来 | `agent.generate` 与 `agent.stream` 接受 `abortSignal`，工具执行上下文也带 `abortSignal`，内部用 `AbortSignal.any` 合并中断信号 | AI SDK `settings` 与 stream abort 文档；Mastra `llm-execution-step.ts` 第 747、862、1311-1321 行；实测 E3/E4 |
| abort 后的调用方形态 | 抛 `AbortError` | 不抛错，流正常结束，结果 `status='canceled'`、`finishReason='aborted'`；需读结果状态 | 实测 E3/E4；两边 mock 均观测到连接提前关闭 |
| 步骤上限默认值 | 裸 `streamText`/`generateText` 默认 `stopWhen: isStepCount(1)`，即 1 步；`ToolLoopAgent` 默认 `isStepCount(20)` | 默认 5，`maxSteps` 与 `stopWhen` 按 OR 组合 | 源码 `dist/index.js` 第 5344、8868、10602 行；实测 E7（1 次请求）、E8、E9；Mastra `model.loop.ts` 第 162-170 行 |
| 默认重试 | `maxRetries` 默认 2，设为 0 关闭 | 源码中 Mastra 自身用 `p-retry`，`retries: modelSettings?.maxRetries ?? 2`，并在调用 provider 前剔除该键；与 AI SDK 重试层不同层 | AI SDK 文档与实测 E5/E6；Mastra `llm-execution-step.ts` 第 1595-1605 行，仅为源码结论，未实测 |
| 默认遥测 | 不注册 integration 不外发；注册后默认发送，按调用 `telemetry: { isEnabled: false }` 关闭；默认记录输入输出 | 源码默认开启，`MASTRA_TELEMETRY_DISABLED=1` 关闭；默认 host `https://us.posthog.com` | AI SDK `telemetry` 文档；Mastra `telemetry/posthog.ts` 第 19-25 行；实测 E12 未观测到外发，不能据此判定实际发送与否 |
| 遥测发送内容 | 由 integration 决定，默认含输入输出，可 `recordInputs` 与 `recordOutputs` 关闭 | 源码定义主机名哈希、OS、Node 版本、Mastra 版本、project id、功能名、token 用量；未实测 | Mastra `telemetry/posthog.ts` 第 56-68 行，`feature-telemetry.ts`，`usage-telemetry.ts` |

## API 入口

AI SDK 最小形态。`providerOptions` 的键必须等于 provider 的 `name` 去掉点号后缀，源码用 `config.provider.split('.')[0].trim()` 计算。

系统提示不能放进 `messages`。`ai@7.0.148` 对 `role: 'system'` 的 message 直接抛 `AI_InvalidPromptError`，要求使用顶层 `system`（或 `instructions`）选项；实测 E1 首次失败即由此触发。下面示例用顶层 `system`。

```ts
const provider = createOpenAICompatible({
  name: 'opencode',
  apiKey: process.env.OPENCODE_API_KEY,
  baseURL: 'https://opencode.ai/inference/go/openai/v1',
});
const model = provider.chatModel('deepseek-v4.1-flash');

const result = streamText({
  model,
  system, // 不要写成 messages 里的 role: 'system'
  messages,
  abortSignal: req.signal,
  maxRetries: 0,
  stopWhen: stepCountIs(3), // 裸调用默认只有 1 步，工具循环需显式设置
  providerOptions: { opencode: { thinking: { type: 'enabled' } } },
  include: { requestBody: true },
  telemetry: { isEnabled: false },
});
```

Mastra 最小形态。对象形式不经过模型路由的 gateway 解析，直接构造 `createOpenAICompatible`。

```ts
const agent = new Agent({
  id: 'sayhear',
  name: 'SayHear',
  instructions,
  model: {
    id: 'opencode/deepseek-v4.1-flash',
    url: 'https://opencode.ai/inference/go/openai/v1',
    apiKey: process.env.OPENCODE_API_KEY,
    api: 'chat',
  },
});

const result = await agent.stream(messages, {
  abortSignal: req.signal,
  maxSteps: 5,
  modelSettings: { maxRetries: 0 },
  providerOptions: { opencode: { thinking: { type: 'enabled' } } },
});
```

备选 Provider 的官方 base 为 `https://api.deepseek.com`，模型 `deepseek-flash`。Mastra 文档的 DeepSeek 页给出了 `{ url: 'https://api.deepseek.com', id: 'deepseek/deepseek-flash', apiKey }` 的对象示例，并列出 `thinking` 与 `reasoningEffort` 两个 provider option。

## 关键源码原文

AI SDK 把未识别的 provider option 展开进 body，已知键会被过滤掉。

> `...Object.entries({ ...providerOptions?.[this.providerOptionsName], ...providerOptions?.[toCamelCase(this.providerOptionsName)] }).filter(([key]) => !Object.keys(openaiCompatibleLanguageModelChatOptions.shape).includes(key))`

来源 `https://unpkg.com/@ai-sdk/openai-compatible@3.0.75/src/chat/openai-compatible-chat-language-model.ts` 第 304-318 行。已知键是 `user`、`reasoningEffort`、`textVerbosity`、`strictJsonSchema`。`thinking` 不在其中，因此原样进入请求 body。

Mastra 对象形式直接构造兼容 provider。

> `createOpenAICompatible({ name: providerId, apiKey, baseURL: this.config.url, headers, supportsStructuredOutputs: true }).chatModel(modelId)`

来源 `https://github.com/mastra-ai/mastra/blob/4c22623ea342a0ce611e15f89f4ab8b377bf7ee8/packages/core/src/llm/model/router.ts` 第 596-607 行。注意该路径没有暴露 `fetch` 或 `transformRequestBody`。

Mastra 未配置 memory 时直接返回 undefined。

> `const memoryConfig = this.#memory ?? this.#inheritedMemory(requestContext); if (!memoryConfig) { return undefined; }`

来源同一 commit `packages/core/src/agent/agent.ts` 第 2779-2784 行。后续 `getOutputProcessors` 与 `getInputProcessors` 在 memory 为空时返回空数组。

Mastra 默认步骤上限为 5。

> `stopWhenToUse = stopWhen ?? llmStepCountIs(5);`

来源同一 commit `packages/core/src/llm/model/model.loop.ts` 第 162-170 行。

AI SDK 裸调用默认只走 1 步，`ToolLoopAgent` 才是 20 步。

> `stopWhen = isStepCount(1)`（`generateText` 与 `streamTextInternal` 的默认参数）

来源 `ai@7.0.148` 的 `dist/index.js` 第 5344 行与第 8868 行；`isStepCount(20)` 出现在第 10602 行附近的 `ToolLoopAgent` 默认值注释。实测 E7 在不传 `stopWhen` 时工具调用后只有 1 次请求，与源码一致。

Mastra 自身的默认重试（源码，未实测）。

> `retries: modelSettings?.maxRetries ?? 2`

来源同一 commit `packages/core/src/llm/model/llm-execution-step.ts` 第 1595-1605 行附近；调用 provider 前会从 `modelSettings` 中剔除 `maxRetries`，因此它与 AI SDK 的重试层不是同一层。本次未做重试实测。

Mastra 产品遥测默认开启。

> `const value = process.env['MASTRA_TELEMETRY_DISABLED']; if (!value) { return true; }`

来源同一 commit `packages/core/src/telemetry/posthog.ts` 第 19-25 行。默认 host 为 `https://us.posthog.com`。

## 最小验证：原计划与实测结果

以下三项原为文档无法回答的 unknown，已用本地 mock 执行，不需要真实密钥或外部服务。真实 Provider 的取消是否停止计费、Vercel 断开后的传播均不在本轮可证明范围内。完整观测、限制与判据对照见 validation。

### V1 自定义 baseURL 与额外 thinking 参数

原判据：两边 path 都是 `/v1/chat/completions`，body 的 `model` 等于 `deepseek-v4.1-flash`，body 出现 `thinking` 字段且结构与传入一致，Authorization 为 `Bearer` 占位值。任一边丢弃字段、拼接出双斜杠或路径错位即失败。

结果：通过（validation E1/E2）。两边 path、model、`thinking` 与 Bearer 均符合，显式 history 完整。Mastra 对象形式的请求 body 键只有 `model,thinking,messages`。

### V2 AbortSignal 传播与默认重试

原判据：abort 后调用方以 `AbortError` 结束，mock 观察到连接关闭，且不产生已完成 assistant 记录。默认设置下请求次数为 3，关闭重试后为 1。两边都必须满足。

结果：部分通过，判据需改（validation E3–E6）。AI SDK abort 抛 `AbortError`；Mastra 不抛错，流正常结束，结果 `status='canceled'`、`finishReason='aborted'`，调用方需读状态。两边 mock 都观测到连接提前关闭，这只证明本地连接关闭，不证明 Provider 停止计费。AI SDK 默认重试实测为 3 次请求，`maxRetries: 0` 为 1 次。Mastra 默认重试未实测，仅有源码证据（`p-retry`，`retries: modelSettings?.maxRetries ?? 2`）。

### V3 关闭 memory 与默认遥测

原判据：没有会话消息落盘，没有 thread 记录，不出现对外 PostHog 请求。若普通生成仍写入内部快照，需记录写入位置与清理方式，再判断是否可接受。AI SDK 侧只需确认无文件写入。

结果：有限通过（validation E2/E10/E12）。Mastra 不配 memory 时显式 history 正常生成，未创建 thread，工作目录无 `.db/.sqlite/.jsonl` 新增文件。未检查 `~/.mastra` 等全局目录，不能断言“全局无任何存储”。未设置 `MASTRA_TELEMETRY_DISABLED` 的对照运行在网络拦截下未出现外发尝试，但源码默认开启；不能把源码默认值写成已实际发送，也不能据此宣称不发。

三项验证的执行前提：本地可运行 Node 22，可绑定 localhost 端口。不读取真实密钥，不连接 `opencode.ai` 或 `api.deepseek.com`。本轮实际使用 Node v24.18.0，全部请求指向 `127.0.0.1`。

## 推荐条件与维护责任

本地 mock 结果没有推翻 AI SDK 的条件优先，也没有排除 Mastra。AI SDK 的维护面更小：一个 provider 工厂加 `messages`，没有默认产品遥测，请求观测与取消都有官方开关。代价是上下文选择、工具循环策略和保存全部由 SayHear 自己组织。需要显式处理的是裸调用默认 1 步、顶层 `system` 与 `AbortError`。

Mastra 仍然可行：对象形式的自定义 baseURL、显式 history、`thinking` 与 `maxSteps` 均已本地通过。采用它需要接受显式设置 `MASTRA_TELEMETRY_DISABLED`、按结果状态而非异常处理取消，并承担升级时重核滚动文档的成本。工作目录无落盘只是有限证据，不能当作全局无存储的保证。

两边的模型对象可以互用是常见说法，但本次未验证。Mastra 内部依赖 AI SDK provider 包，不等于任意版本、任意配置下都能互换；如需依赖这一点，应单独验证，不写成绝对保证。

维护责任：采用方负责在每次升级后重跑 V1 与 V3，核对 `@mastra/core` 的 gateway 解析、telemetry 默认值和 `maxSteps` 默认值是否变化。Provider 适配层负责人同时负责记录实际发送的模型名、baseURL 和额外参数。滚动文档不能作为长期证据，必须固定版本。

## 未执行事项

本轮已执行：依赖安装、本地 mock、网络拦截、abort 与重试观测、遥测开关对照。仍未执行：真实 Provider 调用、Vercel 运行时验证、数据库连接、`~/.mastra` 等全局路径检查、Mastra 默认重试实测、真实取消后的计费行为。上述 unknown 不因本地 mock 通过而消失。
