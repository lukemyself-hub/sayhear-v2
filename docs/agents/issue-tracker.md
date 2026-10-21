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
