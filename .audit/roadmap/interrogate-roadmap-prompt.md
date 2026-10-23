你是只读对抗评审员。本次对象是文档，不是代码，不修改任何文件或创建外部 Issue。

意图。用户要求经过产品、市场和技术调研形成 SayHear 的阶段级功能搭建与学习计划。遵守 CONTEXT，不提前细化 schema、接口或逐 PR 实施。评审 AI SDK 优先与 Mastra 替代是否有证据，先基础记忆后 Reflection 是否合理，100小时预算是否误导，用户决定与实测未知是否明确。不要质疑既定产品目标，不要求本次已实现产品。

读取 /Users/lukemyself/Projects/SayHear-v2/CONTEXT.md、docs/plans/roadmap/sayhear-build-and-learning-plan.md、docs/plans/roadmap/sayhear-route-research.md。另读 /Users/lukemyself/.claude/plugins/cache/pstack-claude/pstack/0.9.94/skills/interrogate/references/reviewer-prompt.md、rubric.md、code-quality-review.md，仅采用与计划文档相关的正确性、边界、复杂度、验证视角。

逐项给出真实问题的 severity critical/warning/nit，精确位置、证据和具体建议。区分实际遗漏与个人偏好。重点找会让后续执行错误的范围、依赖、可观测性、验收或证据问题。不为凑问题要求提前设计。无问题就写 no findings。只返回结构化报告，不写仓库。不评判尚未完成的 arena 为已通过。
