# 阶段 1 主会话接续

更新及补录日期：2026-10-24。来源为 Luke 本次接续指令、最新 learning-stage 的记录要求、[Issue #1](https://github.com/lukemyself-hub/sayhear-v2/issues/1)、[ADR 索引](../../../decisions.md)、已有两项功能接续和 PR #4 的 GitHub 合入回执。此前缺阶段总记录，本文件是本次补建，不代表过去已完成总计划确认。

## 当前目标与下一动作

当前交付授权（2026-10-24）：Luke 明确要求“提交 commit，开 PR 合入 main 分支”，本轮可提交、推送、创建 PR 并合入 main，使用 luke-agents。范围仅本次 M2 文档；不修改 Issue #1，不实现或部署。下文历史“未授权提交/发布”不再用于阻止本次 Git/PR 交付；交付结果以实际 PR 状态为准。

最终收口（2026-10-24）：Luke 明确回复“认可，收尾 M2 方案吧”，M2 收尾方案整体接受，含 seq 分配与输入引用首版表示。M2 设计已收口，[规格入口](features/canonical-data-model/spec-draft.md)未发布为执行 Issue，实现/验收未运行。下一会话从 M3 上下文与日期继续，先读总计划、本段和 M2 规格交接表，不重开已接受决定。跨模块待办、外部学习笔记待同步均保留；无活跃委派。本次未提交、推送、创建新会话或修改 Issue。下文“待整体审阅”是此前状态，已被本段覆盖。

本会话收尾（2026-10-24）：Luke 指定只收尾 M2，M3 后续另开新会话。已整理 [M2 收尾规格草稿](features/canonical-data-model/spec-draft.md)，包含四表契约、seq 工程方案、输入引用首版表示、数据库来源校验及跨模块交接和未运行验收。当前为收尾稿待 Luke 整体审阅，不冒记全部工程建议已接受。M3 不在本会话展开；不创建新会话，不提交/推送/发布 Issue，不实现或测试。恢复优先读本段、M2 状态卡及收尾稿；下文旧停点仅作历史。

最新接受（2026-10-24）：Luke 同意 attempt 内 JSON 引用由数据库强制校验来源，暂不新增引用关系表，见 ADR 0010；明确历史裁剪必须保留有效产品指令，部署 B 后旧记录仍可读 A 原文，见 ADR 0016。M2 后续汇总剩余字段及跨模块契约；M3 细化预算与裁剪，具体数据库实现未验证。此前候选和旧停点以本段及 M2 顶部状态卡为准。

当前范围校准与主线：Luke 澄清生成中的目标界面只有停止按钮，没有删除正在生成回答的入口。主 Agent 撤回“删除时是否停止”的确认问题，不增界面功能，不让该假设场景阻塞 M2；M5/M7 出现明确需求再重访。停止沿用保留部分回答的既定语义。当前回到 M2 输入引用 JSON 及同 owner/会话来源约束；下文将生成中删除列作当前必决的段落仅为已撤回的讨论经过。

最新联合审阅停点：两份 M2 字段草案已由主 Agent 核对，见[联合审阅记录](features/canonical-data-model/joint-review.md)。已补幂等意图、首段消息与来源原子保存、准确测量持久化、JSON 来源校验和活动 attempt 竞争要求，非独立审查或运行通过。当前只讨论“删除正在生成的 assistant 回答是否同时停止”，推荐停止并 interrupted、不 fallback，见 ADR 0005 Proposed。此项属 M4/M7 的共享产品边界，会影响 M2 操作与状态，先处理后回主线；不展开删除触发 user 消息或账户清理。M2 仍未整体收口。

最新接受与格式议题：Luke 明确接受 assistant 首段先入库确定位置再展示，已记 ADR 0015；具体 seq 分配与合并算法仍为工程候选。M2 当前补齐格式元数据建议：消息 parts_schema_version 与 input_record.schema_version 独立，实际应用/SDK 版本另记，未来发生真实不兼容再决定迁移或读取转换。不预建复杂兼容框架；消息字段汇总、来源映射和跨模块竞态仍未完整收口，未实现或测试。

当前排序议题：M2 已核对 PostgreSQL sequence、行锁与 READ COMMITTED 官方机制，提出[会话内 seq 分配候选](features/canonical-data-model/evidence/message-seq-allocation.md)，见 ADR 0015 Proposed。用户消息首次入库分配；assistant 第一段正文先入库、确定 seq 后再展示，后续不改号。待 Luke 确认首段多一次数据库等待的体验取舍；具体并发分配、客户端合并与缺口补取仍需 M4/M5 对齐和后续验证。不启用队列或实时订阅，未实现或测试。

当前字段汇总：Luke 已接受输入保存与发送资格的原子写入、finished 与结果一起保存。已建立 [run/attempt 最小结构草案](features/canonical-data-model/run-attempt-draft.md)，建议 run 明确引用产生正文的 output_attempt_id，并约束同 owner、同 run；字段归属、时序与约束仍随完整规格审阅。M2 尚余 seq、格式版本与来源映射细化，跨模块竞态未收口。本次仅文档设计，无实施、测试或 Git 发布。

最新接受与工程细化：Luke 已接受 attempt 生命周期 created/running/finished 与 Provider 结果 not_sent/succeeded/failed/unknown 分列，见 ADR 0010。当前落实状态组合与发送门槛的建议：保存输入和取得 created→running 资格同一数据库操作，只有确认成功的执行方继续发送；running 仍不是 Provider 已收到的证明。随后汇总 run/attempt 最小字段。完整竞态、seq 和表示格式仍未收口，未实现或测试，无新的发布授权。

最新状态决定：Luke 已接受 run 的 created、running、succeeded、failed、interrupted 五状态，见 ADR 0010。M2 当前提出 attempt 的生命周期 created/running/finished 与 Provider 结果 not_sent/succeeded/failed/unknown 分开记录，待确认；首段超时可明确为本地失败原因而远端结果未知。完整状态转换、停止与保存失败的竞争、输入记录与删除的生效顺序仍由 M4/M7 对齐，未实现或测试。

当前学习与下一动作：Luke 已正确回答旧运行仍显示指令 A、已删除消息 102 不再显示原文，证明本场景中能区分当次信息与正文引用。M2 回到完整 run 五状态表审阅，之后细化 attempt 的结果确定性与未发送表示；不重复表决已接受的有限引用方向。完整物理 schema、并发和输入字段仍未收口，外部学习笔记未同步。

最新接受与停点：Luke 在行业调研后明确同意保留引用方向、限定功能、不提前建设复杂工具和场景。ADR 0010 的有限纯文本引用方向已 Accepted，当前进入 attempt 输入记录字段草案；具体 JSON schema、完整 run/attempt 状态字段及 M3/M4/M7 竞态仍未收口。下文 Proposed/等待方向确认是较早讨论经过，不再作为当前状态。无新增实施、测试或发布授权。

当前调研回执：Luke 要求在接受消息引用方案前先查行业最佳实践。主 Agent 已调查 OTel、Langfuse、LangSmith、Vercel AI SDK/Chatbot、LangGraph，见[一手资料报告](features/canonical-data-model/evidence/input-recording-industry-practices.md)：外部内容引用和增量状态保存有直接先例，逐次完整输入也有明确实践，不能将现有候选称为行业通用。ADR 0010 引用方案仍 Proposed，若采用建议限定阶段 1 纯文本及已选 SDK/Provider，不预建通用请求重建系统。独立 investigator 在 300 秒后 TIMED_OUT，无完整报告，非独立审查通过；无活跃委派。下一步向 Luke 解释依据及取舍，再继续审阅。未实现、测试、部署或写入 Issue。

当前候选（覆盖下文旧停点）：已核查 SDK 纯文本及工具转换，见[稳定引用与最终输入](features/canonical-data-model/evidence/message-references-and-final-input.md)。M2 待 Luke 确认 ADR 0010 Proposed 的“终态正文固定、引用加最终结构及当次信息”方向；不重新询问删除后原文不再回看的决定。M3 待细化中断/变化中消息资格与内部裁剪，M4/M7 待对齐终态写保护、迟到写入和删除发送顺序。无新增委派、实现或测试。

当前决定与主线更新：Luke 已明确接受删除单条消息后历史运行详情不再显示其原文，替代此前完整回看的要求，见 ADR 0005/0010。发送前保存原则保持；当前优先评估消息引用加本次独有信息，具体表示与 SDK 最终请求映射尚未确认。下文较早的“旧快照原文保留”摘要是被本决定替代的讨论经过；不自动删除 run/attempt，不把放宽回看扩展为彻底清除所有副本的承诺。Issue #1 的相关验收尚待有发布授权后同步。

最新主线：Luke 已接受捕获最终请求体后先保存再发送的第四步，随后因历史正文在快照中重复存储，要求 double check 消息 ID 引用与存储成本。当前重开快照完整副本及单条删除后保留的取舍，暂停字段细化；旧 Accepted 决定尚未被替代。先区分可删除消息引用、每次完整副本和不可变内容去重，见[存储取舍核对](features/canonical-data-model/evidence/snapshot-storage-tradeoffs.md)。不得把假设量级当实测数据库占用或费用，不自行修改 Issue、执行测试或连接数据库。

当前议题更新：快照布局已接受，主 Agent 已对 `ai@7.0.153` / compatible `3.0.78` 的固定 tag 源码核查[请求体捕获时机](features/canonical-data-model/evidence/request-snapshot-capture-timing.md)。候选方案是在 Provider 专属自定义 fetch 边界先保存最终请求体，再转交网络；保存失败不发送或 fallback。方案尚待 Luke 确认；独立 investigator 在 240 秒后 TIMED_OUT，无完整报告，详情见 M2 局部接续，无活跃委派。当前结论来自主 Agent 直接源码核查，没有独立审查通过、产品构建、测试或真实调用证据。

最新停点：Luke 已接受输入快照存 attempt 的 jsonb 列，不另建快照表，并要求核对关联文档，权威决定见 ADR 0010。owner 与 RLS 直接保护 attempt 行，账户清理随该行删除，单条消息删除不改旧快照。ADR、身份 SPEC 草稿、阶段计划和入口已同步，历史拆表学习示例加后续说明。下一项是快照字段及捕获、保存时序；恢复期限、并发收尾和迟到写入由 M4 细化，完整 schema 仍未收口。Issue #1 未规定必须独立表，本次不因布局调整修改 Issue。下文较早停点仅保留为讨论经过。

最新停点更新：Luke 已接受首段前主动停止也记为 interrupted、不建空 assistant 消息、不自动 fallback，见 ADR 0005。M2 继续 run/attempt 生命周期，当前讲解 Provider 正常完成与应用保存成功的区别；完整状态机、持久化失败与恢复仍未收口。学习表现待场景回访，不因认可决定标为掌握。

最新停点更新：Luke 已认可当前阶段每 owner 至多一个连续会话及 id、owner_id、created_at 的最小结构，见 ADR 0008。M2 当前转入 run/attempt 生命周期，之后讨论恢复和输入快照；消息 seq 分配、格式版本及跨模块约束仍待收口。主路线、fallback 与显式重试的数量关系继承 ADR 0010，不重开已接受决定；本次没有新增实现或外部操作授权。

最新停点：Luke 已接受合成网络搜索的成功、失败、尚无结果三类样本，以及仅保存、读取和运行详情展示的阶段 1 边界，见 ADR 0015。M2 接下来讨论会话容器最小结构及每 owner 数量约束。消息完整 schema 仍未收口：seq 分配与合并、格式版本及跨模块约束继续保留，不能把合成工具议题结束记为消息结构全部完成。

2026-10-24 新一轮接续：当前实际工作区为 `/Users/lukemyself/Projects/SayHear-v2`，分支 `main`，启动干净。已读回 Issue #1，无新评论。Luke 确认同一 run 的主路线与 fallback 固定产品指令，更新从新 run 生效，见 ADR 0016；文件内容 hash 等细节保留为实现建议，随完整规格审阅。当前推进 M2 合成工具记录的验收边界，候选为成功、失败、无结果的最小合成样本，不执行工具。其余模块顺序不变；本轮未提交、推送、修改 Issue、实现或测试。以下为此前接续历史，旧路径及“下一步讨论指令版本”的停点由本段和 M2 顶部状态卡更新。

本次先恢复全阶段视角，补齐 [README](README.md)、[总计划](plan.md)及本文件，再接续 [canonical 数据结构](features/canonical-data-model/session.md)尚未确认的系统记录方案。不重做已完成的消息存储调查，不重新询问 parts、seq、行粒度、run 关联及删除清空决定。

Luke 已明确认可总计划的九个模块及先继续 canonical 数据结构、再按依赖细化其余模块的安排。Tolan 每轮重建上下文的事实问题已回答；Luke 随后认可每次模型请求携带有效指令，以及仓库内独立文本文件随应用部署、修改规则需要重新部署的方案，已记录为 [ADR 0016](../../../adr/0016-per-request-system-instructions.md)。系统记录决定已完成：阶段 1 不保留独立 system 聊天记录，原验收改为核对实际请求的指令链路，见 ADR 0016。下一步讨论指令文件的版本追踪。

本次体验目标是保留能解释实际输入与来源的聊天基础；学习目标是区分当前运行的产品指令、库中消息与运行记录、实际输入快照。总计划确认已完成；系统记录一项已收口，其余结构讨论继续推进。

当前议程为指令文件的版本追踪与实际副本。系统记录一项已收口：阶段 1 不保留独立 system 聊天行，原验收改为核对实际请求的指令链路，见 ADR 0016；Issue #1 和 ADR 0010 的措辞待修订。之后讨论合成工具记录，不把一次消息表讨论当成全阶段收口。

## Git、授权与并行状态

- 启动检查为干净的 detached HEAD；已 fetch `origin/main`，从 `c306c6ba46fabe9be59295ac5238b0e60be36be7` 建立 `codex/stage-1-learning-resume`。基线是 PR #4 的合入提交，GitHub 已读回 `MERGED`。
- 当前 worktree 为 `/Users/lukemyself/.codex/worktrees/bb3e/SayHear-v2`；后续模块切换继续本分支，不自动另开。
- Luke 本次授权建立讨论分支、必要文档补录和继续讨论，不包含产品实现、构建测试、安装工具、资源创建、用户库访问、部署、修改 Issue、commit、push、PR 或 merge。
- 历史记录中的收尾 Git 发布授权仅用于对应轮次，不自动继承。Issue 的 `ready-for-agent` 不扩大本次授权。
- 2026-10-24 收尾：Luke 明确授权将本轮文档提交、推送并通过 PR 合入 main，不包含产品实现、修改 Issue、云资源或用户库访问。下一 session 从最新 `main` 接续，不继承本次发布授权。
- 启动没有并行未提交改动，无活跃委派。pstack 项目 checkpoint 指针为 missing；按本次明确指定的阶段文件和已合入分支材料恢复，没有扫描无关聊天。

## 全阶段进度

完整依赖、调研点、学习目标及验收归属见 [plan.md](plan.md)，以下仅保留接续摘要。

| 模块 | 当前状态与下一步 |
| --- | --- |
| M1 身份与环境隔离 | 设计收口，局部 SPEC 草稿未发布，全部产品验收未运行；逐表覆盖及 checkpoint 集成依赖 M2/M4 |
| M2 canonical 数据结构 | 设计已收口，Luke 整体接受；[收尾规格](features/canonical-data-model/spec-draft.md)未发布，实现与验收未运行 |
| M3 上下文与日期 | 连续会话及预算原则已定；时区、选择策略与部分回答使用等待细化 |
| M4 聊天执行与 Provider | 两段预算、一次 fallback、关闭思考等已定；事件、状态机、保存恢复及具体预算待细化 |
| M5 聊天界面与历史 | 旧设计复用边界已定；界面与新事件、排序契约适配待细化 |
| M6 运行详情 | 库内记录、实际输入与来源可查已定；字段、捕获与视图待细化 |
| M7 删除与清理 | 后续排除、旧快照保留、清空及迟到写入保护已定；运行中删除取消及完整清理流程待细化 |
| M8 合成数据与验收 | 数据类别、责任与四层验证已定；夹具、装载、证据模板及执行方式待细化 |
| M9 私有部署与恢复 | 地区、两库、每日加密备份等已定；运维、恢复、部署与真实观测待完成设计及获授权执行 |

## 跨模块约束与待定事项

- Accepted ADR 0001–0016 继续有效；物理 schema 尚未完整确定。身份模块不预先决定数据列，消息存储也不改变 owner、RLS 与同 owner 引用契约。
- 阶段 1 不设独立 system 聊天消息行，已确认。实际指令经请求快照保存与展示；ADR 0010 已同步；Issue #1 的系统消息措辞待获发布授权后修订。指令版本标识细节和 M3/M6 契约继续细化。
- 合成工具记录用于存储验收，不授权阶段 1 执行工具；采用 parts 后须替换旧独立 tool_call/tool_result 行草案。
- 输入快照须为 SDK 转换后的实际发送内容副本，不是消息 id 引用，也不作为新输入来源。已接受合并到 attempt 的 jsonb 列，权限和账户清理随该行，见 ADR 0010；字段与捕获时序待细化。历史调研中“自行组装内容即可替代最终快照”的推断不能覆盖 Issue 契约。
- 生成中继续发送的队列范围、首次可见事件及生成中删除是否停止未定；不因兼容性设计自动纳入产品范围。
- ADR 0004 已有版本核对提示，保留旧实验上下文；实施时按锁定版本核实系统参数和请求捕获，源码核查不当作新版运行通过。
- 路线图仍保留“阶段 0 尚未正式开展”等早期启动描述，与后来的阶段 0 记录、Issue #1 及已接受 ADR 时序不同。本次不改写旧历史，当前状态按后续有日期的记录及本阶段总接续读取。
- Provider、平台、SDK 与数据库能力是易变证据，采用前再核实；本次没有重新调用 Provider、连接数据库或验证托管行为。
- `docs/agents/domain.md` 仍有“ADR 数量为 0”的启动旧描述，与实际决策索引不符。当前依据索引及实际 ADR 文件定位，不把该描述作为当前数量，也不在此任务顺带改写无关入口。

## 学习、笔记与回访

沿用[身份理解记录](features/identity-data-ownership/learning-history.md)、[数据结构讨论历史](features/canonical-data-model/discussion-history.md)与[阶段 0 学习状态](../stage-0/session.md#学习状态)。已有表现是当次证据，不能把已讲解或文档完成标为掌握。

当前要回访“存储格式不授予指令权限”“记录副本与实际发送的关系”。Luke 主动询问 Tolan 每轮重建是否包含系统指令、能否增强产品规则一致性，表明正在检查每轮模型调用的输入机制，尚无新应用判断证据。已定点核查并记录[公开资料及建议边界](features/canonical-data-model/evidence/tolan-per-turn-context-and-system-instructions.md)；需澄清每次调用提供指令与每轮新增系统消息行是两件事。后续结合设计和运行回访 owner 外键、真实续期、单条删除不触发级联、迟到写入保护、排序与上下文选择的区别。

外部笔记目标为 `/Users/lukemyself/Documents/学习/AI/Agent Harness/topics/` 与 `learning-records/`。已确认目标目录存在，本 worktree 无 `study-notebook` 链接；未写外部目录，未同步笔记。待同步摘要为身份学习记录及数据结构讨论历史中的机制、理解表现、校准与回访点，并补充“每次发送指令与新增消息行的区别”。先核对已有分类和并行写入，再按正常写权限处理；仓库历史不是永久笔记。Luke 对每次请求携带指令表示认可，未给出新场景判断，不据此标为掌握。

## SPEC、交付与构建交接

- [阶段 SPEC 入口](spec.md)指向 Issue #1；初始 SPEC 已发布，后续设计细化未全部发布，阶段完整设计未收口。
- 身份[局部草稿](features/identity-data-ownership/spec-draft.md)未发布，canonical 尚无完整局部 SPEC；不自行新建竞争的阶段总 Issue。
- 历史文档 [PR #4](https://github.com/lukemyself-hub/sayhear-v2/pull/4) 已合入，合入 SHA 为上述基线。本次文档尚未提交、推送或创建 PR。
- 本次按 Prove It Works 原则检查实际文档与 Git 状态：7 份规划文档的 78 个本地链接及标题锚点有效，M1–M9 对 Issue #1 的 28 条用户故事均有归属，换行和 diff 格式检查通过，HEAD 与 fetch 后的 origin/main 一致。这些检查不代表设计已确认，也不是独立审查；未运行产品构建、测试或验收。
- 阶段交接前按总计划逐项核对设计、共享契约、验收与 ADR 覆盖，获得对应发布授权后细化 Issue #1，不能以 M2 收口代替全阶段就绪。
- 将来构建先读 Issue #1、总计划、相关 ADR 和[本地环境规则](../../../agents/local-environment.md)，核对获准实施范围及资源。第一步是工具链、隔离测试环境及最小数据契约前置；当前不执行。新构建分支从届时 fetch 后核实的最新 `origin/main` 建立。
