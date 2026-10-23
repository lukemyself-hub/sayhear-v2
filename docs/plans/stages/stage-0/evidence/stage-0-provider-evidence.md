# 阶段 0 Provider 证据备忘

状态：Draft，证据备忘。阶段 0 已由 Luke 授权启动，但本文件不是 ADR，不是 working spec，也不代表阶段 0 已验收或技术路线已被接受。本轮只修正证据与归因，不改变已授权的方向。

## 这份文档解决什么

把旧仓库的 Provider 实现与 ADR、当前官方页面，以及尚未验证的线索放在一处，供阶段 0 做 Provider 决定。范围只覆盖 OpenCode Go 与 DeepSeek 官方 API 两条路线。本次没有重新比较 Harness、数据库或记忆组件，也没有调查 WorkBuddy。

以下偏好已由 Luke 给出，本文件不再询问：

- OpenCode Go 为主路径。
- DeepSeek 官方 API 为 fallback。
- 两边目标模型都是 DeepSeek V4.1 Flash。
- 暂不设 API 月预算。

本轮没有读取密钥、发送真实请求、部署、联系外部、安装依赖或启动 agent。前轮调查读取了下列官方页面；本轮为修正 Responses 结论，定点补读了 Responses API 页面。官方页面是滚动文档，接入时应重新核对。

## 证据等级

| 标记 | 含义 | 能证明什么 | 不能证明什么 |
| --- | --- | --- | --- |
| `[文档]` | 官方页面当时写明的接口、字段、限制和条款 | 页面当时写明的接口、字段、限制和条款 | 实际服务行为、当前账号可用性、长期稳定性 |
| `[旧仓库]` | 旧仓库 `/Users/lukemyself/Projects/SayHear` 的代码、ADR、任务记录和验证证据 | 当时实现过什么、当时哪些请求成功 | v2 可以照搬，或当前仍然成立 |
| `[未实测]` | 有线索但没有可复核证据 | 需要验证的问题 | 任何确定结论 |
| `[建议]` | 主 Agent 的判断 | 一个可讨论的起点 | 已获 Luke 接受 |

## 两条路线的事实

### OpenCode Go

| 项目 | 内容 | 等级 |
| --- | --- | --- |
| 线索中的 base | `https://opencode.ai/inference/go/openai/v1`。本次抓取只确认了完整 chat endpoint 和 models URL，没有单独读到 base 字段 | `[未实测]` |
| 文档列出的 endpoint | `https://opencode.ai/inference/go/openai/v1/chat/completions` | `[文档]` |
| 文档列出的模型列表 | `https://opencode.ai/inference/go/v1/models` | `[文档]` |
| 模型 ID | `deepseek-v4.1-flash` | `[文档]` |
| 协议 | OpenAI-compatible Chat Completions；文档列出 `@ai-sdk/openai-compatible` | `[文档]` |
| 用途说明 | 面向 OpenCode 和其他发送相似请求的编码 agent；要求客户端使用自己的 user agent，并在 `x-opencode-session` 发送稳定 session ID | `[文档]` |
| 非编码私人应用 | 文档没有明确许可，也没有明确禁止 | `[文档]`，兼容性 `[未实测]` |
| 训练与保留 | DeepSeek V4.1 Flash 标为不用于训练，保留 0 天；ZDR 协议按月续签，当前有效期到 2026-10-31 | `[文档]` |
| 套餐额度 | Go 上 DeepSeek V4.1 Flash 每月 80 美元额度，Go Plus 为 160 美元；单模型限制为 5 小时 20%、每周 50%、每月 100% | `[文档]` |
| 额度用尽后的文档选项 | 可改用免费模型；若 Console 有余额且启用 Extra usage，则回退到按量付费 | `[文档]` |
| 固定 model 请求在额度用尽时的行为 | 文档没有说明固定 `model` 请求是否会自动换模型，也没有描述错误形状 | `[未实测]` |
| 旧仓库使用的 endpoint | `https://opencode.ai/zen/go/v1/chat/completions`，与当前文档路径不同 | `[旧仓库]` |
| 旧仓库的请求头 | Bearer key、`SayHear/1.0`、不透明 `x-opencode-session` | `[旧仓库]` |
| 旧仓库的请求形状 | `tool_choice: "auto"`、`stream_options.include_usage`、要求 `[DONE]` 结束标记；丢弃 `reasoning_content`；工具调用后只做一次不带工具的续写 | `[旧仓库]` |
| 旧仓库的运行证据 | 2026-10-04 合成 SSE 探针成功；2026-10-14 一次真实文字对话使用 `opencode-go / deepseek-v4.1-flash`，可见回复 2.6 秒，3118 输入、102 输出 token | `[旧仓库]` |

旧仓库证据只能说明那条路径当时可用。它不能证明当前 endpoint 仍相同，不能证明非编码用途被允许，也不能证明回复质量、工具循环或多轮稳定性。

### DeepSeek 官方 API

| 项目 | 内容 | 等级 |
| --- | --- | --- |
| OpenAI-compatible base | `https://api.deepseek.com` | `[文档]` |
| Chat Completions 路径 | `POST /chat/completions` | `[文档]` |
| Anthropic-compatible base | `https://api.deepseek.com/anthropic` | `[文档]` |
| Responses API | 官方文档有独立的 Responses API 页面，标题为 “Responses API \| DeepSeek API Docs”，记录 `POST /responses`；必填 `model`（`deepseek-flash` 或 `deepseek-v4-pro`）和 `input`/`instructions`，可选 `reasoning`、`max_output_tokens`、`stream`、`text`、`tools`、`tool_choice` 等；流式以 `response.completed`、`response.incomplete` 或 `response.failed` 结束；页面未写 base URL，也没有弃用提示。根页导航未列该项，不等于官方未文档化 | `[文档]` |
| 模型 ID | `deepseek-flash` 是 alias，当前由 `DeepSeek-V4.1-Flash-1017` 承载；`deepseek-v4-pro` 单列；`deepseek-v4-flash` 和 `deepseek-v4-flash-vision-exp` 仍被接受，但模型已退役，请求会转到 1017 | `[文档]` |
| alias 更新与快照 | 模型页没有说明 alias 何时更新，也没有说明如何固定不可变快照 | `[文档]` |
| 流式 | `stream: true` 加 `stream_options`；SSE 以 `data: {JSON}` 发送，以 `data: [DONE]` 结束；`include_usage: true` 时最后一个 chunk 带 usage；`stream_options` 不与 `stream: true` 同用会返回 400 | `[文档]` |
| 结束原因 | `stop`、`length`、`content_filter`、`tool_calls`、`insufficient_system_resource`、`aborted` | `[文档]` |
| 参数 | `max_tokens` 范围 1 到 393216；`response_format` 支持 `text` 和 `json_object`；`tools` 与 `tool_choice` 可用 | `[文档]` |
| 错误码 | 400、401、402、422、429、500、503；500 和 503 建议短暂等待后重试，429 建议放慢请求 | `[文档]` |
| 思考模式 | `thinking` 取 `{"type": "enabled"}` 或 `{"type": "disabled"}`；`reasoning_effort` 接受 `low`、`high`、`max`，Chat Completions 参数页另列 `none`；默认启用，effort 为 `high` | `[文档]` |
| 思考内容 | 返回在 `reasoning_content`；流式在 `delta.reasoning_content` | `[文档]` |
| 不带工具的思考回传 | 之前的 `reasoning_content` 不必回传，带了也会被忽略 | `[文档]` |
| 带工具的思考回传 | 每个后续请求都要回传完整 `reasoning_content`，包括没有工具调用的轮次 | `[文档]` |
| 思考模式限制 | 不支持 `temperature`、`presence_penalty`、`frequency_penalty`，传入不生效；`tool_choice` 的 `required` 和指定工具在思考模式下返回 400 | `[文档]` |
| 非思考工具调用 | 官方示例使用 `deepseek-flash`、`thinking: {"type": "disabled"}`、`tools`、`tool_calls` 和 `role: "tool"` 加 `tool_call_id` | `[文档]` |
| 思考模式工具调用 | 官方说从 DeepSeek-V3.2 起支持；没有给出流式工具调用的细节 | `[文档]` |
| 训练与保留 | 文档根页和 FAQ 没有说明 API 输入是否用于训练，也没有说明请求保留多久 | `[文档]` |
| 专用数据协议 | 前轮调查报告提到官方 API 的专用协议页曾返回 403；本轮未独立复核，也没有在旧仓库的 ADR、任务记录和验证证据中找到对应记录 | `[未实测]` |
| 旧仓库实现 | ADR-0102 通过 Responses API 接入 `https://api.deepseek.com`，模型 `deepseek-v4-flash`；ADR-0140 说 API 把同一个 alias `deepseek-flash` 作为快照返回 | `[旧仓库]` |
| 旧仓库运行证据 | 2026-10-14 hosted 一次文字对话使用 `deepseek / deepseek-v4-flash` 成功；记录只写 endpoint 为 `https://api.deepseek.com` | `[旧仓库]` |

旧仓库的 DeepSeek adapter 调用 `POST {baseUrl}/responses`。当前官方文档存在独立的 Responses API 页面，因此不能再说“官方未文档化 Responses”。旧实现的具体 base、字段、工具和流式处理仍需按当前页面复核，不能直接照搬。v2 推荐统一使用 Chat Completions 的理由是主路径 Go 本身就是 OpenAI-compatible Chat Completions，一套适配更容易覆盖两条路线；这不是因为官方缺少 Responses。

## 不能从现有证据推出的结论

1. **Go 的 `deepseek-v4.1-flash` 与官方的 `deepseek-flash` 不是已证明的同一快照。** 官方 alias 当前指向 `DeepSeek-V4.1-Flash-1017`，Go 文档只写模型 ID。相同名称家族不能证明相同权重、相同参数默认值或相同行为。
2. **Go 的“不用于训练、0 天保留”不能迁移到官方 API。** 两者是不同服务、不同条款。
3. **官方 API 的训练与保留仍是 unknown。** 前轮报告中的 403 线索只说明当时没有读到条款，不说明官方会用数据训练，也不说明不会；本轮没有独立复核该页。
4. **回传 `reasoning_content` 是思考模式加工具时的协议要求，不是产品要永久保存推理。** 文档要求在多轮工具请求中回传。这不等于把它写进 canonical 历史、展示给用户或长期保留。
5. **文档不等于实测。** 本次没有发送真实请求，无法确认当前账号可用性、实际返回的 `model` 字符串、工具调用流式形状或额度用尽时的错误。
6. **Go 的编码 agent 用途既不是许可，也不是禁令。** 非编码私人应用能否长期使用，需要看 OpenCode 的账号条款和实际运行，不能从文档用途一句话推出。
7. **文档根页导航缺少某一项，不等于该 API 未文档化。** Responses API 有独立页面；判断某个接口是否存在，应定点读取对应页面或官方索引，不能只依据根页导航。

## 对阶段 1 和阶段 2 的直接影响

### 传输协议

两条路线默认都应使用 Chat Completions。Go 文档明确是 OpenAI-compatible Chat Completions；官方既文档化了 Chat Completions，也有独立的 Responses API 页面。统一 Chat Completions 的理由是主路径 Go 使用它，v2 可以用一套请求、流式和错误适配覆盖两条路线，减少分叉；不是因为官方缺少 Responses。旧仓库的 Responses 实现是历史证据；若阶段 2 或后续要采用 Responses，需按当前页面重新核对 base、字段、流式事件和工具行为。

### Provider 身份与运行记录（工程建议）

`[建议]` 把 `opencode-go` 和 `deepseek` 做成两个诚实的 Provider 身份，而不是一个可以换 base URL 的配置。理由是 endpoint、模型 ID、快照语义、ZDR、额度和错误形状都不同。一个身份会把这些差异压进同一份运行记录，之后难以解释一次失败来自哪条路线。这是实现取舍，不需要 Luke 拍板；最终方案在 working spec 和 ADR 中记录。

### 返回模型记录（工程建议）

`[建议]` 在运行记录中保存每次返回的 `model`，便于解释实际走的是哪条路线、哪个 alias。官方 alias 更新与快照语义文档未说明；Go 返回的模型字符串也未实测。记录返回模型属于工程常规，不是产品决定。是否 pin alias、是否把返回模型与预期不一致当作失败阈值，属于工程研究，待 working spec 决定。

Go 文档写明，额度用尽后可以改用免费模型，或在启用 Extra usage 时回退到按量付费。这句话描述的是服务提供的选项，不能推出“固定 `model` 的请求会自动换模型”。固定请求在额度用尽时是否换模型、返回什么错误，文档没有说明，属于 unknown。

### 错误映射

官方错误码大多能映射到应用已有的类别：401 到 `authentication`，422 到 `configuration`，429 到 `rate_limited`，500 和 503 到 `unavailable`，请求超时到 `timeout`，截断或协议不完整到 `invalid_response`。402 是账户余额不足，现有类别里没有对应项，应单独显示，不要归入 `configuration`。Go 的额度用尽错误形状没有文档，不能提前假定它等于 429 或 402。

### 思考内容

`[建议]` 不把 `reasoning_content` 放进 canonical 历史，也不在运行详情里展示。若阶段 2 的工具循环需要多步调用，就在一次运行的内存状态里保留它，用于同一请求链的回传。进程丢失后无法回传时，明确失败，不伪造推理。

文档要求回传的场景是思考模式加工具的多轮请求。至于“只做一次工具调用后不带工具续写”能否避开这个要求，没有实测证据，不作为建议。旧仓库这样做过，但那只说明旧实现当时能跑，不构成协议依据。

### 旧 endpoint 不要照搬

旧仓库固定使用 `https://opencode.ai/zen/go/v1/chat/completions`。当前文档列的是 `https://opencode.ai/inference/go/openai/v1/chat/completions`。v2 不应直接复制旧常量。应以当前文档为准，并把旧路径当作历史证据。

## Fallback 建议（方向已授权，具体落地待 working spec）

Luke 已明确 OpenCode Go 为主路径、DeepSeek 官方 API 为 fallback。以下是自动切换的工程建议，不是新增授权要求。阶段 1 和阶段 2 如何安排（主路径先接、fallback 何时进入请求路径、是否自动切换、用户如何看到切换）在 working spec 中写清，不重复确认已授权方向。

| 时点与错误 | 建议行为 | 理由 |
| --- | --- | --- |
| 首个可见输出之前：超时、429、5xx、额度用尽、响应截断或协议不完整、返回模型与预期不符 | 允许一次自动切换到另一条路线，复用同一请求，新建 attempt 记录 | 用户还没有看到内容，切换不会产生两份回答 |
| 首个可见输出之前：401、403 | 不自动切换，显示认证或配置错误 | 切换会掩盖凭据或账号问题 |
| 首个可见输出之前：402 或余额不足 | 不自动切换，显示余额错误 | 换一条路线可能同样失败，且会隐藏计费问题 |
| 首个可见输出之前：400、422 | 不自动切换 | 同一个无效请求换路线仍会失败 |
| 已有任何可见输出之后 | 不自动切换；把本轮标为中断，保留已显示内容，由用户决定是否重新生成 | 自动切换会产生第二份回答、人格跳变和重复历史 |
| 已经切换过一次 | 不再级联到第三条路线，不静默改模型，不自动启用额外计费 | 有界失败比无界扩散更容易解释 |

这个建议与旧仓库 ADR-0059 的“可见输出前才允许 fallback handover”一致，但旧 ADR 不是 v2 的接受依据。自动切换是否对用户可见、切换时如何提示，属于用户可见行为，是阶段 0 要确认的偏好；具体触发条件和错误映射属于工程建议。

## 建议的最小验证（均未执行）

执行前提：凭据就绪；执行符合当前会话授权与本地规范；不读取密钥；未获访问真实私密内容授权时，只使用合成提示和合成工具；记录 endpoint、返回的 `model`、HTTP 状态、`finish_reason`、usage、是否出现 `reasoning_content` 和时延；遇到认证或计费错误立即停止，不盲目重试。本轮不读取密钥、不调用。

### V1：确认 Go 当前 endpoint 与模型身份

- 做法：向文档列出的 `https://opencode.ai/inference/go/openai/v1/chat/completions` 发送一次极短的合成请求，`max_tokens` 设小，使用真实 SayHear user agent 和不透明 session。
- 调用数：1 次。
- 能证明：当前 key 可用，文档 endpoint 可用，返回的 `model` 字符串，SSE 是否以 `[DONE]` 结束，usage 字段是否存在。
- 不能证明：非编码用途被允许，回复质量，工具循环，额度用尽行为，旧 `zen` 路径是否仍可用。

### V2：确认官方 fallback 的 Chat Completions 与工具形状

- 做法：向 `https://api.deepseek.com/chat/completions` 发送一次合成请求，模型用 `deepseek-flash`，关闭思考模式，带一个无副作用的合成工具定义，观察 `tool_calls` 和 `tool_call_id` 的形状。
- 调用数：1 次，必要时 2 次完成工具结果回传。
- 能证明：当前 key 和余额可用，alias 是否可用，返回的 `model` 字符串，非思考工具调用是否符合文档。
- 不能证明：思考模式下的工具行为，流式工具调用，训练或保留条款，Responses API 的字段细节。

### V3：确认思考模式加工具时的 `reasoning_content` 回传

- 做法：在一条路线上做两轮合成工具调用。第一轮带工具并启用思考，第二轮回传第一轮的完整 `reasoning_content`，观察是否成功、工具参数是否连贯。
- 调用数：2 到 3 次。
- 能证明：该路线在回传完整 `reasoning_content` 后能继续，返回内容与工具参数的基本形状。
- 不能证明：缺少回传时是否报错或退化（没有负向用例），长工具循环的稳定性，跨进程恢复，是否应把推理写入 canonical，另一条路线的相同行为。

三项合计约 4 到 6 次调用。这个数字是验证计划，不是审批门槛或月预算。

## 尚未调查

- DeepSeek 官方 API 的专用数据协议页。前轮调查报告提到先前 403，本轮未独立复核，也没有找到可复核记录。
- 官方 Responses API 的 base URL、工具/推理字段和流式事件细节。页面已确认存在，但未逐项复核。
- OpenCode 的账号条款是否允许非编码私人应用长期使用。
- Go 背后的实际模型快照和权重。
- Go 额度用尽时的具体错误码、响应形状，以及固定 `model` 请求是否自动换模型。
- 官方 API 的流式工具调用细节。
- 旧 `zen` endpoint 是否仍可用。
- Go 支持的 `reasoning_effort` 取值是否与官方一致。
- WorkBuddy。它不在本次两条路线内。
- 价格和月预算。Luke 已表示暂不设月预算，本文件不重新提出。

## 来源

前轮调查读取了以下官方页面；本轮为修正 Responses 结论，定点补读了 Responses API 页面。官方页面是滚动文档，接入时应重新核对。

- [OpenCode Go](https://opencode.ai/docs/go/)
- [DeepSeek 模型列表](https://api-docs.deepseek.com/quick_start/models)
- [DeepSeek 思考模式](https://api-docs.deepseek.com/guides/thinking_mode)
- [DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls)
- [DeepSeek Chat Completions 参数](https://api-docs.deepseek.com/api/create-chat-completion)
- [DeepSeek Responses API](https://api-docs.deepseek.com/api/create-response)（本轮补读）
- [DeepSeek 错误码](https://api-docs.deepseek.com/quick_start/error_codes)
- [DeepSeek API 文档根页](https://api-docs.deepseek.com/)
- [DeepSeek FAQ](https://api-docs.deepseek.com/faq)

旧仓库证据：

- `/Users/lukemyself/Projects/SayHear/docs/adr/0147-g1-opencode-go-provider.md`
- `/Users/lukemyself/Projects/SayHear/docs/tasks/g1-opencode-go-provider-20261004.md`
- `/Users/lukemyself/Projects/SayHear/docs/tasks/g1-token-profile-20261004.md`
- `/Users/lukemyself/Projects/SayHear/docs/adr/0140-g1-deepseek-model-alias-is-pinned-evidence.md`
- `/Users/lukemyself/Projects/SayHear/docs/adr/0102-deepseek-joins-openai-as-a-conversation-text-provider-in-1a1.md`
- `/Users/lukemyself/Projects/SayHear/docs/adr/0059-text-fallback-handover-precedes-visible-output.md`
- `/Users/lukemyself/Projects/SayHear/packages/ai/src/opencode-go-conversation-text-model.ts`
- `/Users/lukemyself/Projects/SayHear/packages/ai/src/responses-api-conversation-text-model.ts`
- `/Users/lukemyself/Projects/SayHear/apps/web/src/runtime-config.ts`
- `/Users/lukemyself/Projects/SayHear/docs/verification/README.md`
- `/Users/lukemyself/Projects/SayHear/docs/verification/evidence/hosted-execution-proof.json`
- 旧仓库提交 `8ac39ba`（2026-10-04，OpenCode Go provider）

## 首次真实数据前的核对项（不是现在要做的决定）

以下事项在第一次把真实私人内容发给任一 Provider 之前核对，不阻塞当前用合成数据做调研和工程验证：

- Go 的 ZDR 协议按月续签，当前有效期到 2026-10-31。续期未到，本轮不预设未续期分支；首次真实数据前确认是否续期及条款状态。
- 官方 API 的训练与保留条款。前轮报告称专用协议页曾返回 403，本轮未独立复核；首次真实数据前读取该页或等价官方说明。
- OpenCode 的账号条款是否允许非编码私人应用长期使用。
- Go 额度用尽时的实际错误形状，以及固定 `model` 请求是否会自动换模型。
- 真实内容会发送到哪条路线、运行记录保存哪些字段，确保与 Luke 确认的数据边界一致。

## 阶段 0 需要 Luke 确认的偏好

以下只涉及用户可见行为和数据边界，不需要 Luke 决定内部实现细节。

1. **自动 fallback 的用户可见行为。** 首个可见输出之前自动切换到另一条路线，是否接受；切换时是否向用户提示；已有可见输出之后是否只标中断、不自动切换。若不接受自动切换，就退回手动重试或只做阶段 2 的替换验证。
2. **真实内容外送的数据边界。** 官方 API 的训练与保留仍是 unknown，Go 的非编码私人用途尚未确认，ZDR 续期待核对。需要确认哪些路线可以接收真实私人内容。可选：只用于合成验证；允许真实内容并记录 unknown；暂不发送真实内容。不要求现在回答 ZDR 未续期的灾难分支；首次真实数据前按上一节核对。

以下由工程研究给出建议，不需要 Luke 拍板：

- 两条路线做成两个 Provider 身份，还是一个 Chat Completions adapter 加两份配置。
- alias、pin 语义和返回 `model` 的记录方式。
- `reasoning_content` 的回传实现，以及 canonical 是否保存推理。
- 错误码到应用类别的映射细节。

这些偏好确认后，写入阶段 0 的 working spec，并在实现前形成 ADR。本文件只提供证据和建议，不替这些决定背书。
