# SayHear v2 文档地图

## TL;DR

- 每个任务先读取根目录 [`AGENTS.md`](../AGENTS.md) 和 [`CONTEXT.md`](../CONTEXT.md)。
- 根目录 [`GLOSSARY.md`](../GLOSSARY.md) 是术语唯一真源。
- `CONTEXT.md` 保存立项共识和长期方向，不承载 SPEC 与实现进度。
- `adr/` 解释重要决定的原因；`tasks/` 是短期 working spec；`specs/` 只维护索引。
- 文档按需读取，不因节省上下文而跳过与任务相关 ADR 的检索。

## Status

Draft

## 权威来源边界

| 内容 | 当前权威来源 |
| --- | --- |
| 立项背景、愿景、阶段范围、协作共识 | `CONTEXT.md` |
| 术语、名称和禁用近义词 | `GLOSSARY.md` |
| 具体功能目标、范围、验收 | 对应 GitHub Issue 或 `tasks/` 下的 working spec |
| 重要决定及其原因 | `adr/` 中对应 ADR |
| 技术边界与系统不变量 | `architecture/` 对应主题文件 |
| 产品行为与体验规则 | `product/` 对应主题文件 |
| 历史与被取代方案 | `archive/` |

## 目录说明

| 目录 | 用途 |
| --- | --- |
| `adr/` | 重要架构与工程决策，含问题、理由、取舍 |
| `architecture/` | 技术契约与系统不变量 |
| `product/` | 产品行为与体验规则 |
| `tasks/` | 短期 working spec |
| `specs/` | 已发布 SPEC 的轻量索引 |
| `agents/` | Agent 操作规则 |
| [`plans/`](plans/README.md) | 跨阶段路线、阶段接续、研究证据与 SPEC 入口 |

执行审计按路线、阶段与工具归类，见 [`.audit/README.md`](../.audit/README.md)。

## 文档状态

- **Draft**：正在形成，不能视为已确认需求。
- **Proposed**：已有完整方案，实施前仍需确认或验证。
- **Accepted**：当前有效的权威来源。
- **Deprecated**：不应继续用于新实现，保留追溯。

## Open questions

- 已接受决定见 [`decisions.md`](decisions.md)，新增重要决定时同步维护 ADR 索引。
- `architecture/`、`product/` 的具体文件在首次涉及该领域的设计前创建。
