# 会话与消息最小结构草案

最终状态（2026-10-24）：Luke 已整体接受 [M2 收尾规格](spec-draft.md)，M2 设计收口。以下形成过程中的“候选/待审阅”以收尾规格及最新 ADR 为准；具体 SQL、SDK 映射和跨模块待办仍需后续落实，未实现或验证。

日期：2026-10-24。状态：数据设计汇总，未实现、测试或发布为执行 SPEC。范围真源仍为 Issue #1。已接受与工程建议分别注明，不以字段草案代替 M2 整体收口。

## 会话

按 [ADR 0008](../../../../../adr/0008-continuous-conversation.md)：id、owner_id、created_at 三列，每 owner 至多一个连续会话。id 为 UUIDv7，时间为 timestamptz，owner 对应 auth.users.id；字段类型的实际支持与默认函数实施前核实。

消息通过同 owner 外键引用会话；账户清理随 auth 用户级联。seq 分配的工程候选锁定已有会话行后读取消息最大号，不在本轮给会话增加计数列，具体算法未由首段展示决定自动接受。

## 消息

| 字段 | 用途与约束来源 |
| --- | --- |
| id、owner_id | 身份与直接归属，UUIDv7 与逐表 RLS，ADR 0010/0015 |
| conversation_id | 连续会话引用，必须同 owner；日期不创建新容器 |
| seq | 持久展示位置；首次入库分配，流式更新、完成、中断、删除不改号。正值、会话内唯一与数据库分配方式随最终 schema 落实 |
| role | 阶段 1 运行消息仅 user/assistant；不设独立 system 行，合成工具过程放 assistant parts |
| parts | 原样采用锁定版本 AI SDK parts，jsonb JSON 数组，不允许 SQL NULL；删除时原子清为 [] |
| parts_schema_version | 推荐新增格式元数据，从首个落地契约的 1 起；标识如何读取 parts，不改变 SDK parts 内容格式，实际映射实施前确认 |
| status | 既定 generating/complete/interrupted；用户输入建议持久化成功即 complete，表示消息内容已完整保存，不表示已有回答。assistant 状态依生成/收尾结果，不与 run/attempt 状态混用 |
| run_id | user 为空，由 run 反向引用触发消息；assistant 必填且每 run 至多一条，复合归属约束按 ADR 0010 |
| created_at | 该消息首次建行时间，不用后续 checkpoint 时间替换；用户本地发送时间是否另记由 M3 的时间语义确认 |
| deleted_at | 与生成状态独立；非空时 parts=[]，保留身份、seq、时间及来源关系，迟到保存不得清除标记或恢复内容 |

不另存镜像正文列，也不为工具调用、结果或系统指令增建消息行。任何需要携带内容的新列必须纳入删除清空规则；其他来源消息中碰巧含相同文字不等于自动一并删除。

已结束且成功保存的正文作为稳定引用来源，除删除与有明确迁移方案的结构升级外不普通改写；重试新建 run 和新 assistant 消息。部分回答是否被选择为后续上下文由 M3 决定，存储允许 interrupted 不等于自动选取。

## 首段与格式版本

用户消息首次保存取得 seq；阶段 1 assistant 第一个非空正文先入库确定位置再显示，已由 Luke 明确接受。后续片段不逐个强制先写库再显示，checkpoint 策略与终态收尾由 M4 细化。首段建行与 run.output_attempt_id 的关联写入仍需在完整数据方案中保证一致。

联合审阅已补充具体事务要求，见 [run/attempt 草案的输出来源](run-attempt-draft.md#输出来源关系的建议)：首次 assistant 消息、seq、run 的输出 attempt 关联以及 attempt 的首段观测同一操作保存，再发布首段。消息更新仍检查 deleted_at、生成状态及当前 run 的可执行条件；具体停止/终态竞态待 M4/M7 决定。

消息 parts_schema_version、attempt.input_record.schema_version 和实际应用/SDK 版本分别表达持久数据格式、输入引用表示、实现来源。未知版本不按最新格式猜读；将来格式迁移须保护旧输入记录的 parts 引用和读取方式，不能只是改版本号。

本阶段只实现首个实际格式，不提前编写任意版本转换框架，也不因为版本字段已存在就宣称升级兼容。上述元数据与用户 status 的常规建议随完整规格审阅，不逐字段要求产品表决。

## 剩余边界

- seq 的具体数据库分配、不可绕过的约束及客户端迟到合并，见 [seq 方案](evidence/message-seq-allocation.md)。不据此启用生成中排队或跨设备实时订阅。
- parts 和 input_record 的首个格式合同、引用 JSON 与校验规则尚未完整列出。
- owner/外键/唯一约束、run 输出来源及原子写函数需要将两份字段草案一起审阅，不能各自验证而遗漏跨表关系。
- M3 的历史资格与裁剪、M4 的终态/恢复竞争与 checkpoint、M5 的临时发送及错误展示、M7 的删除生效顺序仍待对齐。
- 账户清理、误配护栏与数据库测试在获授权构建阶段验证。本轮未创建表、迁移或测试数据。
