# Issue tracker

## TL;DR

- Issues 与完整 SPEC 跟踪在 GitHub Issues，是执行范围的唯一真源。
- 本地文档不复制 SPEC 正文，只维护索引和指向 Issue 的说明。
- 实现前先读取 Issue 及其明确链接的文档，再检索相关 ADR。

## Status

Draft

## 规则

1. 每个功能在开始前有对应 Issue，写清目标、范围、验收标准。
2. Issue 链接是最低起点，不保证已列全相关决策，仍需按 `docs/decisions.md` 检索 ADR。
3. 实现完成后在 Issue 中记录实际结果与验证证据。
4. 实现中若发现范围外问题，另开 Issue，不就地扩张当前 Issue。

## gh CLI 操作约定

仓库从 `git remote -v` 推断；在 clone 内运行 `gh` 时会自动解析，无需显式传 `--repo`。

- **建 Issue**：`gh issue create --title "..." --body "..."`，多行 body 用 heredoc。
- **读 Issue**：`gh issue view <number> --comments`，并用 `jq` 过滤 comments，同时取 labels。
- **列 Issue**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，按需加 `--label` / `--state` 过滤。
- **评论**：`gh issue comment <number> --body "..."`
- **改 label**：`gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **关闭**：`gh issue close <number> --comment "..."`
- **设为子 Issue**：`gh issue create --parent <parent> ...`，或事后 `gh issue edit <parent> --add-sub-issue <child>`（`gh` 2.94+）。旧版 `gh`：`gh api --method POST repos/<owner>/<repo>/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>`。没有子 Issue 能力时，在子 Issue body 顶部写 `Part of #<parent>`。

## 术语对应

- 技能说「publish to the issue tracker」= 创建一个 GitHub Issue。
- 技能说「fetch the relevant ticket」= `gh issue view <number> --comments`。
- Issue 与 PR 共用同一编号空间，裸 `#42` 可能是 PR：先 `gh pr view 42`，失败再 `gh issue view 42`。

## PR 是否作为需求入口

**PRs as a request surface: no。** （本仓库不把外部 PR 当 feature request 纳入 triage 队列；需要时把此标记改为 `yes`。）

改为 `yes` 后，PR 走与 Issue 相同的 label 与状态，用 `gh pr` 对应命令：

- **读 PR**：`gh pr view <number> --comments` 加 `gh pr diff <number>`。
- **列外部 PR**：`gh api --paginate 'repos/{owner}/{repo}/pulls?state=open' --jq '.[] | select(.author_association | IN("OWNER","MEMBER","COLLABORATOR") | not) | {number, title, author: .user.login, author_association, labels: [.labels[].name]}'`。
- **评论 / label / 关闭**：`gh pr comment`、`gh pr edit --add-label` / `--remove-label`、`gh pr close`。

## Wayfinding 操作（`/wayfinder`）

**map** 是单个 Issue，**child** Issue 作为工单。

- **Map**：一个带 `wayfinder:map` label 的 Issue，body 承载 Notes / Decisions-so-far / Fog。`gh issue create --label wayfinder:map`。
- **子工单**：通过 GitHub 原生子 Issue 挂到 map 上（见上）。没有子 Issue 时，在 map body 的任务清单里登记，并在子工单 body 顶部写 `Part of #<map>`。Label：`wayfinder:<type>`（`research` / `prototype` / `grilling` / `task`）。被认领后指派给推动的开发者。
- **Blocking**：GitHub **原生 issue dependencies**，是 UI 可见的规范表示。`gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`，其中 `<blocker-db-id>` 是阻塞方的数字 **database id**（`gh api repos/<owner>/<repo>/issues/<n> --jq .id`，不是 `#number` 或 `node_id`）。GitHub 用 `issue_dependencies_summary.blocked_by` 汇报（只含未关闭阻塞，实时门禁）。不可用时退化为子工单 body 顶部的 `Blocked by: #<n>, #<n>`。所有阻塞关闭后工单才解除阻塞。
- **Frontier 查询**：列出 map 的未关闭 child，剔除有未关闭阻塞者（`issue_dependencies_summary.blocked_by > 0`，或 `Blocked by` 行里有未关闭 Issue）和已有 assignee 者，map 顺序第一个胜出。
- **Claim**：`gh issue edit <n> --add-assignee @me`，是会话的第一次写操作。
- **Resolve**：`gh issue comment <n> --body "<answer>"`，然后 `gh issue close <n>`，最后在 map 的 Decisions-so-far 追加一条上下文指针（gist + 链接）。
