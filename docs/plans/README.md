# 计划与阶段文档

## 目录约定

- `roadmap/`：跨阶段搭建与学习路线、路线研究。
- `stages/stage-N/README.md`：阶段入口与产物导航。
- `stages/stage-N/plan.md`：阶段完整模块、依赖、调研决策、学习目标与验收覆盖，未开始模块也登记。
- `stages/stage-N/session.md`：阶段接续，记录授权、决定、已验证、待验证与下一步。
- `stages/stage-N/evidence/`：该阶段的调研、比较与有限实验。证据不替代 ADR，旧推荐不代表当前决定。
- `stages/stage-N/spec.md`：指向 GitHub Issue 的规格入口，不复制完整 SPEC。
- 阶段内按需增加 `features/<feature-slug>/`，保存局部接续与专项证据；已有功能目录不代表完整模块清单，完整规格仍归 GitHub Issues。

阶段 1 从[阶段入口](stages/stage-1/README.md)恢复，先读总计划和总接续，再进入当前模块。阶段 0 保留原历史记录，不因本次补录改写过去的规划状态。

重要决策统一位于 `docs/adr/`，通过 `docs/decisions.md` 检索。审计与执行过程记录位于 `.audit/`，不混入产品共识。

新增文档应先确定阶段与功能归属，避免继续在本目录根部堆放带日期或阶段前缀的文件。文档移动时同步相对链接、技能入口与 GitHub Issue 的引用。
