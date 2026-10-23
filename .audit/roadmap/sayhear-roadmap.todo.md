# SayHear 路线调研工作流

- [x] Read the Principles section of the poteto-mode skill.
- [x] Phase A: Frame.
- [x] Phase B: Design the workflow.
- [x] Frame.
- [x] Fan out.
- [x] Cross-judge.
- [x] Pick.
- [x] Graft.
- [x] Verify.
- [x] Phase D: Keep the audit trail.
- [x] Phase E: Verify and hand back.

产出是阶段级功能搭建与学习计划，不实现产品，不创建或提交 PR。通用 multi-phase-plan 的逐 PR 模板、原型、十路运行验证与 check-plan 脚本不适用。skip: 用户明确要求阶段启动时再做领域细化，本次以资料证据回答选型问题。

1. 核对 CONTEXT、ADR 索引、五份旧资料。
2. 四个模型依据同一任务独立调研和形成候选，每个模型只写各自目录。
3. 候选完成后跨模型评分，主 Agent 阅读全部候选并复核关键一手来源。
4. 写入 docs/plans/roadmap/sayhear-build-and-learning-plan.md，另存研究依据和综合说明。
5. 检查每阶段目标、feature & spec、验收、学习证据、待确认问题，以及来源、边界和时间预算。

## 评分标准

每项 0 至 5 分。

- 与 CONTEXT 产品愿景、数据边界和年底范围一致。
- 技术与产品调研覆盖典型路线，结论有一手证据并承认未知。
- 技术路线便于理解、可替换、可维护，避免提前引入复杂度。
- 阶段依赖合理，验收能观察到真实行为。
- 学习活动融入真实产品，每周约 10 小时预算可信。
- 区分已定共识、研究推荐、待用户决定与待实测事项。

## 吞吐检查点

并行仅用于四份独立候选，整合文件由主 Agent 单独写。四份候选齐备后才交叉评审。来源冲突和选型未知优先处理，工具安装、实现原型和部署均不属于本次任务。预计 Luke 只需审阅最终推荐和关键问题，后台调研不占其学习预算。
