# Domain Docs

工程技能在探查代码库时应当如何消费本仓库的领域文档。

## 探查前先读这些

- **`GLOSSARY.md`**（仓库根目录）：SayHear 术语、名称与禁用近义词的唯一权威来源。
- **`docs/decisions.md`**：ADR 索引，按「主题检索」表和关键词定位相关 ADR，再读 `docs/adr/` 下命中的文件。当前 ADR 数量为 0，索引为空属于正常状态。

这些文件不存在时**静默继续**：不要提示缺失，也不要建议先创建。`/domain-modeling` 会在术语或决策真正被解决时按需创建它们。

## 文件结构

单上下文仓库（本仓库）：

```
/
├── GLOSSARY.md
├── docs/decisions.md            ← ADR 主题检索索引
├── docs/adr/                    ← ADR 正文（当前为空）
├── CONTEXT.md                   ← 立项共识与产品范围
└── docs/architecture/           ← 技术约束
```

注意：本仓库的 ADR 通过根目录 `docs/decisions.md` 的主题检索表定位，不直接扫 `docs/adr/` 目录。

## 使用 GLOSSARY 的词汇

输出中命名领域概念时（Issue 标题、重构提案、假设、测试名），使用 `GLOSSARY.md` 中的定义写法，不要漂移到它明确标为 `_Avoid_` 的近义词。

如果需要的概念还不在 GLOSSARY 里，这是个信号：要么你在发明项目不用的语言（重新考虑），要么这是真实缺口（记录下来交给 `/domain-modeling`）。

## 标记 ADR 冲突

输出与已有 ADR 矛盾时，明确暴露出来，不要静默覆盖：

> _与 ADR-0007 矛盾，但因为……值得重新讨论_
