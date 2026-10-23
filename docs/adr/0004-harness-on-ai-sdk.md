---
status: accepted
---

# Harness 直接基于 AI SDK 构建，不采用 Mastra 的 Agent 与 Memory

SayHear 的学习目标是理解并掌控 Harness：模型上下文如何组成，原始消息、AI 推断与来源如何关联，错误来自哪一层。Luke 于 2026-10-22 确认采用 AI SDK（`ai` 与 `@ai-sdk/openai-compatible`），对话循环、上下文组装、历史与记忆的存取、重试与 fallback 由 SayHear 自己实现。Mastra 可行，本地 mock 中非流式、流式中止、工具步数限制均可工作，但其 Memory 自带存储结构，会与 SayHear 的 canonical 数据模型形成两套事实来源，且框架层的重试与遥测默认值需要额外关闭和理解。

证据见[运行层本地验证](../plans/stages/stage-0/evidence/stage-0-runtime-validation.md)与[运行层调研](../plans/stages/stage-0/evidence/stage-0-runtime-evidence.md)。

## 取舍与边界

工具循环、历史截断、重试与运行记录需要自行实现，早期进度较慢。实现时须遵守已实测的行为：系统提示走顶层 `system`，不能放入 `messages`；裸 `streamText` 与 `generateText` 默认只执行 1 步，工具循环需显式 `stopWhen`；SDK 默认重试与应用层 fallback 不得叠加，阶段 1 设 `maxRetries: 0`；中止须结合取消信号和 SDK 终态事件判断；[真实链路验证](../plans/stages/stage-0/evidence/stage-0-live-provider-validation.md)观察到 `fullStream` 的 `abort` 事件，不能假定所有消费方式都会向调用方抛 `AbortError`。

AI SDK 提供每步实际发送的 `request.messages` 与 HTTP `request.body`、`onStepFinish` 与 `onFinish` 回调，以及默认记录输入输出的遥测接口；它不持久化记录，也不知道 SayHear 为什么选中或遗漏某条记忆。运行详情由 SayHear 自行保存与展示。

## 重评条件

出现需要持久化、可恢复的长流程编排，且自建成本明显高于引入外部编排组件时，评估只引入 Mastra Workflow 或其他编排工具，不整体替换 Harness。本地验证基于 `ai@7.0.148`，真实 Provider 与 Vercel 运行时行为尚未验证。
