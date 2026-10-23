---
status: accepted
---

# Provider 分阶段：自用阶段 OpenCode Go 为主，fallback 可替换并允许承载真实对话

Luke 于 2026-10-22 确认：只有 Luke 本人使用的阶段，OpenCode Go 为主 Provider，DeepSeek 官方 API 为 fallback；Go 故障时真实对话允许自动切换到 fallback。fallback Provider 可替换，DeepSeek 是当前选项而非固定依赖。

OpenCode 服务条款（2026-08-15 生效）写明 "You will only use the Services for your own internal use, and not on behalf of or for the benefit of any third party"。因此邀请其他用户前必须重新选择主 Provider。证据见 [Provider 条款证据](../plans/stages/stage-0/evidence/stage-0-provider-terms-evidence.md)与 [Provider 证据](../plans/stages/stage-0/evidence/stage-0-provider-evidence.md)。

## 取舍与边界

Go 对 DeepSeek V4.1 Flash 写明不用于训练、保留 0 天，但依赖按月续签的 ZDR 协议，当前有效期到 2026-10-31，上游托管方未公开。DeepSeek 官方 API 允许衍生产品开发，但 API 数据是否用于训练与保留期限为 unknown，数据存储在中国境内，无 ZDR 与 DPA。Luke 接受自用阶段真实对话经 fallback 外送的风险。

Provider 实现为相互独立的 Provider 身份，不做可换 base URL 的单一配置；运行记录标明每次请求实际使用的 Provider。自动切换的触发条件、切换时机与用户提示在阶段 1 SPEC 中确定。

## 重评条件

邀请 Luke 以外的用户前，重选主 Provider 与 fallback，并按当时条款确认真实内容外送边界与隐私告知。Go 的 ZDR 未续期或条款变化时，复核 Luke 本人真实对话是否继续走 Go。
