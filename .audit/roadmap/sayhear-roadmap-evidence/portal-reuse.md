# 旧 Portal UI 复用可行性

只读调查。对象是 `/Users/lukemyself/Projects/SayHear`（旧仓库，HEAD `cce52bb`）的 Internal Portal。结论针对 `CONTEXT.md:49`：复用聊天 UI 与交互，Journal Tab 暂不实现，运行详情按需重设计，旧 API、事件协议和会话模型按 v2 适配。

## 结论

可行，但“复用”必须限定为三件事：交互设计与视觉规则、四个纯逻辑模块、聊天相关的 CSS 子集。直接搬运组件树会把 Daily Session、next-auth、Journal、Inspector 和 recovery gate 一起带进 v2。

旧聊天界面的真实耦合面很窄：一个 NDJSON 流端点、一个读取契约、一个会话守卫，外加消息上的 Inspector 深链。真正宽的是外壳，而 v2 第一阶段只需要外壳中的聊天切片。

## 技术栈与路径

| 项 | 事实 | 位置 |
| --- | --- | --- |
| 框架 | Next.js 16.2.12 App Router，React 19.2.8 | `/Users/lukemyself/Projects/SayHear/apps/web/package.json` |
| 语言 | TypeScript 7.0.2，`jsx: preserve` | `/Users/lukemyself/Projects/SayHear/apps/web/tsconfig.json` |
| 鉴权 | next-auth 4.24.15，GitHub OAuth，database session | `/Users/lukemyself/Projects/SayHear/apps/web/src/auth.ts` |
| 样式 | 单文件全局 CSS，无 Tailwind、无 CSS Modules、无组件库、无深色模式 | `/Users/lukemyself/Projects/SayHear/apps/web/app/styles.css`（2433 行） |
| 部署 | Vercel，Workflow SDK | `/Users/lukemyself/Projects/SayHear/apps/web/next.config.ts` |
| 设计源 | 仓库内没有设计稿，只有 `.spec275-review/sidebar-*.png` 两张侧栏截图；已批准设计的事实载体是 CSS 与提交 `3e1fbec` 的说明 | `/Users/lukemyself/Projects/SayHear/apps/web/app/styles.css` |

### 文件规模

| 区域 | 文件 | 行数 |
| --- | --- | --- |
| 聊天容器 | `app/internal/text-conversation.tsx` | 1034 |
| 聊天纯逻辑 | `app/internal/text-conversation-state.ts` | 320 |
| 消息展示 | `app/internal/message-time.tsx` / `message-time-presentation.ts` | 240 / 193 |
| 历史只读 | `app/internal/history-conversation.tsx` | 299 |
| 外壳 | `app/internal/portal-shell.tsx` | 510 |
| 外壳辅助 | `portal-integration.ts` / `portal-write-status.ts` / `portal-date-format.ts` / `portal-conversation.ts` | 184 / 75 / 37 / 61 |
| 日期列表 | `app/internal/chat-module-list.tsx` | 157 |
| 服务端页面 | `app/internal/layout.tsx` / `page.tsx` | 59 / 114 |
| Journal | `journal-card.tsx` / `journal-date-list.tsx` / `journals/page.tsx` | 291 / 182 / 70 |
| 运行详情 | `context-inspector.tsx` + data / `reflection-inspector.tsx` / `candidate-review.tsx` | 1255+473 / 1921 / 782 |

所有路径前缀为 `/Users/lukemyself/Projects/SayHear/apps/web/`。

## 与旧 API、事件、会话和 Journal 的耦合

### 流式协议

客户端只调用两个写入端点，`POST /api/internal/conversation/responses` 与 `POST /api/internal/conversation/retries`，按行解析 NDJSON。容器期待的事件集合是固定的：

- `user_committed`（带 `generationCommandId`、`message`、`turnId`）
- `assistant_delta`（`delta`）
- `assistant_committed`（`eventId`、`revisionId`、`createdAt`）
- `action_admitted`（`receipt`）
- `response_interrupted`、`response_failed`（带 `category`）

重试端点另有 `retry_committed`。类型定义在 `/Users/lukemyself/Projects/SayHear/packages/application/src/conversation-response.ts:44-81`，传输层在 `/Users/lukemyself/Projects/SayHear/apps/web/src/ndjson-response.ts`。

容器的 1000 行里，约 600 行是围绕这些事件名的发送、停止、补充发送、重试和失败恢复逻辑。事件名一变，这部分必须重写；`text-conversation-state.ts` 的状态形状可以保留。

另有两条容易漏掉的协议语义。客户端 62 秒自行放弃等待，服务端预算 60 秒（`text-conversation-state.ts:282`，ADR-0152）。飞行中再次发送会作废旧回答，而不是排队（`text-conversation.tsx:244-260`）。

### 会话模型

UI 依赖 Daily Session 的完整形状：`dailySessionId`、`logicalDate`、`startedAt`、`timezoneAtStart`、`activityState`，见 `/Users/lukemyself/Projects/SayHear/packages/application/src/user-text-conversation.ts:202-250`。由此派生：

- 顶部状态行“日期 · 今天/继续交流”（`portal-conversation.ts`）
- `?date=YYYY-MM-DD` 的只读历史页与“返回今天”
- 日期列表分页，30 天/页；消息分页 50 条/页
- 跨午夜不拆会话的展示规则

如果 v2 不采用 Daily Session，这些全部不适用，`portal-conversation.ts`、`portal-date-format.ts`、`chat-module-list.tsx`、`history-conversation.tsx` 都应放弃。

### 消息身份

消息字段是 `actor`、`eventId`、`revisionId`、`generationCommandId`、`sequence`、`locale`、`createdAt`、`logicalDate`。`MessageSurface` 用 `generationCommandId` 生成 Inspector 深链 `/internal/context-inspector?generation_command_id=...`（`message-time.tsx:214-219`）。这是消息展示与旧运行详情之间唯一的硬连接，必须切断或改指 v2 的运行详情。

### 写入闸门

外壳启动时请求 `GET /api/internal/access`，读 `privateWrites.allowed/reason`，再禁用输入框并显示底栏状态（`portal-shell.tsx:140-164`、`portal-write-status.ts`）。这是旧 Internal Owner 与 recovery gate 的概念，v2 的多用户访问设计不会原样存在。

### Journal

聊天模块与 Journal 只有两处接触：

1. `action_admitted` 时客户端插入“已接受，Journal 正在重新生成”的状态消息（`text-conversation.tsx:894-935`）。
2. 外壳的模块导轨与日期列表包含 Journal 入口（`portal-shell.tsx:346-460`）。

CONTEXT 明确 Journal Tab 暂不实现，这两处都应删除，而不是留占位。

### 鉴权与页面

每个页面独立执行 `getServerSession` 并重定向到 `/api/auth/signin`，没有自定义登录页（`layout.tsx`、`page.tsx`、`journals/page.tsx`）。服务端页面同时依赖 `createServerComposition()`，它装配了旧仓库的整个 application 层。

## 可复用的部分

| 类别 | 具体内容 | 复用方式 |
| --- | --- | --- |
| 布局与视觉 | 64px 顶栏、72px 模块导轨、日期列、聊天内容列、1024px 抽屉断点、760px 窄屏、safe-area | 取 CSS 规则与尺寸，不取带 Journal/工具导航的外壳组件 |
| 消息展示 | 用户右侧圆角气泡 `#efebe5` 28px；助手左侧无边框正文；1rem/1.65；`pre-wrap`；24px 间距；中断消息描边样式 | 可直接复用标记结构与 CSS |
| 时间展示 | 浏览器时区格式化、跨午夜补日期、无效时间不渲染、桌面 hover/键盘 focus/触摸长按三种揭示方式 | `message-time-presentation.ts` 可原样移植，已有 166 行测试 |
| 输入框 | 白色胶囊、44px 圆形发送键、自动增高到 200px、Enter/Shift+Enter、IME 组合保护、发送中切换停止键、错误行聚焦 | 从 `text-conversation.tsx` 抽出，作为纯展示组件接一个 `onSend(text)` |
| 交互状态机 | 等待阶段 idle/submitting/awaiting/streaming/settled/stopped/failed；只在 `user_committed` 后显示三点；滚动跟随 48px 阈值；失败恢复矩阵；客户端截止时间 | `text-conversation-state.ts` 可原样移植，已有 393 行测试；事件名需要一层映射 |
| 历史只读 | 只读日期页、加载更早消息、保持滚动锚点、返回今天、中断项只引导不重试 | 概念与 CSS 可复用；代码依赖 v2 的读取契约 |
| 无障碍细节 | `role="status"` 的稳定播报、错误聚焦、`prefers-reduced-motion`、触摸长按阈值、抽屉 Escape 只作用于窄屏 | 建议保留，这些是重做成本最高的部分 |
| 验收句柄 | `.userMessage`/`.assistantMessage` 类名，以及“想聊些什么？”“发送”“历史聊天记录”“返回今天”等可访问名 | 若保留，旧 Playwright 旅程可改造而不是重写（`scripts/verify-browser.mjs:105-373`） |

## 必须重适配的边界

| 边界 | 原因 | 处理方向 |
| --- | --- | --- |
| NDJSON 事件协议 | 事件名与字段是旧 Harness 的内部契约 | 先定 v2 流契约，再写容器；状态机形状保留 |
| 会话模型 | Daily Session、logical date、时区归属是旧产品规则 | v2 决定后再决定日期列表与历史页是否保留 |
| 鉴权与访问闸门 | next-auth v4 + 单 Owner + recovery gate | 只保留“未登录重定向”和“只读/可写”两个 UI 状态 |
| 外壳导航 | Journal 与检查工具在 v2 第一阶段不存在 | 外壳收缩为顶栏加内容区，删除模块导轨与工具列 |
| Inspector 深链 | 旧运行详情按旧 schema 构建，CONTEXT 要求重设计 | 移除消息上的图标，或改指 v2 运行详情 |
| Journal 模块 | CONTEXT 明确暂不实现 | 不移植 `journal-card`、`journal-date-list` 与对应 CSS |
| 全局 CSS | 2433 行里混有 Journal、Inspector、Candidate Review、Release Operations；存在重复选择器（`.moduleListMore`、`.composer` 等） | 只抽取聊天相关约 850 行，先删后取 |
| 文案语言 | 界面骨架是中文，失败与错误文案是英文（`text-conversation.tsx:77-87`） | 统一为中文，不照抄 |
| 框架绑定 | 外壳使用 `next/link`、`next/navigation`，页面是 App Router 服务端组件 | 若 v2 换框架，纯模块与 CSS 仍可留，外壳需重写 |

## 学习与时间预算

已测量的量：聊天切片约 3300 行 TS/TSX，加约 900 行 CSS（基础规则 283 行、外壳 288 行、聊天历史与输入 339 行）。可原样移植的只有约 600 行纯逻辑和约 900 行 CSS；其余容器逻辑要按 v2 契约重写。

估算是猜测，不是测量。按 10 小时/周计算：

| 工作 | 估计 |
| --- | --- |
| 抽取 CSS、搭静态外壳 | 3 到 4 小时 |
| 输入框与流式容器接到 v2 协议 | 4 到 6 小时 |
| 历史页与日期列表（若保留 Daily Session） | 3 到 4 小时 |
| 浏览器验证与缺陷修正 | 2 到 4 小时 |

合计 12 到 18 小时，约 1.5 到 2 周的学习预算。从 7 月 27 日起，`text-conversation.tsx` 有 15 次提交，其中包含一次高保真对齐和多次交互缺陷修复，说明“看起来简单”的部分实际最费时间。

学习上的取舍：重适配会训练协议边界和状态机设计，但不训练 Harness 内部机制。它直接占用第一阶段本应用于模型调用、流式输出和失败处理的时间。缓解办法是按顺序做：先移植纯模块与 CSS，等 v2 的流契约和会话模型定下来再做容器，历史页最后做。这样不会因为协议未定而重写两次。

另外，旧验证驱动共 1278 行（`scripts/verify-control.mjs` 294 行、`scripts/verify-browser.mjs` 984 行），绑定旧数据库与选择器。要复用得另花 3 到 5 小时改造，第一阶段不必做。

## 前提检验

`CONTEXT.md:49` 的前提成立。旧聊天 UI 没有把业务逻辑焊进展示层，纯逻辑模块已经与 React 分离并有测试。风险在于把“复用 UI”理解成复制组件树，那会连带旧会话模型、Journal、Inspector 和鉴权一起进入 v2。

建议在计划中把复用写成可验收的边界：保留交互规则、四个纯模块和聊天 CSS 子集；容器、鉴权、会话模型和运行详情全部按 v2 重写。

本次判断使用了两个原则。`principle-redesign-from-first-principles` 改变了结论的表述方式：把 v2 的流契约与会话模型当作基础假设，围绕它重设计容器，而不是把旧容器搬过来再打补丁。`principle-guard-the-context-window` 改变了调查方式：只读取聊天切片、外壳和契约文件，运行详情与 Journal 只做规模与耦合抽样，没有通读 1900 行的 Reflection Inspector。
