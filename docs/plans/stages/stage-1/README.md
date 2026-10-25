# 阶段 1：基础文本对话与 canonical 闭环

2026-10-24 补建阶段入口。依据为已发布的 Issue #1、路线图、ADR 0001–0015 和两个功能的接续记录，不代表这些总记录在此前已经存在或获得确认。

阶段目标是让 Luke 离开开发电脑也能私密聊天，重开后看到历史，遇到遗漏或失败时能查到实际模型输入及保存结果。完整执行范围以 [Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1) 为准。

## 恢复入口

1. 读 [总计划](plan.md)，了解完整范围、依赖、设计与学习进度。
2. 读 [总接续](session.md)，核对当前授权、停点、阻塞及下一动作。
3. 进入 [canonical 数据结构接续](features/canonical-data-model/session.md)，从尚未确认的系统记录方案继续。

本次只补录规划并继续讨论，不开始产品实现。Luke 于 2026-10-24 确认总计划的九个模块，以及先继续 canonical 数据结构、再按依赖细化其余模块的安排；已接受的 ADR 不重新表决。设计收口、SPEC 发布、文档合入、产品实现和验收分别记录。

## 产物导航

| 材料 | 职责与状态 |
| --- | --- |
| [plan.md](plan.md) | 全阶段模块、共享契约、调研决策、学习与验收覆盖；模块组织及推进顺序已确认，各模块未决设计仍待讨论 |
| [session.md](session.md) | 全局当前状态、授权、下一步与交接 |
| [spec.md](spec.md) | 已发布阶段 SPEC 的 Issue 入口及后续细化状态 |
| [功能索引](features/README.md) | 已有局部记录，不是阶段完整模块清单 |
| [身份与数据归属](features/identity-data-ownership/session.md) | 设计已收口，局部 SPEC 为未发布临时草稿 |
| [canonical 数据结构](features/canonical-data-model/session.md) | 部分决定已接受，完整结构未收口；系统记录已决定不设独立 system 行 |
| [决策索引](../../../decisions.md) | 定位全部相关 ADR；决定的权威位置 |
| [跨阶段路线图](../../roadmap/sayhear-build-and-learning-plan.md) | 阶段顺序、学习覆盖和预算背景 |
| [阶段 0 接续](../stage-0/session.md) | 前置调查、有限验证与历史交付，使用时辨别时间与后续决定 |

尚未有细节材料的模块只在总计划登记，按需建立局部记录。私人学习笔记仍位于 `CONTEXT.md` 指定的外部目录。
