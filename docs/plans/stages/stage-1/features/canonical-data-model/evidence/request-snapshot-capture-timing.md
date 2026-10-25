# 实际请求快照的捕获与保存时序

日期：2026-10-24。目的：为 M2 输入快照提供可决策的捕获位置和发送顺序，不执行实现、构建、测试或真实 Provider 调用。停止条件：确认是否存在发送前的最终请求体边界、完成回调的覆盖限制，以及发送不确定性。

## 证据基线

主 Agent 直接读取固定 tag `ai@7.0.153` 的公开源码，并核对 npm registry：本次 `ai` latest 为 `7.0.153`，`@ai-sdk/openai-compatible` latest 为 `3.0.78`，同 tag 下该包的 package.json 也为 `3.0.78`。这是本次核查基线，不是已安装或已锁定的项目依赖。仓库尚无产品 package.json 或锁文件，实施前仍需锁定版本并复核。

- [固定 tag 的 compatible package.json](https://github.com/vercel/ai/blob/ai%407.0.153/packages/openai-compatible/package.json)
- [官方 Provider 配置文档](https://ai-sdk.dev/providers/openai-compatible-providers)：提供自定义 fetch 以拦截请求。

## 已直接核对的源码事实

1. Provider 配置将自定义 fetch 传入模型公共配置。见 [openai-compatible-provider.ts](https://github.com/vercel/ai/blob/ai%407.0.153/packages/openai-compatible/src/openai-compatible-provider.ts#L150-L174)。
2. 流式调用先 getArgs，再 transformRequestBody，随后将 body、abortSignal、自定义 fetch 交给 postJsonToApi。见 [chat-language-model.ts](https://github.com/vercel/ai/blob/ai%407.0.153/packages/openai-compatible/src/chat/openai-compatible-chat-language-model.ts#L451-L487)。
3. postJsonToApi 对 body 执行 JSON.stringify；postToApi 在调用 fetch 时传入该序列化内容与取消信号。因而该链路上的自定义 fetch 看见的是转换后的 JSON 请求体，已晚于 SDK/Provider 参数转换，早于其转交的网络 fetch。见 [post-to-api.ts](https://github.com/vercel/ai/blob/ai%407.0.153/packages/provider-utils/src/post-to-api.ts#L11-L42)及[调用位置](https://github.com/vercel/ai/blob/ai%407.0.153/packages/provider-utils/src/post-to-api.ts#L93-L102)。这是源码机制证据，不是自定义 wrapper 已运行通过。
4. requestBody 和 requestMessages 默认不在步骤结果中保留，需要 include 显式选择。见 [stream-text.ts include 类型](https://github.com/vercel/ai/blob/ai%407.0.153/packages/ai/src/generate-text/stream-text.ts#L197-L214)。
5. onStepEnd 的通知发生在 finish-step 处理；flush 时没有已记录步骤则提前返回，已有步骤但 isAborted 时也会在 onEnd 前返回。不能仅依赖这些完成回调覆盖所有失败、取消请求。见 [步骤通知](https://github.com/vercel/ai/blob/ai%407.0.153/packages/ai/src/generate-text/stream-text.ts#L1728-L1765)及[结束处理](https://github.com/vercel/ai/blob/ai%407.0.153/packages/ai/src/generate-text/stream-text.ts#L1791-L1826)。
6. 自定义 fetch 抛出的错误会进入 SDK 的错误处理，网络错误可能被映射为可重试的 APICallError。见 [post-to-api.ts](https://github.com/vercel/ai/blob/ai%407.0.153/packages/provider-utils/src/post-to-api.ts)和 [handle-fetch-error.ts](https://github.com/vercel/ai/blob/ai%407.0.153/packages/provider-utils/src/handle-fetch-error.ts#L41-L101)。应用必须区分自有持久化失败和 Provider 网络失败，不能只凭最外层错误或 errno 决定 fallback。

## 设计建议，尚未接受

阶段 1 在每个 attempt 专属的 Provider 请求边界捕获最终 JSON 请求体，先保存至该 attempt 的快照列，确认保存成功，再转交同一请求体给真实网络 fetch。不修改全局 fetch，也不把所有数据库、Auth 等网络请求纳入捕获。

- 快照只保存请求内容，不保存认证头、密钥或含凭据的 URL；不把整个 RequestInit、错误对象或请求头直接序列化入库或日志。实际内容副本与消息来源、选择理由、应用/指令版本的对应关系仍需定义。
- 保存快照失败则不发出当前 Provider 请求，按本地持久化错误处理，不因它触发 Provider fallback。SDK 自动重试与流重试不得绕过该门槛；需要实施验证错误归因与调用次数。
- 保存期间仍计入整次应用预算，保存后再次检查取消与剩余预算，已停止或超时则不转交网络。Provider 首段计时不应把数据库等待冒充 Provider 等待，具体计时边界由 M4 实施核对。
- 完成回调可补 usage、结束原因或用于交叉核对，但不能作为首次保存请求副本的唯一入口。

相较于生成结束后再存快照，本建议能在发送前阻止“无法保存本次输入但仍调用 Provider”，也能保留首段前故障的输入证据。代价是发送前多一次数据库等待，数据库故障会阻止新模型调用。本次未测量延迟，不给出时间承诺。

## 必须保留的证据边界

保存快照之后、实际发起网络调用之前可以崩溃。因此有快照只证明内容已准备并保存，不能单凭它声称已发送或 Provider 已收到。

应用数据库写入与外部 Provider 收到请求不是一个共同事务。记录发送标记之前或之后都可能发生崩溃；本地记录只能诚实区分已确认的本地事实与不确定的远端结果。按 ADR 0006，结果无法确认时保留 unknown，不自动重放或臆测计费。

jsonb 保存的是 JSON 内容和数组顺序，不承诺保留请求字节、空白或对象键顺序。本阶段需要核对模型输入内容，不做 HTTP 字节级取证。实施时须防止解析或重建过程改变原始发送内容，真实转发仍使用捕获时同一请求体。

## 未决与验证交接

- 保存成功但尚未发送、发送失败或结果未知的具体字段、时间戳和界面文案。
- wrapper 中保存失败是否被错误映射到网络重试，取消能否在持久化等待后阻止发送，响应与 checkpoint 行为是否保持，须由 M4 的受控 Provider 和真实部署证据验证。本 skill 不运行这些验证。
- 捕获失败或请求体形状不受支持时如何拒绝发送，以及快照字段与来源映射由 M2/M6 收口。
- 独立 investigator session `0f5443d4-4777-4231-822c-8bf8ff3b0a40` 在 240 秒后返回 `timed_out` / `TIMED_OUT`，配置模型组 `group/light[1m]`，返回模型 `glm-5.3-flash`，没有完整报告。Read 工具限于工作目录，worker 改用 Bash 读取临时源码；最终 warnings 为 null。本文源码事实由主 Agent 直接核对，不宣称独立审查通过；无活跃委派，也未启动 fallback。
