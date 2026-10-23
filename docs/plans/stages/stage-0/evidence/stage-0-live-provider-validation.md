# 阶段 0 真实 Provider 最小验证

执行日期：2026-10-22。Luke 明确授权从本地 `.env` 安全调取 `OPENCODE_API_KEY` 与 `DEEPSEEK_API_KEY`。脚本只读取这两个指定变量，不执行 `.env`，不打印密钥、请求头或错误响应正文。仅发送合成 TEST_OK 内容，未发送私人对话，未连接数据库、部署或创建资源。

## 范围与结果

Node 原生 `fetch` 直接调用 Chat Completions。每条路线各发一次流式请求与一次强制工具调用，共 4 次，不自动重试。单次截止 45 秒，`max_tokens: 128`，`thinking.type: disabled`。工具名 `echo_marker`，参数仅为合成标记；未执行外部工具，也未回传工具结果继续生成。

| 路线 | 流式 | 工具调用 | 返回模型标识 | 两次合计 token |
| --- | --- | --- | --- | --- |
| OpenCode Go | HTTP 200，收到 TEST_OK、`[DONE]`、usage，结束为 `stop` | HTTP 200，`tool_calls`，名称与参数符合预期 | `deepseek-v4.1-flash` | 339 |
| DeepSeek 官方 | HTTP 200，收到 TEST_OK、`[DONE]`、usage，结束为 `stop` | HTTP 200，`tool_calls`，名称与参数符合预期 | `deepseek-flash` | 338 |

OpenCode endpoint 为 `https://opencode.ai/inference/go/openai/v1/chat/completions`；DeepSeek endpoint 为 `https://api.deepseek.com/chat/completions`。Go 请求使用专属 User-Agent 与随机不含个人信息的 session ID。

## 第二轮：AI SDK 真实链路与受控实验

使用既有固定依赖 `ai@7.0.148`、`@ai-sdk/openai-compatible@3.0.75`，又完成 4 次真实请求，均只发合成内容、`maxRetries: 0`、45 秒截止。正常流式上限 128 token，取消场景上限 512 token。

- Go 与 DeepSeek 经 `streamText` 各一次正常流式请求，均收到 TEST_OK，`finishReason: stop`，SDK usage 各为 19 token，每次只发出一个 HTTP 请求。
- 受控 fallback：实验代码在主路线发网络请求之前注入 503 异常，由实验自身的两路线循环切到 DeepSeek。备用真实流式成功，只发一个 HTTP 请求。该结果仅证明这段实验控制逻辑可调用备用；未验证真实 Go 故障分类，也不是 SDK 自动提供 fallback 的证据。
- 取消：Go 收到首个文本片段后调用 `AbortController.abort()`。SDK `fullStream` 给出 `abort` 事件，传到 fetch 的 signal 被中止，未收到正常完成事件，只发一个 HTTP 请求。不能证明上游停止生成或计费，也未覆盖浏览器断开、Vercel 或落库。

**取消处理的更正**：旧 ADR / SPEC 将“AI SDK 中止必抛 AbortError”写得过于绝对。本次消费 `textStream` 后再读取 `fullStream`，实际观察到 `abort` 事件，无异常抛到实验的 catch。应用应按取消意图及 SDK 终态事件判断中断，不能只靠 catch AbortError；不同消费方式的差异应保留。

临时脚本 `sdk-live-probe.mjs` 与脱敏结果 `sdk-live-results.json` 位于同一 job 临时目录。本轮与上一轮合计 8 次真实请求。无性能基线或费用结论。

## 证据与限制

本次证明当前凭据与上述模型 ID 可完成这两类最小请求，不证明返回 alias 背后的具体权重快照。未验证 AI SDK 到真实 Provider 的适配、完整工具循环、思考模式、流式工具参数、取消、额度用尽、自动 fallback、Vercel 运行时或恢复演练。未制造认证或余额错误。没有计算费用，不把 token 数当作费用。

一次请求的时延不作为性能基线。本次不是约一小时的合成示范，不计为该项完成。

可复用临时脚本：`/Users/lukemyself/.claude/jobs/470196ef/tmp/provider-probe.mjs`。脱敏结果：同目录 `provider-probe-results.json`。临时目录会随 job 删除；本文保留可追溯的请求形状、次数和结果，不保留任何凭据。
