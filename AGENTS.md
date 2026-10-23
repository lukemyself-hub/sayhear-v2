# SayHear Agent 入口

本文件只提供全局规则和启动入口。完整立项共识读取 [`CONTEXT.md`](CONTEXT.md)。

## 全局规则

- 未经 Luke 明确授权，Git 与 GitHub 操作默认使用 `luke-agents` 账号，禁止擅自使用 `lukemyself-hub` 个人账号。
- 修改前检查 `git status`，保留已有改动；优先小而可逆的变更，避免无关重构和新依赖。
- 修复问题前先确认根因，完成后运行与风险相称的验证。
- 未经明确要求，不提交、推送、重写历史、删除分支或工作树。
- 不因实现便利改变产品定义。若改动会影响产品定位、用户承诺、数据边界或关键体验，先读取 `CONTEXT.md` 与 Luke 确认。
- 学习笔记固定存放在 `/Users/lukemyself/Documents/学习/AI/Agent Harness`，各 worktree 的 `study-notebook` 是指向它的本地符号链接，不写入代码仓库。

## 文档启动规则

- 每个任务先读取本文件和 [`CONTEXT.md`](CONTEXT.md)。
- 有 GitHub Issue 或 `docs/tasks/` working spec 时，先读取任务本身，再读取它明确链接的文档；这些链接是最低起点，不是相关决策的完整清单。
- 设计或开发具体功能，以及修改架构、数据模型、接口或隐私边界前，先通过 [`docs/decisions.md`](docs/decisions.md) 检索并读取所有命中的 ADR。
- 不无目标地通读全部 ADR、`docs/archive/` 或整套产品文档。
- 需要环境变量、连接数据库或运行测试前，先读取 [`docs/agents/local-environment.md`](docs/agents/local-environment.md)。
- 发现文档与代码冲突时，明确指出冲突，不要自行猜测。
- 同一任务中不重复读取没有变化的长文档。

## 学习环节

- 讲解重要架构设计、关键决策和实现逻辑时，结合当前代码和实际运行，不照本宣科。
- 适时反问 Luke 确认理解；发现缺口后补充讲解或演示，并在后续讨论中再次提问。
- 不背诵、不看课时、不考试，也不因完成讲解或笔记就认定 Luke 已掌握。
- 不为学习安排无目的试错。有成熟实践时，讲清适用条件和取舍后采用。

## Agent skills

### Issue tracker

Issues 与 SPEC 跟踪在 GitHub Issues。读取 [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md)。

### Triage labels

五个标准 triage 角色直接使用默认 label 名（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`）。读取 [`docs/agents/triage-labels.md`](docs/agents/triage-labels.md)。

### Domain docs

单上下文：根目录 `GLOSSARY.md` 加 `docs/adr/`，ADR 通过 [`docs/decisions.md`](docs/decisions.md) 的主题检索定位。读取 [`docs/agents/domain.md`](docs/agents/domain.md)。
