# 计划与阶段文档

## 目录约定

- `roadmap/`：跨阶段搭建与学习路线、路线研究。
- `stages/stage-N/session.md`：阶段接续，记录授权、决定、已验证、待验证与下一步。
- `stages/stage-N/evidence/`：该阶段的调研、比较与有限实验。证据不替代 ADR，旧推荐不代表当前决定。
- `stages/stage-N/spec.md`：指向 GitHub Issue 的规格入口，不复制完整 SPEC。
- 后续阶段涉及多个功能时，在阶段内增加 `features/<feature-slug>/`，保存功能接续与证据；完整规格仍归 GitHub Issues。

重要决策统一位于 `docs/adr/`，通过 `docs/decisions.md` 检索。审计与执行过程记录位于 `.audit/`，不混入产品共识。

新增文档应先确定阶段与功能归属，避免继续在本目录根部堆放带日期或阶段前缀的文件。文档移动时同步相对链接、技能入口与 GitHub Issue 的引用。
