# 阶段 0 Provider 条款证据：真实私人内容可以发往哪个 LLM Provider

核验日期：2026-10-22。只读调研，未调用任何 Provider API，未读取或打印任何凭据，未提交 git。

本文件只补条款与数据边界证据，不改写 [`stage-0-provider-evidence.md`](stage-0-provider-evidence.md) 的结论，也不改变 Luke 已授权的方向（Go 主路径、DeepSeek 官方 API 为 fallback、目标模型 DeepSeek V4.1 Flash）。

## 证据等级

| 标记 | 含义 |
| --- | --- |
| `[文档]` | 官方页面当时写明的原文，含链接与核验日期 |
| `[推断]` | 从 `[文档]` 推出的判断，可被反驳 |
| `[unknown]` | 一手资料未给出答案，或页面打不开、被拒 |

官方页面是滚动文档，接入前应重新核对。

## 问题 1：OpenCode Go 的 ZDR 与 DeepSeek V4.1 Flash 条款

来源：[OpenCode Go 文档 Privacy 一节](https://opencode.ai/docs/go/)（核验 2026-10-22，页面无 last-updated 元数据）

原文：

> "DeepSeek V4.1 Flash | Not used | 0 days\*"（Privacy 表 Model / Model training / Data retention 三列）
> "DeepSeek: ZDR agreement is renewed monthly. The current agreement is valid through October 31, 2026."

| 问题 | 结论 | 等级 |
| --- | --- | --- |
| ZDR 有效期是否仍到 2026-10-31 | 是，页面仍写 "valid through October 31, 2026" | `[文档]` |
| 是否有续期公告 | 没有。页面没有"已续期""新有效期"字样；[changelog](https://opencode.ai/changelog) 2026-10-22 的最新条目也只涉及免费模型开关与 Go session 头，未提 ZDR、DeepSeek 或保留期 | `[文档]` |
| DeepSeek V4.1 Flash "不用于训练、保留 0 天"是否仍成立 | 是。Privacy 表仍标 Not used / 0 days\*，脚注只有上述 DeepSeek 按月续签一句；星号未在页面内显式定义指向哪条脚注 | `[文档]` |
| 上游由谁托管 | OpenCode 未点名托管方。原文只说 "We worked with a few providers to make sure these were being served correctly" 与 "For most models, we make this work through bulk discounts and reserved GPU capacity" | `[unknown]` |
| 条款是否覆盖上游 | ToS 把上游责任显式排除：见问题 2 的 Third Party Model 原文 | `[文档]` |

关键判断：ZDR 承诺是 OpenCode 与上游之间的协议（"ZDR agreement is renewed monthly"），不是用户与 OpenCode 之间的合同义务。页面把有效期写成一个会过期的日期，说明它是一份按月重签的商业安排，不是一个稳定承诺。今天（2026-10-22）仍在有效期内，剩 9 天；页面没有承诺 11 月自动续签，也没有提供任何订阅或查询渠道。`[推断]`

补充：[OpenCode Zen 隐私页](https://opencode.ai/docs/zen/)（核验 2026-10-22）给出更细的默认规则：付费 DeepSeek V4.1 Flash 与 V4 Pro 不在"例外列表"中，适用 "Our providers follow a zero-retention policy and do not use your data for model training"；只有 `DeepSeek V4.1 Flash Free` 单独列了一条同样表述。也就是说 Go 与 Zen 对 DeepSeek 的保留表述一致。`[文档]`

## 问题 2：OpenCode 服务条款是否限制为编码用途

来源：[Terms of Use](https://opencode.ai/legal/terms-of-service)（Effective date: Aug 15, 2026；核验 2026-10-22）

原文：

> "What is OpenCode? OpenCode is an AI-powered coding agent that helps you write, understand, and modify code using large language models."
> "You will only use the Services for your own internal use, and not on behalf of or for the benefit of any third party, and only in a manner that complies with all laws that apply to you."
> "If you use OpenCode with Third Party Models, then your Content will be subject to the data retention policies of the providers of such Third Party Models. Although we will not retain your Content, we cannot and do not control the retention practices of Third Party Model providers."
> "OpenCode has no control over, and assumes no responsibility for, the content, accuracy, privacy policies, or practices of any providers of Third Party Models."

来源：[OpenCode Go 文档 Where can I use it?](https://opencode.ai/docs/go/)（核验 2026-10-22）

原文：

> "OpenCode Go is designed for OpenCode and other coding agents that produce similar types of requests. Traffic is monitored for abuse that degrades the experience for other users."
> "Send typical coding agent traffic"
> "Go and Go Plus are for workspaces with a single member"

来源：[Privacy Policy](https://opencode.ai/legal/privacy-policy)（Effective date: Mar 6, 2026；核验 2026-10-22）

原文：

> "Other Identifying Information that You Voluntarily Choose to Provide such as information included in conversations or prompts that you submit to AI | Passing through to upstream provider to provide services | Not stored"

| 问题 | 结论 | 等级 |
| --- | --- | --- |
| 是否限制为编码 agent 用途 | 没有明确的用途限制条款。Go 文档只说 "designed for ... coding agents"，属产品定位描述，不是禁止条款 | `[文档]` |
| 非编码个人聊天应用通过 API 调用是否允许 | 条款未禁止，也未明确许可。Go 文档没有"仅限编码"的措辞，也没有"允许任意应用"的措辞 | `[unknown]` |
| 有没有明确禁止的原文 | 有禁止项但都不针对用途类别：内部使用限制、爬取或批量提取 Output、用 Output 训练竞争模型、给服务施加不合理负载。私人日记聊天不属于其中任何一项 | `[文档]` |
| 最大真实风险 | 不是被条款禁止，而是被运行时限制或判定为异常流量。Go 文档要求客户端 "Send typical coding agent traffic" 并说明 "Traffic is monitored for abuse that degrades the experience for other users"；个人聊天与编码 agent 的请求形状不同（无工具定义、无文件上下文、会话长短与频率不同），是否触发限流或风控没有文档 | `[unknown]` |

对私人陪伴 Agent 的具体影响：Go 明确要求 `x-opencode-session` 发送稳定 session ID 用于"optimize routing and prompt caching"。长期陪伴会话天然是一个超长 stable session，这在语义上与该要求一致，不是滥用。`[推断]`

另一个不可忽略的约束：Go 订阅与单成员 workspace 绑定（"Go and Go Plus are for workspaces with a single member"）。Luke 个人订阅 + 个人陪伴 Agent 与该形态一致；一旦 SayHear 要服务多用户，就需要 Enterprise 或另一路线。`[推断]`

## 问题 3：DeepSeek 官方 API 的隐私与开放平台协议

前轮报告称专用协议页返回 403。本轮重试结果：

| URL | 结果 |
| --- | --- |
| <https://platform.deepseek.com/downloads/DeepSeek%20Privacy%20Policy.html> | HTTP 403（换浏览器 UA 仍 403） |
| <https://platform.deepseek.com/downloads/DeepSeek%20API%20Service%20Agreement.html> | HTTP 403 |
| <https://platform.deepseek.com/> | HTTP 403 |
| <https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html> | HTTP 200，可读 |
| <https://cdn.deepseek.com/policies/zh-CN/deepseek-open-platform-terms-of-service.html> | HTTP 200，可读 |
| <https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html> | HTTP 200，可读 |
| <https://cdn.deepseek.com/policies/zh-CN/deepseek-privacy-policy.html> | HTTP 200，可读 |

`platform.deepseek.com` 整个域名对本环境 403，因此原 403 不是该页内容问题，是域名级访问拒绝。等价的官方政策文件在 `cdn.deepseek.com/policies/` 下可读，本轮全部读到了原文。

### 开放平台服务协议（DeepSeek Open Platform Terms of Service）

来源：<https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html>（Release April 22, 2026；Effective April 29, 2026；核验 2026-10-22）

原文：

> "(3) You may apply the Inputs and Outputs of the Services to a wide range of use cases, including personal use, academic research, derivative product development, training other models (such as model distillation), etc."
> "We will collect and process the personal information you provide as the data subject in accordance with the 'DeepSeek Privacy Policy'. However, when your end users access downstream systems, applications, or functions that you've developed based on the open platform, the processing rules for their collected personal information are not covered by this privacy policy. As the controller of personal information processing activities in that scenario, you should disclose the relevant privacy policy to your end users."
> "For behaviors suspected of violating laws and regulations or involving illegal activities, relevant records will be retained, and reports will be made to the competent authorities in accordance with the law"

中文版对应原文（<https://cdn.deepseek.com/policies/zh-CN/deepseek-open-platform-terms-of-service.html>）：

> "您可将本服务的输入与输出应用于广泛的使用场景中，包括个人使用、学术研究、衍生产品开发、训练其他模型（如模型蒸馏）等"（§4.2(3)）

结论：开放平台服务协议明确规定 Inputs/Outputs 可用于"derivative product development"，即明确允许把 API 输入输出用于衍生产品。SayHear 是衍生产品，用途上被允许。`[文档]`

该协议同时把 SayHear 定为下游用户个人信息的 controller，即 Luke 需要向 SayHear 用户披露隐私政策，并对用户的权利请求（查阅、复制、转移、更正、删除）负责。这不是禁止，是一项合规义务。`[文档]`

### 隐私政策（DeepSeek Privacy Policy）

来源：<https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html>（Last Update: Feb 10, 2026；核验 2026-10-22）

原文：

> "To improve and develop the Services and to train and improve our technology, such as our machine learning models and algorithms."
> "the right to opt-out of using your Personal Data for training our models or optimizing our technologies."
> "We retain Personal Data for as long as necessary to provide our Services and for the other purposes set out in this Privacy Policy."
> "we directly collect, process and store your Personal Data in People's Republic of China."
> "The Personal Data we collect from you may be stored on a server located outside of the country where you live."
> "For end users of developer-built applications, the processing rules ... are not covered by this privacy policy."

中文版（<https://cdn.deepseek.com/policies/zh-CN/deepseek-privacy-policy.html>，更新/生效 2026-02-10）：

> "我们可能会将服务所收集的输入及对应输出，用于DeepSeek模型训练和服务的优化。"（该句出现在智能对话服务小节，前提是"在经安全加密技术处理和去标识化前提下"）
> "如您拒绝将您的数据用于模型训练，可以在产品内通过关闭'数据用于优化体验'来选择退出，关闭后您的输入和输出不会再用于我们的模型训练。"
> "我们仅在为提供DeepSeek之目的所必需的期间内保留您的个人信息。"
> "我们依照法律法规的规定，将在境内运营过程中收集和产生的您的个人信息存储于中华人民共和国境内。""目前，我们不会将上述信息传输至境外"
> "留存相关的网络日志不少于六个月"

| 问题 | 结论 | 等级 |
| --- | --- | --- |
| API 输入/输出是否用于训练 | 无法从官方文件确认"是"或"否"。隐私政策把"输入及对应输出用于模型训练"写在智能对话服务语境下，并指向产品内开关；开放平台服务协议与 API 文档（[api-docs.deepseek.com](https://api-docs.deepseek.com/) 全站，含 [Your First API Call](https://api-docs.deepseek.com/)、[Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing)、[Chat Completions 参数](https://api-docs.deepseek.com/api/create-chat-completion)、[Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit)）都没有 API 训练条款 | `[unknown]` |
| 保留多久 | 无 API 保留期。隐私政策只给"必要期间"的通用规则，并给"网络日志不少于六个月"的法定下限；开放平台协议只承诺违法违规记录依法保留 | `[unknown]` |
| 存储地 | 中国境内。隐私政策中文版明确"存储于中华人民共和国境内"且"目前不会传输至境外"；英文版同义 | `[文档]` |
| 是否可申请不保留 | 有面向产品内对话的 opt-out 开关（关闭"数据用于优化体验"），但没有 API 侧的 opt-out、没有 ZDR 或专用数据协议、没有 DPA 可供申请 | `[unknown]` |
| 用户协议（对话服务）侧 | [DeepSeek 用户协议](https://cdn.deepseek.com/policies/zh-CN/deepseek-terms-of-use.html)（2025-09-05）允许在去标识化前提下用输入输出训练，并给出同一 opt-out 开关；但这是对话服务协议，不是 API 条款 | `[文档]` |

本轮读到的与之前"403"线索不同的东西：官方确实存在一套完整的政策文件，只是托管在 `cdn.deepseek.com/policies/`，`platform.deepseek.com/downloads/` 对本环境 403。之前"专用协议页 403"的记录可以更新为"域名级 403，等价页面已读到"。但这些文件都没有回答 API 训练与保留。`[文档]`

一个值得记下的反向证据：Go 的 Privacy 表把 DeepSeek V4.1 Flash 标为 "Not used / 0 days\*"，且脚注说这是按月续签的 ZDR 协议。如果 DeepSeek 官方 API 默认不训练，OpenCode 无需单独签一份 ZDR 协议。`[推断]`

## 问题 4：两条路线可以接收真实私人内容的证据强度

| 路线 | 训练 | 保留 | 用途许可 | 能否接收真实私人内容 |
| --- | --- | --- | --- | --- |
| OpenCode Go（`deepseek-v4.1-flash`） | Not used，`[文档]` | 0 天，`[文档]`，但依赖按月续签的 ZDR 协议，2026-10-31 到期 | 未禁止，也未明确许可；受运行时流量监控约束，`[unknown]` | 弱到中等。隐私条款当前有利，用途条款不明确，ZDR 9 天后到期 |
| DeepSeek 官方 API（`deepseek-flash`） | unknown，`[unknown]` | unknown，`[unknown]` | 明确允许衍生产品，`[文档]`；Luke 作为 controller 有披露义务，`[文档]` | 最弱。训练与保留两个核心问题都没有官方答案，且存储在中国境内 |

### 剩余 unknown 会影响什么

1. **Go 的 ZDR 未续期（2026-10-31 之后）。** 影响：Go 的隐私承诺整段失效。到期前不预设分支，到期后应重读 Go 页面确认新有效期或是否降级为 30 天 / 参与训练。这是时间敏感项，建议在 10-31 前或刚过 10-31 时复查一次。
2. **Go 的上游托管方未点名。** 影响：无法判断数据实际经过哪些第三方。ToS 明确 OpenCode 不控制也不为 Third Party Model provider 的保留实践负责，因此 ZDR 的具体执行方不可从合同角度追索。
3. **Go 的非编码用途合规性。** 影响：不是立即的法律风险，而是账号级风险（限流、风控、封号）。`x-opencode-session` 与 user agent 要求照文档做可以降低风险，但不能消除。若 SayHear 要给多个用户使用，还会撞上单成员 workspace 限制。
4. **DeepSeek 官方 API 的训练与保留。** 影响：无法回答"用户情绪与私人生活内容会不会进模型训练、会不会被长期留存、存在哪里"。这直接影响 SayHear 能否对用户承诺隐私。在上游给出 API 侧书面答复（例如通过 api-service@deepseek.com）之前，这条路线不适合承载真实私人内容。
5. **DeepSeek 存储在中国境内。** 影响：跨境数据合规。若 SayHear 的用户在中国境外，这一点需要单独评估；若只在中国境内使用，这一点不构成额外障碍。

## 建议（`[建议]`，不是 Luke 已接受的决定）

- 阶段 0 到阶段 2 的合成数据验证两条路线都可以用。
- 真实私人内容在 ZDR 续期确认（10-31 之后重读 Go 页面）之前，只走 OpenCode Go。
- DeepSeek 官方 API 保持 fallback 身份，用于合成数据与工程验证；在拿到 API 侧关于训练与保留的书面答复之前，不承载真实私人内容。
- 把"ZDR 有效期"作为运行记录里的一个字段，而不是一次性假设。

## 来源

全部为官方一手资料，核验日期 2026-10-22。

- [OpenCode Go](https://opencode.ai/docs/go/)
- [OpenCode Zen](https://opencode.ai/docs/zen/)
- [OpenCode Terms of Use](https://opencode.ai/legal/terms-of-service)（Effective date: Aug 15, 2026）
- [OpenCode Privacy Policy](https://opencode.ai/legal/privacy-policy)（Effective date: Mar 6, 2026）
- [OpenCode Changelog](https://opencode.ai/changelog)
- [DeepSeek API Docs](https://api-docs.deepseek.com/)
- [DeepSeek Your First API Call](https://api-docs.deepseek.com/)
- [DeepSeek Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [DeepSeek Chat Completions 参数](https://api-docs.deepseek.com/api/create-chat-completion)
- [DeepSeek Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit)
- [DeepSeek Open Platform Terms of Service（英文）](https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html)（Effective April 29, 2026）
- [DeepSeek 开放平台服务协议（中文）](https://cdn.deepseek.com/policies/zh-CN/deepseek-open-platform-terms-of-service.html)
- [DeepSeek Privacy Policy（英文）](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html)（Last Update: Feb 10, 2026）
- [DeepSeek 隐私政策（中文）](https://cdn.deepseek.com/policies/zh-CN/deepseek-privacy-policy.html)
- [DeepSeek 用户协议（中文）](https://cdn.deepseek.com/policies/zh-CN/deepseek-terms-of-use.html)

打不开的官方页面（如实记录，不用二手资料替代结论）：

- <https://platform.deepseek.com/>：HTTP 403
- <https://platform.deepseek.com/downloads/DeepSeek%20Privacy%20Policy.html>：HTTP 403
- <https://platform.deepseek.com/downloads/DeepSeek%20API%20Service%20Agreement.html>：HTTP 403
- <https://static.deepseek.com/faq/index.html?lang=en#/category/4>：可访问但正文为空（JS 渲染），未取到内容
- <https://api-docs.deepseek.com/faq>：仅重定向到上述 FAQ，无内容
