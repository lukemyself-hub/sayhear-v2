---
name: learning-stage
description: 启动或接续 SayHear 阶段主会话，围绕当前 feature 推进调研、讲解与决策，维护进度并交付阶段 SPEC；不执行构建与测试。
---

# Learning stage

推进当前阶段的产品设计和 Luke 的理解。遵循 `AGENTS.md`、`CONTEXT.md` 和阶段共识。主 Agent 拆目标、查事实、推荐、讲解并维护记录；Luke 决定产品取舍、阶段范围和关键架构。

会话围绕一个 feature 推进：随时清楚当前是哪个 feature、本次要推进到哪里、还剩哪些议题。单个决策点是推进 feature 的手段，不是会话本身的目标。

## 会话流程

会话开始或切换 feature 时做第 1 步，之后在第 2 至 4 步之间循环。

1. **恢复焦点。** 查 `git status`，保留并行改动。按 [focus.md](references/focus.md) 读阶段计划、总接续和当前 feature 的状态卡。向 Luke 简短说明当前 feature、已定事项、本次目标和暂不展开的议题。范围未变时直接推进，不重复确认议程。
2. **选一个议题。** 从议题清单选一项阻塞本次目标的议题。讨论中新出现的问题先按 focus.md 分流登记，不自动展开。
3. **按议题性质处理。**

   | 议题需要 | 读 |
   | --- | --- |
   | 查事实、机制或外部资料 | [investigate.md](references/investigate.md) |
   | Luke 先理解某个机制 | [explain.md](references/explain.md) |
   | Luke 做取舍或确认 | [discuss.md](references/discuss.md) |

4. **回到主线。** 议题解决、暂缓或转交后更新状态卡，说明 feature 离完成条件还差什么，再选下一项或收尾。

feature 达到完成条件时按 focus.md 收口。新阶段启动、目录结构、接续与学习笔记格式见 [records.md](references/records.md)。阶段内各 feature 收口、跨 feature 契约与验收就绪后，才读 [spec-handoff.md](references/spec-handoff.md)。

## 分支与授权

- 新阶段从最新 `origin/main` 建工作分支；恢复时沿用原分支，切换 feature 不另开分支。
- 区分授权、决定、推荐、待验证、完成。调用本 skill 不扩大提交、发布或其他外部操作的授权。

## 写作

默认中文，按 `unslop` 写议程、比较、提问和讲解。从最小完整解释开始，按 Luke 的回应展开；简洁，但保留决策条件、风险和证据，不幼儿化。

## 外部 skill

不加载 `poteto-mode`、`grill-with-docs`、`grilling` 或 `teach` 的整体流程：它们的结束条件和产物要求与阶段会话冲突，需要的部分已写入各 reference。各 reference 写明何时直接使用 `how`、`why`、`research`、`domain-modeling`、`to-spec`、`pr` 和委派工具。技能或工具在当前运行时缺失时说明并继续，不伪称调用。
