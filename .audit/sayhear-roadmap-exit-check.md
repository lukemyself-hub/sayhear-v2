# 准出核对

逐条对照本次会话的准出标准。每条给出实际证据与未完成部分。

- [x] 形成本地 Markdown 计划书。主计划 `docs/plans/sayhear-build-and-learning-plan.md`，研究依据 `docs/plans/sayhear-route-research.md`。均为仓库内未提交文件。
- [x] 核心技术路线与功能迭代路径。主计划给出 TypeScript Web 主线、AI SDK 优先与 Mastra 替代条件、托管 Postgres 候选、Provider 双路径、运行详情与后台执行分层。
- [x] 每个阶段含目标、feature & spec、验收标准、学习活动与理解证据、待确认问题。阶段 0 至 5 共六节。脚本检查 feature & spec、验收标准、学习活动与理解证据、待确认问题四个小标题。目标写在各阶段标题下的首段，不是小标题，脚本不检查它，由人工核对。
- [x] 保留长期愿景。阶段 6 至 10 覆盖用户控制、日记、Open Loop、语音和完整多用户，各含目标、验收、学习重点和待确认问题。
- [x] 经过技术、产品与市场调研。技术覆盖 AI SDK、Mastra、LangGraph、OpenAI Agents SDK、Claude Agent SDK、durable-harness、Mem0、Zep、Graphiti、Letta、Honcho、Hindsight、Supabase、Neon、Vercel Queues 与 Workflows、Langfuse、Inngest。产品覆盖 Pi、Nomi、Character.AI、Rosebud、Day One、Tolan。市场判断在 `sayhear-route-research.md` 的市场一节，明确当前只验证 Luke 自身需求。
- [x] 区分已定共识、研究推荐、待用户决定与待实测。主计划有“哪些结论可以确定”一节，研究依据和综合说明分级标注。
- [x] 计划符合长期愿景与年底目标。年底六阶段覆盖模型调用、流式、工具、停止、失败、可替换 Provider、运行详情、测试数据与 Vercel 部署，没有删去 Reflection 或工具调用。

未完成与限制。

- 计划状态为 Proposed，尚未获得 Luke 对技术路线、Provider、数据库和预算的共识。
- 所有验收项尚未执行。没有运行候选框架、真实 Provider、竞品应用或产品评测。
- 100 小时是低置信度参与预算，不含后台实现工时，阶段 0 后需重估。
- 候选自报的版本、价格、免费额度和函数时长未复核，不作为决定依据。外部文档可能已变化，阶段启动时按采用版本重新核对。
- 准出核对时研究与审计文件尚未提交。2026-10-21 Luke 已授权提交，本次一并留存。原始 transcript 和私人参考材料仍保留在本地，不进入仓库。
