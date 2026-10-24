---
status: accepted
---

# Web 框架采用 Next.js App Router（Node runtime），以三条护栏约束续期、缓存与入口

阶段 1 需要选定 Web 框架，以承载登录与 cookie 会话（[ADR 0011](0011-stage-1-login-lifecycle.md)）、用户令牌访问 Data API（[ADR 0009](0009-server-data-access-and-rls.md)）和流式聊天（[ADR 0006](0006-chat-time-budgets.md)），并部署在 Vercel `iad1`（[ADR 0002](0002-hosting-region.md)）。Luke 于 2026-10-24 接受。

## 决定

- 采用 Next.js App Router，服务端代码在 Node runtime 运行。版本在实施时锁定，`@supabase/ssr` 也锁定版本（Issue #1）。
- 复用 v1 只复用外观和交互设计：视觉规则与尺寸、DOM 结构、交互状态机、设计契约测试，以及视觉验收脚本。不直接搬用完整页面代码。登录、会话、数据装载、流式事件协议须按 v2 的决定重建。

## 三条护栏

1. **续期只在能写 cookie 的地方做。** 续期和 Set-Cookie 只能出现在 Proxy 与 Route Handler 中；Server Component 只读数据，不承担续期。原因：Server Component 写不了 cookie，官方模板还会吞掉写入错误。续期因此会在服务端悄悄成功，新令牌却送不回浏览器。浏览器下次带着已轮换的旧 refresh token 来请求，可能导致会话被撤销，表现为偶发被登出，很难复现。
2. **私人页面不缓存。** 读写私人数据的页面和接口一律动态渲染，并在响应上设置 `Cache-Control: private, no-store`（与 ADR 0011 一致）。不依赖框架缓存的默认值，必须在验收中检查。
3. **入口要薄。** 聊天主链路（`getUser()` 确认会话 → 必要时续期 → 原子写 → 返回流式响应）放在不依赖框架的服务端模块中，只接收标准 `Request`、返回标准 `Response`。Route Handler 只负责转交。业务核心不调用 Next 专有 API。

## 选项与取舍

| 选项 | 优势 | 代价 |
| --- | --- | --- |
| Next.js App Router（采用） | Supabase 官方 SSR 指南与 AI SDK 示例最多，便于 agent 实现、也便于 Luke 查资料；Vercel 一等支持；v1 同栈，设计迁移阻力小 | 规则较多：哪类组件能写 cookie、缓存默认值；升级时曾改缓存默认值、将 middleware 改名为 proxy |
| React Router framework mode | 在 loader 一处完成续期与读取，心智模型直观，没有 RSC 缓存这一类风险 | 范例较少，遇到问题更多依赖自行推理；Vercel 支持次于 Next；framework mode 较新 |
| Vite React SPA + Node API | 前后端边界最清楚，私人应用不需要 SEO | 首屏须先加载再请求数据，需要自行组织路由、会话与部署；与 v1 结构差异最大 |

两者在发送消息和流式回复上的写法基本相同；差别集中在打开页面这一步，即在哪里续期、在哪里读首屏数据。AI SDK 的 `useChat` 通过 HTTP 通信，与框架耦合低。300 秒上限来自 Vercel 套餐，不是框架限制。`after()` / `waitUntil` 不是耐久后台任务。

## 迁移成本

只要守住护栏 3，日后更换框架时，需要重写的只有页面加载层（续期位置与首屏数据）和路由入口；聊天主链路、数据库函数、RLS 与验收用例都可以整体保留。

## 实施期验证

- 锁定版本的 Next 与 `@supabase/ssr` 中，Proxy 续期会回写 cookie，Server Component 中不会出现续期写入。
- 私人页面与接口的响应头不可缓存；A/B 两个合成主体交替访问时，不串用身份，也不命中对方的缓存（ADR 0013）。
- 流式响应开始前完成续期，且响应带有新 cookie（ADR 0009 与[流式令牌核查](../plans/stages/stage-1/features/identity-data-ownership/evidence/streaming-token-lifetime-evidence.md)）。

## 重评条件

Next 升级使续期或缓存的约定无法用锁定方式维持；护栏 1、2 反复被违反，或其验收成本明显高于收益；Vercel 套餐或运行时限制迫使服务端迁出；React Router 等替代方案在 Supabase/AI SDK 上获得同等成熟的官方范例，而当时恰有迁移需求。

依据：本次会话中关于 v1 前端耦合、候选框架能力的两项调研，以及“打开聊天页→发送消息”的对照讲解。调研报告没有单独存入 evidence；采用其中的版本细节前须重新核对。
