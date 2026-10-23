# 阶段 0 运行层验证：本地 mock 实测

状态：实验记录。执行日期 2026-10-21（UTC），本地 macOS / Node v24.18.0 / npm 11.16.0。全部请求指向 `127.0.0.1` 本地 mock，使用 dummy key，未读取 `.env`，未访问外部 LLM、云资源或真实凭据。本文只记录本地 mock 观测，不构成 Vercel 运行时或真实 Provider 行为的证据，也不证明取消后 Provider 停止计费。

配套草稿：`docs/plans/stages/stage-0/evidence/stage-0-runtime-evidence.md`（只读调研）。本文中“纠正”一节列出该草稿需要修订的结论。

## 依赖与安装

实验目录 `/tmp/sayhear-stage0-runtime-1792648199`（独立临时目录，未改动仓库依赖）：

```json
{
  "private": true,
  "type": "module",
  "dependencies": {
    "ai": "7.0.148",
    "@ai-sdk/openai-compatible": "3.0.75",
    "@mastra/core": "1.79.0"
  }
}
```

```bash
cd /tmp/sayhear-stage0-runtime-1792648199
npm install --no-audit --no-fund --ignore-scripts
```

结果：通过，152 个包，约 5 秒。版本经 `npm ls --depth=0` 核对为 `ai@7.0.148`、`@ai-sdk/openai-compatible@3.0.75`、`@mastra/core@1.79.0`。

Node 兼容：`ai` 与 `@ai-sdk/openai-compatible` 的 `engines.node` 为 `>=22`，`@mastra/core` 为 `>=22.13.0`。本机 Node v24.18.0 满足三者。这是包声明与本地运行，不代表 Vercel 运行时的 Node 版本与冷启动行为。

## 隔离与安全措施

- 实验代码放在 `$EXP/scripts`，工作目录为 `$EXP/work`，依赖目录为 `$EXP/node_modules`；不在 `node_modules` 内运行解释器，不执行下载包自带脚本（`--ignore-scripts`）。
- 网络拦截 preload `$EXP/scripts/block-net.cjs` 覆盖 `fetch`、`http(s).request`、`dns.lookup`，非 `localhost/127.0.0.1/::1` 一律拒绝并打印 `NET-BLOCK`。只用于本实验观测，不是产品拦截方案。
- 运行时设置 `MASTRA_TELEMETRY_DISABLED=1`，并额外做一次未设置该变量的对照运行。
- mock 只绑定 `127.0.0.1` 随机端口，记录 method、path、headers、原始 body 与连接是否提前关闭。

## 运行命令

```bash
EXP=/tmp/sayhear-stage0-runtime-1792648199
cd "$EXP/work"
MASTRA_TELEMETRY_DISABLED=1 \
NODE_OPTIONS="--require $EXP/scripts/block-net.cjs" \
node "$EXP/scripts/experiment.mjs"
```

诊断脚本（abort 形态与遥测对照）：

```bash
MASTRA_TELEMETRY_DISABLED=1 NODE_OPTIONS="--require $EXP/scripts/block-net.cjs" node "$EXP/scripts/probe-e4b.mjs"
MASTRA_TELEMETRY_DISABLED=1 NODE_OPTIONS="--require $EXP/scripts/block-net.cjs" node "$EXP/scripts/probe-e4c.mjs"
MASTRA_TELEMETRY_DISABLED=1 NODE_OPTIONS="--require $EXP/scripts/block-net.cjs" node "$EXP/scripts/probe-e4-telemetry.mjs"
```

日志：`$EXP/work/run2.log`（主实验）、`run1.log`（首次失败运行，已删除，结论记录在下文）。

## 实测结果

状态含义：通过 = 实测符合判据；失败 = 实测不符合；未运行 = 未取得实验证据。

| 编号 | 实验 | 状态 | 实测 |
| --- | --- | --- | --- |
| E1 | AI SDK 非流式，`createOpenAICompatible` + `generateText` | 通过 | path `/v1/chat/completions`；body `model=deepseek-v4.1-flash`；`thinking={type:'enabled',budget_tokens:128}` 原样出现；`Authorization: Bearer dummy-key`；messages 角色 `system,user,assistant,user` |
| E2 | Mastra 非流式，对象形式 `{id,url,apiKey,api:'chat'}` + 显式历史，不配 memory | 通过 | 同一 path 与 model；`thinking` 原样出现；Bearer dummy-key；messages 四角色完整；请求 body 键仅 `model,thinking,messages`；工作目录无新增文件 |
| E3 | AI SDK `streamText` + 300ms 本地 abort | 通过 | 调用方抛 `AbortError`（"This operation was aborted"）；mock 观测到连接提前关闭 |
| E4 | Mastra `agent.stream` + 300ms 本地 abort | 通过（判据需改） | 不抛错：`textStream`/`fullStream` 正常结束；结果对象 `status='canceled'`、`finishReason='aborted'`；mock 观测到连接提前关闭。首次记录为 failed 是脚本判据写错，不是框架失败 |
| E5 | AI SDK 默认重试：mock 连续两次 500 后 200 | 通过 | 共 3 次请求（1 次 + 2 次重试），最终成功 |
| E6 | AI SDK `maxRetries: 0`：mock 一次 500 | 通过 | 共 1 次请求；抛 `AI_APICallError`（mock 500） |
| E7 | 裸 `streamText` + tool call，不传 `stopWhen` | 通过 | 仅 1 次请求，工具调用后不继续。源码默认 `stopWhen = isStepCount(1)` |
| E8 | `streamText` + `stopWhen: stepCountIs(3)` + tool call | 通过 | 3 次请求，工具循环按显式条件继续 |
| E9 | Mastra `maxSteps: 2` + tool call | 通过 | 2 次请求后停止 |
| E10 | Mastra 不配 memory 运行后检查落盘 | 部分通过 | 工作目录无 `.db/.sqlite/.jsonl` 新增文件；未检查 `~/.mastra` 等全局目录，不能据此断言“无任何落盘” |
| E11 | Mastra 默认重试次数 | 未运行 | 仅源码证据：`p-retry` 使用 `retries: modelSettings?.maxRetries ?? 2` |
| E12 | 未设置 `MASTRA_TELEMETRY_DISABLED` 时是否外发 PostHog | 未取得证据 | 独立 `Agent` 运行未出现任何外发尝试（`NET-BLOCK` 计数 0）；源码默认开启，但不能据此证明实际发送 |

请求计数：主实验 14 次本地请求；诊断脚本另有 6 次，合计 20 次。单请求超时 10 秒。整体实际耗时约 12 分钟，超过 8 分钟时间盒，原因是首轮两处脚本/用法错误与 abort 形态复核；未继续追加实验。

### 首次失败运行记录

`run1.log` 中 E1/E5/E6/E7/E8 失败，根因不是框架：`ai@7.0.148` 不允许把 `role: 'system'` 放进 `messages`，抛 `AI_InvalidPromptError: System messages are not allowed in the prompt or messages fields. Use the instructions option instead.` 改用顶层 `system` 选项后全部通过。E4 首次记为 failed 是脚本把“未抛错”当成失败，复核后按 `status/finishReason` 判定为通过。E9 首轮失败是 mock 对 `stream:true` 返回了非流式 JSON，修正 mock 后通过。

## 判据对照

草稿的 V1：两边 path、model、thinking、Bearer 均符合，通过。

草稿的 V2：AI SDK 的 abort 以 `AbortError` 结束且连接关闭，通过；重试次数默认 3 次请求、`maxRetries: 0` 为 1 次，通过。Mastra 的 abort 不抛 `AbortError`，而是结束流并标记 `status='canceled'`、`finishReason='aborted'`，连接同样关闭。因此“两边都必须以 AbortError 结束”的判据不成立，应改为“连接关闭且不产生完整 assistant 结果”。

草稿的 V3：Mastra 未配置 memory 时显式历史可正常生成，未创建 thread，工作目录无会话落盘；未检查全局目录，不能扩大为“无任何写入”。遥测默认值只有源码证据，本地未观测到实际外发。

## 需要纠正的草稿结论

1. “直接调用 `streamText` 或 `generateText` 无步骤上限”不成立。`ai@7.0.148` 的 `dist/index.js` 中 `generateText`（第 5344 行）与 `streamTextInternal`（第 8868 行）默认 `stopWhen = isStepCount(1)`；E7 实测工具调用后仅 1 次请求。`isStepCount(20)` 是 `ToolLoopAgent` 的默认值（第 10602 行注释），不是裸调用的默认值。工具循环要继续，必须显式传 `stopWhen`；`ai@7.0.148` 的类型声明中没有 `maxSteps` 选项。
2. “两边 abort 都以 AbortError 结束”不成立。Mastra 的 `agent.stream` 在 abort 后流正常结束，`status='canceled'`、`finishReason='aborted'`，调用方需读结果状态而不是捕获异常。AI SDK 则抛 `AbortError`。
3. AI SDK 的系统提示必须走顶层 `system`（或 `instructions`），放进 `messages` 会直接报错。草稿示例未说明这一点，实际接入容易踩坑。
4. Mastra 默认重试不是“未固定的 unknown”。源码显示其自身用 `p-retry`，默认 `retries: 2`，并在调用 provider 前从 `modelSettings` 中剔除 `maxRetries`。该层与 AI SDK 的重试层不是同一层；未做实验验证，需标注为源码结论。
5. Mastra 产品遥测“默认开启并发送”只有源码依据（`isTelemetryEnabled` 默认 true、host 为 `https://us.posthog.com`）。本次独立 Agent 运行未观测到任何外发尝试，不能把源码默认值写成已观测事实，也不能反过来宣称“不发”。
6. 草稿中 `thinking` 的键名规则正确：`providerOptionsName = provider.split('.')[0].trim()`。实验中 provider 名 `mock`，键 `mock.thinking` 原样进入 body。Mastra 对象形式同样透传，前提是键与 `id` 的 provider 段一致；本次只验证了匹配的情况，未验证不匹配时的行为。

## 限制

- mock 只验证 wire 形状、连接关闭和重试计数，不验证真实 Provider 的思考参数支持、错误码分类、取消后是否停止计费。
- 未在 Vercel 或任何 serverless 运行时执行；不覆盖冷启动、函数超时、平台级请求中止。
- E10 只检查了当前工作目录，未检查 `~/.mastra` 或其它全局路径。
- Mastra 默认重试、遥测实际发送均为未运行或仅有源码证据。
- 脚本与依赖位于 `/tmp`，重启后可能丢失；结论以本文记录为准。复现需重建目录并重新安装固定版本。
- 网络拦截 preload 只覆盖 Node 的 `fetch`、`http(s)`、`dns`，不覆盖原生扩展或子进程网络。

## 实验脚本路径

- `/tmp/sayhear-stage0-runtime-1792648199/scripts/experiment.mjs`：主实验 E1–E10
- `/tmp/sayhear-stage0-runtime-1792648199/scripts/mock.mjs`：本地 OpenAI-compatible mock 与超时工具
- `/tmp/sayhear-stage0-runtime-1792648199/scripts/block-net.cjs`：非 localhost 网络拦截 preload
- `/tmp/sayhear-stage0-runtime-1792648199/scripts/probe-e4b.mjs`：abort 三种消费方式对照
- `/tmp/sayhear-stage0-runtime-1792648199/scripts/probe-e4c.mjs`：abort 后结果状态读取
- `/tmp/sayhear-stage0-runtime-1792648199/scripts/probe-e4-telemetry.mjs`：遥测开关对照
- `/tmp/sayhear-stage0-runtime-1792648199/work/run2.log`：主实验日志
- `/tmp/sayhear-stage0-runtime-1792648199/package.json`：固定依赖清单
