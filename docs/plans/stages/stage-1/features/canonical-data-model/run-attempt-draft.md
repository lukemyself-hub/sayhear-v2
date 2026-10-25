# run/attempt 最小结构草案

最终状态（2026-10-24）：Luke 已整体接受 [M2 收尾规格](spec-draft.md)，M2 设计收口。以下形成过程中的“候选/待审阅”以收尾规格及最新 ADR 为准；具体 SQL、SDK 映射和跨模块待办仍需后续落实，未实现或验证。

日期：2026-10-24。状态：设计草案，字段名及新增关系待完整审阅，未实现或验证。范围真源仍为 Issue #1；本文件只汇总数据设计，不复制阶段需求。已接受的数量、权限、状态与发送门槛见 [ADR 0010](../../../../../adr/0010-minimal-data-contract-and-owner.md)，指令规则见 [ADR 0016](../../../../../adr/0016-per-request-system-instructions.md)。

## run：整次应用执行

| 字段或字段组 | 作用与约束 |
| --- | --- |
| id、owner_id | 身份与直接归属；继承 UUIDv7、RLS 和同 owner 引用 |
| trigger_message_id | 引用触发本次运行的 user 消息；必须属于当前 owner，角色约束的具体实现待 schema 汇总 |
| client_request_id | 幂等标识；同 owner 唯一，显式重试使用新的请求标识 |
| request_fingerprint | 推荐：服务端对稳定规范化后的提交意图生成摘要，包含发送/重试动作及目标、内容等必要差异；不信任客户端提供摘要，不含令牌或请求头。重复请求标识且意图相同才复用；意图不同则拒绝冲突，不创建另一份消息或调用 Provider。算法和表示须稳定，不由 SDK 转换或当前历史决定 |
| status | 已接受 created/running/succeeded/failed/interrupted |
| end_reason、failure_stage | 为什么结束，失败发生在准备、持久化、Provider 等哪一层；具体原因值由 M4 错误映射确认，不保存可能携带正文或凭据的原始错误对象 |
| created_at、started_at、ended_at | 分别记录登记、应用执行开始、收口；开始和结束前的时间为空，结束与终态原子写入 |
| deadline_at | 推荐：从请求入口的总预算推导可靠执行截止，覆盖 created 状态的恢复依据；不以数据库 created_at 重新起算完整预算，fallback 不重置。恢复宽限和具体含义与 M4 最终对齐 |
| instruction_record | 推荐：保存本 run 选定的产品指令正文及内容标识，主路线与 fallback 共用这一固定来源；各 attempt 仍记录最终协议表达与当次注入内容。只存 hash 不足以读取旧指令 |
| build_info | 推荐：应用及读取/转换所需 SDK/适配器版本；有版本来源才记录，不伪造未知值。具体与输入表示版本的归属由 M6 汇总 |
| output_attempt_id | 推荐新增关系：明确产生 assistant 正文的 attempt；无正文则为空；一旦建立输出来源，不能被后续另一个 attempt 覆盖 |

不在 run 再复制一组实际 Provider/模型、usage 或耗时汇总列；单次观测以 attempt 为准，可推导的汇总在查询时计算。assistant 消息已经引用 run，草案不再添加 run.assistant_message_id 作为第二套权威关系。

## attempt：单次 Provider 尝试

| 字段或字段组 | 作用与约束 |
| --- | --- |
| id、owner_id、run_id | 身份、直接归属、所属 run；组合外键保证同 owner |
| attempt_no | 推荐 1 或 2，run 内唯一；最多两次，不通过更多行模拟 SDK 隐式重试。编号存在不证明已经发送 |
| status、provider_result | 已接受 created/running/finished；未 finished 时结果为空，finished 时为 not_sent/succeeded/failed/unknown 之一 |
| end_reason、failure_stage | 区分首段超时、显式错误、用户停止、失联等事实；fallback 判断使用已定条件，不只看 provider_result |
| provider、requested_model | 本次选择的服务商与请求模型；不把两家服务只当成一个可变 base URL |
| reported_model、provider_response_id | Provider 实际报告的身份与响应标识，可能缺失；不拿配置模型冒充实际报告，也不把无响应 ID 当作未发送证明 |
| input_record | jsonb；保存最终有序结构、稳定正文引用、本次参数/时间/指令表达、来源校验与选择理由等。表示格式版本随记录保存；具体 JSON schema 尚未冻结 |
| created_at、dispatch_started_at、first_text_at、ended_at | 登记、取得发送资格、首次非空正文观测、尝试收口。dispatch_started_at 在发送门槛事务记录，语义为本地进入调用阶段，不命名为 delivered_at；精确网络耗时使用本次执行的单调计时观测，不能把数据库准备等待算成 Provider 耗时 |
| first_text_latency_ms、provider_elapsed_ms | 推荐补充：分别持久化真实网络调用起点到首次非空正文、到本地观察该调用结束的单调计时差。后者不证明 Provider 已停止或停止计费，也不包括后续数据库保存等待；未调用或缺少可靠观测为空，正常零值与未知有区别。响应刷新后依赖保存的测量，不能重新用 dispatch_started_at 相减冒充精确耗时 |
| finish_reason | 如可获得，保留 Provider/SDK 原始结束原因；不以数据库 CHECK 穷举外部值，逻辑使用前映射为产品原因 |
| usage、cost_info | 可获得的 token 与成本证据，推荐 jsonb 保留必要字段及口径；缺失为 unknown/空，不默认等于零，不编造订阅摊销金额。具体来源与字段由 M6 对齐 |

输入记录在发送前准备失败时可以不存在；有输入记录也不证明网络发送或远端收到。输入与 created→running 资格一起持久化，finished/result/end_reason/ended_at 一起收口。数据库不可写时不能声称这些字段已可靠落库。

同一 run 内 attempt_no 唯一且只能为 1/2；建议数据库约束同一 run 至多一个 created/running attempt，阻止主路线尚未收口时并发建立备用。第二次尝试的授权原因、第一条已结束、run 仍可执行和剩余预算须一并检查，不能只靠编号小于 3。已终态 run 不再启动新的 attempt；并发停止与备用创建的具体条件更新由 M4 对齐。

input_record 内的消息 ID 是跨记录引用，但 JSON 字段不会自动成为外键。最终数据库设计必须为其提供不可绕过的同 owner、同目标会话与存在性校验，并在读取时继续按 owner 解析；只保护 attempt 本行的 RLS 不足以证明 JSON 内来源合法。可采用数据库触发校验或显式引用关系表等方式，具体实现仍待输入 JSON 与最终 schema 联合审阅，不在本草案擅自新增产品表。删除生效顺序与选取资格另按 M3/M7，不能将引用合法性校验当作已解决全部删除竞态。

## 输入引用的最小表达与已接受的来源校验

来源校验方向已获 Luke 接受，见 ADR 0010；最小表达仍为设计草案，未冻结 JSON schema，也未实现。纯文本示例中的 101/102 是便于阅读的消息代号，实际仍用 UUID。记录应保留实际协议消息的顺序、角色和 content 的字符串或数组形状；正文位置用明确的自有引用节点表示，例如来源为消息 102 的第 0 个 text part，多个来源按指定顺序直接拼接。这个节点属于 input_record，不写进 AI SDK parts，也不发送给 Provider。最终协议中的其余实际参数与本次独有文字按原值记录，省略值保持省略，不补猜默认值。产品指令可关联本 run 已保存的固定正文，但必须记录本次实际协议表达与注入差异。

发送前以当次读取的来源解析候选记录，核对其 JSON 值、数组顺序、角色和正文与已捕获请求相同，再按既定门槛保存并发送原请求。映射来自组装过程，不能仅以文字相同反推来源。这里只支持已确认的有限形状，不预建工具或多模态通用解释器。

来源校验推荐继续保留 attempt 的 jsonb 列，以数据库触发校验覆盖 input_record 的插入与修改，并保护 owner/run/会话来源关联不被普通更新改挂。校验从 attempt 所属 run 的触发消息推导目标会话，不信任 JSON 自报的 owner 或 conversation。逐一确认来源存在、同 owner、同目标会话，以及引用 part 的类型和范围合法。正文摘要用于发现意外改写；读详情时仍按 owner 读取、优先检查 deleted_at，删除显示缺失，校验不符不展示新内容冒充旧输入。

相比另建引用关系表，此候选少维护一套关系行，但失去普通外键的直接表达，须维护 JSON 版本解析、反向关联保护和覆盖全部写入口的数据库校验。若阶段内确实需要大量按来源反查引用，或校验明显膨胀，再比较显式关系表。当前不新增产品表；Luke 已于 2026-10-24 接受这一方向；触发器细节与覆盖性仍待规格及后续验证。校验合法来源不等于解决删除与发送的时序，后者继续归 M7/M4；触发校验也不重新执行上下文选择或 SDK 转换。

历史预算裁剪不得移除有效产品指令。旧记录须保留当次 A 原文，部署 B 后仍读取 A；可关联 run 中固定保存的正文，不以当前文件或 hash 替代。详见 ADR 0016。

## 输出来源关系的建议

链路是 assistant 消息 → run → output_attempt_id → Provider/模型。run 还可列出其全部 attempt，但实际输出来源不靠“最后一条”或 UI 列表顺序猜测。

output_attempt_id 指向的 attempt 必须与该 run 同 owner、且其 run_id 就是当前 run；仅同 owner 不足以防止误挂到同一用户的另一运行。物理组合外键、唯一键与引用循环的创建顺序在最终 schema 中明确，不为这一草案立即创建迁移。

输出来源在 assistant 第一段正文建立时确定，有部分回答但后来中断仍保留它；此时 attempt 的 provider_result 可以 unknown，不能约束只有 succeeded 的 attempt 才能成为输出来源。首段前全部失败或停止不创建空 assistant 消息，output_attempt_id 为空。来源关联与首段正文持久化如何原子完成由 M2/M4 对齐。

联合审阅补充的事务要求：首段建行时，将消息首段与 seq、run.output_attempt_id、attempt.first_text_at 的首次观测及可获得的首段计时结果作为同一个 owner/RLS 数据库操作保存，确认提交后再发布消息开始和首段。序号写入依既定分配规则；不得先发布来源缺失的消息，再单独补来源。结果丢失时由原有消息身份、run 至多一条 assistant 和不可变输出来源进行幂等核对，不无条件新建另一条回答。

该要求是完整规格的工程补充；若提交失败或结果不确定，仍按已有保存失败与不重放原则处理，不能凭未向浏览器显示就切换 Provider。锁顺序、已停止 run 拒绝首段写入及迟到回调由 M4/M7 对齐，不能仅因一次原子操作的建议存在便宣称所有竞态已通过。

## 仍待收口

- 本草案的字段名、JSON 表示、输出 attempt 引用和具体数据库约束尚未获得逐项接受，随完整方案审阅。
- M3 决定历史选择、部分回答/变化中消息资格、时区和预算裁剪；input_record 提供承载位置，不自行决定这些产品行为。
- M4 决定截止与恢复宽限、错误原因映射、各终态转换、停止/保存失败/迟到回调的竞争顺序和可证明的计时位置；未执行验证。
- M6 确认实际模型、usage、成本与输入读取的字段，避免建立重复真源或把未知值默认成零。
- M7 对齐删除与准备输入/发送/保存的生效顺序；已定删除后运行详情不再显示原文，账户清理删除所有归属内容。
- 消息 seq 的分配与合并、parts 与输入记录的格式版本仍在 M2，未由本草案自动完成。
