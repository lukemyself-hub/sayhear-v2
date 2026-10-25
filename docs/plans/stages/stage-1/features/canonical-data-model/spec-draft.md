# M2 canonical 数据模型收尾规格草稿

日期：2026-10-24。状态：M2 设计已收口，Luke 于 2026-10-24 回复“认可，收尾 M2 方案吧”，整体接受收尾方案，包含 seq 分配及输入引用首版表示；已接受决定关联 ADR。未发布为执行 Issue，未实现、测试或部署。Luke 指定本会话只收尾 M2，M3 后续另开会话，本轮不创建新会话。阶段范围真源为 [Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1)。

## 目标与决定入口

提供可追溯的连续历史、运行与 Provider 尝试、按当次协议结构记录的模型输入，并支持 owner 隔离与单条删除。核心为四张产品表，不增加独立快照表、产品指令消息行或输入引用关系表。

- 权限与真实引用：[ADR 0009](../../../../../adr/0009-server-data-access-and-rls.md)、[ADR 0010](../../../../../adr/0010-minimal-data-contract-and-owner.md)。
- 连续会话：[ADR 0008](../../../../../adr/0008-continuous-conversation.md)。
- parts、排序和首段持久化：[ADR 0015](../../../../../adr/0015-message-parts-and-ordering.md)。
- 每请求指令、固定 A 与裁剪保护：[ADR 0016](../../../../../adr/0016-per-request-system-instructions.md)。
- 停止、结果和期限：[ADR 0005](../../../../../adr/0005-chat-experience-and-run-record.md)、[ADR 0006](../../../../../adr/0006-chat-time-budgets.md)。

## 四类记录与约束

详细字段沿用[消息与会话](message-conversation-draft.md)、[run 与 attempt](run-attempt-draft.md)，本稿作为收尾入口，不另外维护重复字段表。

| 记录 | 必须表达的内容 | 关键关系和约束 |
| --- | --- | --- |
| conversation | id、owner_id、created_at | 每 owner 至多一个；不是登录会话或每日会话 |
| message | id、owner、conversation、seq、role、parts、格式版本、status、run_id、创建/删除时间 | user 的 run_id 为空；assistant 必填且每 run 至多一行；同 owner、同会话的来源关系不得改挂 |
| run | 触发消息、幂等意图、生命周期、结束原因/阶段、期限与时间、固定产品指令及实现版本、输出 attempt | 触发消息必须为同 owner 的 user；输出 attempt 必须属于本 run；同 owner 请求标识唯一 |
| attempt | 所属 run、编号、生命周期与 Provider 结果、输入记录、Provider/模型/响应标识、观测时间/耗时、usage 与成本 | 编号 1/2 且 run 内唯一；主路线与一次 fallback 分开记录，具体切换资格由 M4 确认 |

身份为 UUIDv7，时间为 timestamptz，自有状态用 text+CHECK。目标数据库的 UUIDv7 支持在实施时核实。所有产品表直接 owner_id、RLS，与 auth.users 关联；真实跨表引用用同 owner 组合外键，必要处另保证同 run/会话及角色。复合唯一键、循环引用的建表顺序与实际 SQL 留给实施，不用 JSON 来源校验替代这些真实外键。

工程建议纳入整体审阅：消息的 parts_schema_version 与 input_record.schema_version 各从首个实际格式 1 起；未知版本不猜读。用户消息保存成功为 complete，只代表消息完整保存。同一 run 至多一个 created/running attempt；同一幂等 key 的相同提交意图复用，不同意图冲突拒绝。输出 attempt 一旦建立不普通改挂，不能强制其结果必须 succeeded，因为部分回答也可能来自 unknown。

## 排序与持久化工程建议

首段先成功入库确定位置再展示已接受。具体推荐将所有首次消息插入收敛为数据库强制执行的同会话分配规则：

1. 在 owner/RLS 路径短事务中锁定所属会话行。
2. 取得锁之后，以 READ COMMITTED 的独立新查询读取包含删除占位的 MAX(seq)，空为 1，否则加 1。
3. 与新消息一起插入并提交；不把锁与 MAX 塞进依赖旧快照的单条查询，不跨 Provider 网络持锁。

seq 为正 bigint，会话内唯一，普通写入不得指定任意序号或改写既有序号。建议 BEFORE INSERT 触发器统一分配并保护不可改字段，配合权限约束覆盖服务端及合成装载入口；不得让某个插入路径绕过分配。实际 SQL、隔离级别、索引、锁顺序与并发行为须在授权实施时验证，尚无运行证明。账号清理等多对象操作须统一锁顺序。

首段操作同时建立 assistant 消息、seq、run.output_attempt_id 与首段观测，确认提交后发布；后续正文不逐片强制入库后展示。首段提交失败或应答不确定不能因浏览器未见正文就 fallback、重建回答或重放 Provider。客户端按稳定 id 合并、按 seq 排序，不能因见过较大号永久忽略迟到的小号。补取、分页和临时发送状态归 M5；本规格不启用排队或实时订阅。

## 输入记录首版表示建议

采用有限纯文本表示，不建任意工具/多模态转换引擎。建议 input_record 由 schema_version、request_template 和 text_bindings 组成。request_template 保留捕获请求的 JSON 结构及非引用值；被引用的正文字符串位置暂置 null，由明确路径绑定恢复。真正的 null 与省略字段保持原样，只有 text_bindings 指定的位置才替换；路径必须唯一、合法、位于支持的文本字段，不能用于改写角色或模型参数。

以下为说明表示方式的片段，不是可直接发送的请求，也不是完整实际 Provider 请求。m101 为消息 UUID 的阅读代号，sha256 值仅为占位。

```json
{
  "schema_version": 1,
  "request_template": {
    "model": "本次实际请求模型",
    "messages": [
      {"role": "system", "content": "当次产品指令 A 原文"},
      {"role": "user", "content": null}
    ]
  },
  "text_bindings": [
    {
      "path": ["messages", 1, "content"],
      "sources": [{"message_id": "m101", "text_part_indices": [0]}],
      "join": "concat",
      "sha256_utf8": "该位置最终文本的摘要"
    }
  ]
}
```

首版仅直接拼接所列完整 text parts，不做隐含分隔、裁剪、trim 或字符规范化；摘要针对最终拼接文本的 UTF-8 字节。数组 content 则记录相应文本叶子路径，保留原数组顺序。参数只记录实际值，不填猜测的 Provider 默认值，不保存请求头、密钥或原始错误对象。来源映射须从组装过程取得，不能只凭字符串相同猜来源。

示例把 A 直接保留在模板中；实现可以引用本 run 固定保存的指令正文，前提是首版表示明确表达该规则，并核对实际协议内容。禁止仅存 hash 或回读当前部署文件。具体字段命名及是否复用 run 指令正文是可逆的工程细节，不要求新增产品表。

发送前用当次来源解析引用表示，按 JSON 值、角色、数组顺序和文本核对捕获的最终请求；成功后与 created→running 资格一起持久化，确认取得资格才发送原请求。JSONB 不追求对象键顺序、空白或 HTTP 字节级取证。不能表示的形状在发送前停止，不静默复制消息全文或发送后才发现无法记录；具体失败呈现归 M4/M5。合成搜索记录仍可存于 SDK parts，但不因此授权发送工具历史或实际搜索。

来源存在、同 owner、同 run 对应会话及 part 范围/类型由数据库强制校验，暂不新增引用关系表，已获 Luke 接受。实现须覆盖 input_record 写入及普通归属改挂；触发器不重新做 SDK 转换或上下文选择。M3 决定可选消息，M7/M4 决定校验后删除与发送的先后，不宣称触发校验已解决这类竞态。

## 状态、删除与回看

run 为 created/running/succeeded/failed/interrupted。只有正常生成且必要保存成功才能 succeeded。attempt 为 created/running/finished，未 finished 时结果为空，finished 必须有 not_sent/succeeded/failed/unknown。收口结果、原因和结束时间原子写；finished 不回到 running。running 只表示本地发送资格，不证明远端收到；缺少可靠证据不能断言 not_sent，也不能自动重放不确定请求。

Provider 正常结束而最终数据库保存失败时，attempt 可 succeeded，run 不得 succeeded。准确首段/调用耗时须保存真实单调计时观测，数据库时间戳不能冒充网络计时。缺失 usage、成本或观测值为空/unknown，不当零值。

消息 parts 是 JSON 数组且不为 SQL NULL；单条删除原子置 [] 并设置 deleted_at，保留 id、seq、来源。所有内容写入原子检查未删除，不使删除内容复活。稳定且成功保存的终态正文不普通改写；显式重试新建 run 与回答。来源删除后旧详情显示缺失，摘要不符时显示不能准确还原；不能从缓存或复制正文绕过删除边界。账户清理仍级联清除归属数据。

产品指令 A 不参与普通历史裁剪，包含 fallback；后来部署 B，旧记录仍读取 A 原文。先为必需指令与输出留预算再选择历史；无法容纳必需指令则发送前明确失败，不静默删指令。本工程建议已获 Luke 本轮认可，具体预算归 M3。

生成中的界面仅使用停止按钮，保留部分回答并标记中断，不新增生成中删除入口。取消远端是否已停止、是否停止计费不能由本地状态推断。

## 交接清单及阻塞归属

| 模块 | 必须继续决定/验证 | M2 已提供的承载契约 |
| --- | --- | --- |
| M3，新会话继续 | 历史选择、interrupted/变化中消息资格、裁剪单位、当前提问与日期/时区、token 预算 | 稳定来源引用；产品指令不可裁掉；超出首版形状须明确重评，不能默许复杂转换 |
| M4 | 原子写条件、fallback 资格、checkpoint、停止/完成/恢复竞争、期限及失败恢复 | 状态/result 分列、发送前门槛、首段与来源原子建立、未知不重放 |
| M5 | 临时状态、迟到合并/分页补取、错误与中断显示 | 稳定 id+seq、首段先入库、不按显示顺序推断输入 |
| M6 | 实际模型与 usage/成本口径、耗时来源、详情读取 | attempt 为观测真源，正文缺失明确展示，旧指令固定 |
| M7 | 删除与组装/发送的生效顺序、账号清理、锁顺序 | 清空正文与条件写保护、来源不级联、数据库来源校验 |
| M8/M9 | 夹具装载、RLS/数据库约束、真实部署、备份恢复 | 四表与合成搜索存储边界，不把文档检查当产品证据 |

上述跨模块契约必须在阶段执行 SPEC/实施前集成收口；本模块讨论收尾不表示它们解决或授权开始构建。

## 后续验收清单，全部未运行

- 两主体逐表 RLS、真实外键及 JSON 跨主体/跨会话/失效 part 引用拒绝；直接入口写入同样不能绕过。
- 并发登记的同意图幂等，不同意图冲突；同 run 输出数量/输出来源/活动 attempt 约束。
- 并发首次插入、回滚、删除占位、seq 不变与不可绕过；首段失败/应答丢失无重复展示或调用。
- 输入解析与真实捕获请求相等；多 text part 拼接、数组形状、参数省略、未知版本、来源改动可识别。
- 删除后原文不再展示或写回，后续上下文排除；A→B 部署后旧运行仍读 A，预算裁剪及 fallback 均携带指令。
- 正常/失败/停止/未知 Provider 结果与数据库故障分别如实表达；合成搜索成功、失败、无结果保存/读取/展示。

## 收尾状态

Luke 已整体接受本收尾方案，包括 seq 分配与首版输入引用表示。M2 数据模型设计收口；具体 SQL、SDK 格式映射和跨模块交接按本稿继续落实。局部规格未发布为执行 Issue，产品实现与全部验收未运行；没有新的独立审查，此前联合审阅为主 Agent 文档核对，历史委派超时不计通过。M3 后续在新会话继续，本会话到此收尾；不提交、推送或修改 Issue。

学习观察：Luke 已能在具体场景区分原文删除与来源保留、旧产品指令 A 与部署 B、Provider 结果与服务端持久化结果。本轮认可不扩大为掌握 SQL 并发、全部引用映射或真实运行机制。外部主题笔记仍待同步，目标为 /Users/lukemyself/Documents/学习/AI/Agent Harness；本轮没有越过写权限同步，也不以本工程规格替代私人学习笔记。
