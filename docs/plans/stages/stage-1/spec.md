# 阶段 1 SPEC 入口：基础文本对话与 canonical 闭环

状态：Luke 于 2026-10-22 确认并授权发布初始阶段 SPEC，已发布为 GitHub Issue，标签 `ready-for-agent`。身份与 canonical 的后续设计细化尚未全部发布；此标签不表示本阶段全部设计已收口或已授权实现。

完整 SPEC 与执行范围以 [Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1) 为唯一真源。本文件不再复制正文，避免形成两套规格。

## 实施前阅读

1. 读取 Issue 正文及明确指向的材料，再读[阶段总计划](plan.md)和[总接续](session.md)核对后续设计与未决项。
2. 读取 [CONTEXT.md](../../../../CONTEXT.md)，按[决策索引](../../../decisions.md)检索所有相关 ADR。当前已接受 ADR 0001–0016；完整数据结构仍在 [canonical 功能接续](features/canonical-data-model/session.md)中讨论，不能据 ADR 数量推断阶段设计全部完成。
3. 运行测试、使用环境变量或数据库前，读取[本地环境规则](../../../agents/local-environment.md)。
4. 核对[阶段 0 接续记录](../stage-0/session.md)中的授权、已验证能力及待验证项。

## 交接限制

Issue 已由 `luke-agents` 发布并读回核对。历史交付中，Luke 曾授权整理对应轮次文档、提交、推送、创建 PR 并合入 main。文档 PR 的合入结果与固定版本材料链接以 Issue 和 PR 回执为准。

后续构建从 fetch 后核实的最新 `origin/main` 新建工作分支，先基于 Issue 整理实施方案与测试环境前置。上述发布与 Git 交付授权仅为对应历史轮次；2026-10-24 本次接续只授权讨论分支、必要文档补录与继续讨论，未授权新的 Issue 写入、Git 发布、产品实现、创建云资源、连接用户库或部署。当前授权以[总接续](session.md)为准。
