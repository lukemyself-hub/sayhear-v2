# 阶段 0 启动检查清单（本地）

状态：进行中。阶段 0 尚未通过，任何路线均未采纳。
更新日期：2026-10-21。范围：数据、部署、Portal、运行层与 working spec 准备。

## 交付状态

| 交付 | 状态 | 位置 |
| --- | --- | --- |
| 托管 Postgres 定点比较 | 已完成，待 Luke 决策 | `docs/plans/stages/stage-0/evidence/stage-0-data-and-delivery-evidence.md` |
| Vercel 时长、流式、取消、访问与遥测 | 文档研究完成，取消传播待实测 | 同上 |
| 旧 Portal 只读定位与复用边界 | 已完成，未运行对比 | 同上 |
| 合成数据与验收责任 | 已完成分工与最低覆盖 | 同上 |
| Runtime 文档与源码研究 | 已完成 | `docs/plans/stages/stage-0/evidence/stage-0-runtime-evidence.md` |
| Runtime 本地 mock 验证 | 已完成，V3 仅有限证据 | `docs/plans/stages/stage-0/evidence/stage-0-runtime-validation.md` |
| 决策简报 | 已完成，已按 mock 结果更新 | `docs/plans/stages/stage-0/evidence/stage-0-decision-brief.md` |
| 阶段 1 working spec | 已完成草案，未采纳 | `docs/plans/stages/stage-1/spec.md` |
| 真实 Provider 调用 | 未执行，待凭据 | — |
| Vercel 运行时与数据库 | 未执行 | — |
| 阶段 0 验收与共识 | 未开始 | — |

## 阶段 0 剩余

- 路线共识：Harness 选择。
- 数据与访问选择：数据库、地区、云费用、登录、部分输出与 fallback 体验、真实内容外送边界。
- 必要真实调用：凭据就绪后核实两条 Provider 的 endpoint、模型、错误形状与额度行为。
- 一小时示范：输入、调用、流输出与保存。
- ADR：记录已采纳路线、理由、未选项与残留 unknown。

阶段 0 的通过条件是上述事项形成共识、示范完成、Luke 能解释各层责任且 ADR 已记录。本地 mock 与文档研究完成不等于阶段 0 通过。

## Investigation

本轮按 poteto `playbooks/investigation.md` 执行。该 playbook 的四步原文：

1. Route through the **how** skill. For motivation questions, also route through the **why** skill.
2. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only investigation`.
3. Produce the `how`-shaped output (Overview / Key Concepts / How It Works / Where Things Live / Gotchas), or a recommendation with a tradeoffs table if the request is a decision between alternatives.
4. Apply the **unslop** skill to the reply.

本轮对应：第 1 步以只读定位与官方文档核验完成，未触发 why 分支；第 2 步见下方吞吐检查点；第 3 步产出为 `docs/plans/stages/stage-0/evidence/stage-0-data-and-delivery-evidence.md` 的比较与建议；第 4 步在交付前应用。

## 决策分级

已定（不重开）：

- Web 部署到 Vercel。
- 测试库与用户库是两个隔离实例。
- 最初用户是 Luke。
- 初期具备基本访问控制、内容查看与清理，兼容未来多用户。
- 复用旧 Portal 的聊天布局与交互。

偏好（Luke 已表达，未验收）：

- OpenCode Go 为主 Provider，DeepSeek 官方为备用。
- 暂不设 API 月预算上限。

建议（本文提出，未采纳）：

- 用 Vercel Authentication 保护所有部署，应用层另做会话。应用鉴权拒绝未认证页面与 API 同样满足访问控制，部署入口保护不是唯一路径。
- 服务端 60 秒预算，客户端 62 秒截止。这两个数字只是待测起点，不继承旧承诺。
- Serverless 使用池化连接串，迁移使用直连串。
- 不注册会记录输入输出的遥测集成。

已完成研究但尚未决策（只有 Luke 能定）：

- 数据库供应商、地区、套餐与月费。
- 部署入口保护方式。
- 应用登录的身份源。
- Harness 在 AI SDK 与 Mastra 之间的选择。

不在阶段 0 当前问题内：

- 是否邀请其他人访问。留到后续阶段处理。

尚未实测（阶段 1）：

- 真实 Provider 的 endpoint、模型、错误形状与额度行为。
- Vercel 断开后服务端是否在数秒内收到 abort，以及 Provider 是否停止计费。
- 关闭标签页后函数是否继续计时。
- 中止后的部分输出能否落库；流式 checkpoint 策略。
- Mastra 默认重试的实测值，以及 `~/.mastra` 等全局路径是否有落盘。
- 旧 Portal 适配的实际工作量。
- 60 秒与 62 秒预算在真实 Provider 下的表现。

## 首次真实数据前的最低核实

缺口有限，不为每一项再开子调查阻塞阶段 0。以下必须在首次写入真实用户数据前完成：

- 选定数据库套餐后，核对备份与恢复边界，并确认测试项目与用户项目是否在同一组织。
- 选定部署保护方式后，用一次未认证请求验证生产 URL 的实际行为。
- 接入 AI SDK 遥测前，确认关闭输入输出记录的具体配置。
- 首次调用 Provider 前，确认发送给 Provider 的内容范围。

## 吞吐检查点

throughput checkpoint: n/a, read-only investigation

## 边界

- 未读取凭据，未连接数据库，未创建云资源，未部署，未调用真实 Provider。
- 本地 mock 只请求 `127.0.0.1`，使用 dummy key；不构成 Vercel、真实 Provider 或计费行为的证据。
- 未修改既有计划与 roadmap。`docs/plans/stages/stage-0/evidence/stage-0-runtime-evidence.md` 的原文调研日期保留为 2026-10-21，错误结论已按 validation 就地修订。
