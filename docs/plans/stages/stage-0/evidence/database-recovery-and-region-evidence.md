# 数据库恢复目标（RPO）成本选项与地区组合证据

调研日期：2026-10-22（全部当日核验）。方式：只读调研，仅官方一手来源；未创建云资源、未连接数据库、未读取凭据、未提交 git。
用途：为 `database-auth-long-term-comparison.md` 的数据库决定补齐「恢复目标对应的成本选项」与「地区组合」两块证据。主推荐仍是 Supabase Postgres + Supabase Auth，**尚未被 Luke 接受**，本文不替 Luke 做选择。

产品前提（来自既有文档，非本文结论）：私人日记式聊天 Agent，初期仅 Luke 一个用户，数据量 <1 GB/年，Web 部署 Vercel，两个隔离库（测试库 + 用户库）。

标注约定：`[文档原文]` = 官方页面逐字可查；`[推断]` = 由原文合理推导但官方未明写；`[unknown]` = 官方来源未见，不猜。

---

## 1. 不开 PITR 时各套餐的备份到底是什么

### 1.1 频率与保留

| 套餐 | 是否有每日备份 | 保留 | 证据 |
| --- | --- | --- | --- |
| Free | **无** | — | `[文档原文]` "We recommend that free tier plan projects regularly export their data using the Supabase CLI `db dump` command and maintain off-site backups."；定价页 Free 行 Backups = "Not included" |
| Pro | 有，每日一次 | "Pro Plan projects can access the last 7 days of daily backups." | `[文档原文]` |
| Team | 有 | 14 天 | `[文档原文]` "Team Plan projects can access the last 14 days" |
| Enterprise | 有 | 最多 30 天 | `[文档原文]` |

开篇原文：`[文档原文]` "We automatically back up all Pro, Team, and Enterprise Plan projects on a daily basis. You can find backups in the **Database** > **Backups** section of the Dashboard."

备份形态：`[文档原文]` "All projects on Postgres `15.8.1.079` and newer use the newer physical backup process."（更早版本需升级后自动切换）

### 1.2 能否自助下载 / 恢复 / 恢复粒度

- **不能下载。** `[文档原文]` "For security purposes, daily backups do not store passwords for custom roles, and you will not find them in downloadable files." 与关闭 PITR 后的说明 "You can still use physical backups for restoration, but they are not available for direct download."
- **恢复是自助的，但只能走 Dashboard / Management API。** `[文档原文]` "You can access daily backups in the **Database** > **Backups** section of the Dashboard and restore a project to any of the backups."；另提供 `v1/projects/$PROJECT_REF/database/backups` 列表与 `restore-pitr` 两个 Management API 端点。
- **恢复覆盖整个项目，不是单表。** `[文档原文]` "The project is inaccessible during this process, so plan for downtime beforehand. Downtime depends on the size of the database—the larger it is, the longer the downtime will be." 且恢复前后需 drop / 重建 subscriptions 与 replication slots。`[推断]` 即整库回滚到某个备份点，期间项目不可用；没有官方「只恢复一张表」的路径。
- Free 层：`[推断]` 平台侧无任何可恢复备份，最坏情况是**全量丢失**（与 Pro 的「丢一段时间」性质不同）。

### 1.3 最坏情况丢多少数据

- Pro 每日备份：`[文档原文]` "Even with daily backups, you could still lose a day's worth of data." → 官方直接承认最坏丢约一天数据。
- `[推断]` 官方未写每日备份的具体触发时刻，也未承诺失败时的兜底频率；按「一天一次」推算，最坏情况 RPO ≈ 24 小时，且保留期 7 天决定的是「能回退到多早」，不等于 RPO。
- Free 层：`[推断]` 最坏 = 全部丢失（平台无备份）。
- 备份**不含** Storage 对象：`[文档原文]` "Database backups do not include objects you store via the Storage API, as the database only includes metadata about these objects. Restoring an old backup does not restore objects you deleted after that backup."

### 1.4 auth schema 是否在备份内（沿用旧结论，仍未解）

`[文档原文/缺失]` 备份页全文未出现 `auth` schema 或 `auth.users`；它只排除 custom roles 的密码，不涉及内置 auth 用户表。`[推断]` auth schema 是 Postgres 数据，库级物理备份按目录快照，"Physical backups provide a snapshot of the underlying directory of the database"，故 auth 表大概率在备份范围内——但这是推断，不是保证。
一个正向旁证：`[文档原文]` clone-project 页「Restore to a New Project」明确列出会转移 "Auth user data (user accounts, hashed passwords, and authentication records from the auth schema)"，说明备份体系里确实携带 auth 数据。该功能为 Beta、仅付费套餐、且要求源项目启用 physical backups。
→ 仍需恢复演练核实（沿用旧文档第 5 节缺口 2）。

来源：https://supabase.com/docs/guides/platform/backups ；https://supabase.com/pricing ；https://supabase.com/docs/guides/platform/clone-project

---

## 2. 不买 PITR 的低成本替代

### 2.1 官方确实文档化了自行逻辑备份

- `[文档原文]` "To generate a logical backup yourself, use the Supabase CLI `db dump` command."
- `[文档原文]` "If you need to download a backup after disabling PITR, you need to take a manual legacy logical backup using the Supabase CLI or pg_dump."
- `[文档原文]` 对 Free 层：regularly export + maintain off-site backups。
- 官方 CLI 备份指南给出了完整三步（roles / schema / data）：
  ```
  supabase db dump --db-url [CONNECTION_STRING] -f roles.sql --role-only
  supabase db dump --db-url [CONNECTION_STRING] -f schema.sql
  supabase db dump --db-url [CONNECTION_STRING] -f data.sql --use-copy --data-only -x "storage.buckets_vectors" -x "storage.vector_indexes"
  ```
  并要求先装 Supabase CLI **与 Docker Desktop**（`db dump` 在容器里跑 pg_dump）。

### 2.2 关键坑：默认 dump 不含 auth schema

`supabase db dump` 参考页原文：
- `[文档原文]` "Runs `pg_dump` in a container with additional flags to exclude Supabase managed schemas."
- `[文档原文]` "The ignored schemas include auth, storage, and those created by extensions."
- `[文档原文]` "The default dump does not contain any data or custom roles." "To dump those contents explicitly, specify either the `--data-only` and `--role-only` flag."

→ `[推断]` 按官方三步法做出来的备份**不包含 `auth` 用户表**，即账号本身（`auth.users`）不在其中。若账号数据只存在于 Supabase Auth，靠 `db dump` 自行备份无法恢复登录账号；要么额外单独处理 auth schema，要么接受该缺口。
`[unknown]` CLI 参考页没有说明 `-s/--schema` 传 `auth` 能否绕过 managed-schema 排除，也没有说明 `--data-only` 是否会带上 `auth` 的行数据。不得断言可以。
官方 CLI 备份指南也只说了 auth 的**定制物**要单独恢复：`[文档原文]` "If you have modified the `auth` and `storage` schemas in your old project, such as adding triggers or Row Level Security (RLS) policies, you have to restore them separately." —— 这是指自定义触发器/RLS，不是 auth 用户数据。

### 2.3 连接方式

- `[文档原文]` 官方 CLI 备份指南默认推荐 **Session pooler** 连接串："Use the Session pooler connection string by default. If your network supports IPv6 or you have the IPv4 add-on enabled, use the direct connection string."（session pooler 端口 5432，用户名 `postgres.[PROJECT-REF]`；direct 端口 5432，用户名 `postgres`）
- `[文档原文]` 连接页对 pg_dump / 备份恢复类操作的归类：direct connection，"These are single sessions and Postgres native commands."；IPv4-only 网络用 session mode 作为替代。
- `[文档原文]` "Direct connections are on IPv6, or on IPv4 if the project has the IPv4 add-on."；"The shared pooler is IPv4-only on every plan."
- `[推断]` 定时备份若放在 Vercel Functions 里跑 `db dump`，需要容器环境，与 Functions 运行时不完全匹配；更现实的载体是 GitHub Actions（runner 有 Docker）。但——
- `[unknown]` **本次未在 Supabase 官方文档中找到任何「用 GitHub Actions 定时备份」的官方页面或示例**。官方只提供手动 CLI 流程 + 「定期导出、离线保存」的建议。定时调度属于自行实现，官方不为其正确性背书。

来源：https://supabase.com/docs/reference/cli/supabase-db-dump ；https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore ；https://supabase.com/docs/guides/database/connecting-to-postgres

---

## 3. PITR 当前价格与前置条件（核对旧文档）

| 项 | 现行官方值 | 与旧文档（"约 $100/月、需 Small compute"）是否一致 |
| --- | --- | --- |
| 7 天 | `[文档原文]` $0.137/小时，约 $100/月 | 一致 |
| 14 天 | `[文档原文]` $0.274/小时，约 $200/月 | — |
| 28 天 | `[文档原文]` $0.55/小时，约 $400/月 | — |
| 最低 compute | `[文档原文]` "Projects that want to use PITR must also use at least a Small compute add-on to ensure smooth functioning."（Small = $15/月） | 一致，是 Small 不是 Large |
| 是否替换每日备份 | `[文档原文]` "If you enable PITR, we will no longer take Daily Backups. PITR provides finer granularity than Daily Backups, so running both is unnecessary." | 一致 |
| 可用套餐 | `[文档原文]` "Pro, Team and Enterprise Plan projects can enable PITR as an add-on."（Free 不可用） | 一致 |
| RPO | `[文档原文]` "By default, we back up WAL files at two-minute intervals... Overall, in the worst case scenario, PITR achieves a Recovery Point Objective (RPO) of two minutes." | 旧文档未写 RPO 数字，此处补齐 |

**结论：旧文档「约 100 美元/月、需至少 Small compute、替换每日备份」三项在 2026-10-22 仍准确。** 需修正/补充的只有：官方现在明确给出了 RPO = 最坏 2 分钟，以及 14/28 天价格。

成本算式（`[推断]`，基于上表与定价页 compute 价）：
- 单用户库：Pro $25 + Small $15 − $10 compute 抵扣 + PITR 7 天 $100 = **约 $130/月**。
- 用户库 + 测试库同层：Pro $25 + Small $15 + Micro $10 − $10 抵扣 + PITR $100 = **约 $140/月**（与旧文档一致）。
- `[unknown]` 定价页写 "$100 per month per 7 days retention"，未明说 PITR 附加费是按项目还是按组织计；按项目计是合理推断，采用前需以实际账单核对。

来源：https://supabase.com/docs/guides/platform/backups ；https://supabase.com/docs/guides/platform/backups（PITR 定价 partial）；https://supabase.com/pricing

---

## 4. 项目暂停规则与测试库放 Free 层

- `[文档原文]` "Supabase pauses Free Plan projects that show low activity over a 7-day period"
- `[文档原文]` "Projects under a paid plan cannot be paused and are not subject to automatic pausing for inactivity."（同页另一处："Paid projects cannot be paused and are not subject to pausing for inactivity."）
- `[文档原文]` "A Free plan project is considered inactive if it does not receive sufficient user database activity over the past week."；"Typically a few user requests to the database each day over the previous week is enough to keep the project from being paused."
- `[文档原文]` "You can restore a paused project for up to 1 year after it was paused"（该页小标题仍写 "90-day-window-to-restore"，正文为 1 年 → `[unknown]` 正文与小标题不一致，需向 Supabase 确认）
- `[文档原文]` 定价页：Free "Free projects are paused after 1 week of inactivity."、"Limit of 2 active projects."、Free 限额 500 MB 库 / 5 GB egress / 50,000 MAU。

**测试库放 Free 层可行性：`[推断]` 可行，但有两个真实约束。**
1. 每周需要有真实数据库活动，否则被暂停；`[推断]` 自动化测试若每天连库跑就能满足，纯静态/无人访问的测试库会中招。
2. Free 层平台无任何备份（见 §1.1），测试库的数据丢失没有平台兜底；`[推断]` 对测试库通常可接受，但恢复演练会受影响（没有官方恢复路径可演练）。
另外 Free 限 2 个 active projects，`[推断]` 若 Luke 只想保留一个 Free 名额给测试库，需注意不要占满。

来源：https://supabase.com/docs/guides/platform/project-pausing ；https://supabase.com/pricing

---

## 5. 地区：可用性与「函数地区 × 数据库地区」配对

### 5.1 Supabase 地区（原文）

`[文档原文]` 三个目标地区都可用，且是精确 AWS region（非 general region grouping）：

| 目标 | Supabase 名称 | 代码 |
| --- | --- | --- |
| 东京 | "Northeast Asia (Tokyo)" | `ap-northeast-1` |
| 新加坡 | "Southeast Asia (Singapore)" | `ap-southeast-1` |
| 首尔 | "Northeast Asia (Seoul)" | `ap-northeast-2` |

相关但未被问的：`[文档原文]` "South Asia (Mumbai), `ap-south-1`"、"Oceania (Sydney), `ap-southeast-2`"。
`[文档原文]` **大阪不在 Supabase 可选地区列表中**（Vercel 有 `kix1` 大阪，Supabase 无对应）。
`[文档原文]` "Each Supabase project is deployed to one primary region. Choose the location closest to your users for the best performance."；"The region you choose also determines where your primary project data is stored."
`[文档原文]` "Note: General regions aren't yet supported for read replicas or management via the API."
`[unknown]` 该页未写「哪些套餐能选哪些地区」。

### 5.2 Vercel Functions 地区

`[文档原文]` 默认地区："By default, Vercel Functions execute in *Washington, D.C., USA* (`iad1`) for all new projects"。
`[文档原文]` Hobby 可以改单地区（Functions 限制表 Regions 行）："Runs in a single region by default (`iad1`), which you can change." —— 即 **Hobby 能把唯一地区设成 hnd1 / sin1 / icn1**。
`[文档原文]` 各地区数量上限（Functions region 页 Limits 表）：

| Plan | Function regions |
| --- | --- |
| Hobby | Single region |
| Pro | 5 regions |
| Enterprise | All regions |

`[文档原文]` "Deploying to more regions than your plan allows causes the deployment to fail before the build step."
`[文档原文]` 多地区故障转移仅 Enterprise："Setting failover regions are available on Enterprise plans"；"Per-function `functionFailoverRegions` is Enterprise only and accepts up to 4 region identifiers."
`[文档原文]` Vercel 地区代码与参考位置：`hnd1` = `ap-northeast-1` Tokyo, Japan；`sin1` = `ap-southeast-1` Singapore；`icn1` = `ap-northeast-2` Seoul, South Korea；`kix1` = `ap-northeast-3` Osaka, Japan。
`[文档原文]` "Functions should be executed in the same region as your database, or as close to it as possible, for the lowest latency."
`[unknown]` Functions region 页正文说 "Pro and Enterprise teams can deploy Vercel Functions to multiple regions"，limits 表写 Pro = 5 regions；另有一条 changelog 标题为 "Pro customers can now configure up to 3 regions for Vercel Functions"，与 5 不一致。`[推断]` 对「单地区」方案无影响，多地区数量采用前需确认。

### 5.3 配对表（只列事实，不推荐）

前提：Vercel 建议函数与数据库同区；Hobby 只能选**一个**函数地区，Pro 最多 5 个。

| 配对 | 函数地区 | 数据库地区 | 同区？ | 备注 |
| --- | --- | --- | --- | --- |
| A | `iad1`（默认） | `ap-northeast-1` 东京 | 否 | 默认配置，函数在美东、库在东京，跨区延迟最高 |
| B | `hnd1` | `ap-northeast-1` 东京 | 是 | 代码同为 `ap-northeast-1`，命名一致便于核对 |
| C | `sin1` | `ap-southeast-1` 新加坡 | 是 | 同上 |
| D | `icn1` | `ap-northeast-2` 首尔 | 是 | 同上 |
| E | `hnd1` | `ap-southeast-1` 新加坡 | 否 | 同为东北亚/东南亚但不同区 |
| F | `sin1` | `ap-northeast-2` 首尔 | 否 | 不同区 |
| G | `kix1` 大阪 | — | — | **不可行**：Supabase 无大阪地区 |
| H | `iad1`（Hobby 单区） | 任选 | 视库而定 | Hobby 无法同时覆盖东京/新加坡/首尔，只能选一个 |

`[推断]` 若 Luke 最终在东京/新加坡/首尔中选库，函数地区设为对应代码即可同区；Hobby 单地区限制不影响单库方案，只影响「未来多地区冗余」。

来源：https://supabase.com/docs/guides/platform/regions ；https://vercel.com/docs/regions ；https://vercel.com/docs/functions/limitations ；https://vercel.com/docs/functions/configuring-functions/region

---

## 6. 三档 RPO 的最便宜实现方式与月费

均为 `[推断]`，基于本文已核实的单价，非官方报价单。

| RPO | 最便宜实现 | 月费 | 依据与保留期 | 主要风险 |
| --- | --- | --- | --- | --- |
| **24 小时** | Pro 用户库 + Free 测试库，靠平台每日备份（不开 PITR） | **约 $25** | Pro $25 + Micro $10 − $10 抵扣；保留 7 天 | 官方承认最坏丢一天数据；备份不可下载；恢复是整库且期间项目不可用 |
| 24 小时（备选） | Free 库 + 自行 `db dump` 定时导出 | 约 $0 | 无平台备份，靠自建 | `[推断]` 默认 dump **不含 auth schema**，账号数据不在备份内；Free 会暂停；需自建调度与异地存储 |
| **1 小时** | Supabase 无 1 小时档；要么自建每小时逻辑导出，要么直接上 PITR | 自建：约 $0 + 调度成本；上 PITR：约 $130 | 自建无官方产品支持（`[unknown]` 无官方 GitHub Actions 备份文档）；Vercel Hobby cron 每天只能跑一次（"Hobby accounts are limited to daily cron jobs"），每小时需 Vercel Pro（$20/月）或 GitHub Actions | 自建同样有 auth schema 缺口；PITR 一步到位但贵 |
| **几分钟（官方值 2 分钟）** | Supabase PITR 7 天 | **约 $130**（单库）；约 $140（库+测试库同层） | $25 + Small $15 − $10 + $100；14 天约 $230，28 天约 $430 | 替换每日备份；需 Small compute；Storage 对象仍不在内 |
| 几分钟（跨方案） | Neon Launch 含 7 天历史窗口 + instant restore | 约 $77.4 + 存储 | 1 CU 常驻 730 CU-hours × $0.106 | 换栈代价；见 `database-auth-long-term-comparison.md` |

关键提醒（`[推断]`）：**PITR 没有「1 小时」这一档**——它的 WAL 间隔是 2 分钟，最坏 RPO 2 分钟。所以「1 小时」档要么降级到自建逻辑导出，要么直接付 PITR 的钱拿到分钟级。中间的 1 小时档没有便宜的官方选项。

---

## 7. 明确 unknown 汇总

1. `auth.users` 是否在每日物理备份 / PITR 内——备份页未提。有 clone-project 转移 "Auth user data" 作为正向旁证，但仍需恢复演练核实。
2. `supabase db dump` 的 `-s/--schema auth` 能否绕过 managed-schema 排除；`--data-only` 是否含 `auth` 行数据——CLI 参考页未说明。
3. Supabase 官方无「GitHub Actions 定时备份」文档；`db dump` 需 Docker，在 Vercel Functions 内运行的适配性未验证。
4. PITR 附加费按项目还是按组织计——定价页未明说。
5. Free 项目暂停后恢复窗口：正文 1 年 vs 小标题 90 天，官方页面自相矛盾。
6. Supabase 地区页未说明哪些套餐可选哪些地区。
7. Vercel Pro 函数地区数：limits 表 5 vs changelog 标题 3。
8. 每日备份的具体触发时刻——未公布，故「最坏丢 24 小时」是按一天一次推算，非官方承诺的上界。

---

## 8. 对既有文档的修正建议（仅建议，本文不改其他文件）

- `database-auth-long-term-comparison.md` §2/§4 的「PITR 约 $100/月、需至少 Small compute、替换每日备份」**仍然准确，无需修正**。
- 建议补充：官方明确 RPO = 最坏 2 分钟；14/28 天价格为约 $200 / $400；每日备份**不可下载**、恢复为**整库**且期间项目不可用；Free 层平台**无备份**。
- 建议新增一条代价：`supabase db dump` 默认排除 auth schema（`[文档原文]` "The ignored schemas include auth, storage, and those created by extensions."），因此「不买 PITR 改用自建备份」这条路**不能同时覆盖账号数据**，除非单独处理 auth schema（方法 `[unknown]`）。
- 建议把「保留期 ≠ RPO」升级为可执行表述：Pro 每日备份的 RPO 上界约 24 小时、PITR 的 RPO 官方值为 2 分钟。

## 参考来源（均核验 2026-10-22）

- https://supabase.com/docs/guides/platform/backups
- https://supabase.com/pricing
- https://supabase.com/docs/guides/platform/clone-project
- https://supabase.com/docs/reference/cli/supabase-db-dump
- https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/docs/guides/platform/project-pausing
- https://supabase.com/docs/guides/platform/regions
- https://vercel.com/docs/regions
- https://vercel.com/docs/functions/limitations
- https://vercel.com/docs/functions/configuring-functions/region
- https://vercel.com/docs/cron-jobs/usage-and-pricing
- https://vercel.com/docs/plans/hobby
