---
status: accepted
---

# 采用 Supabase Postgres 与 Supabase Auth，初期两库均用 Free 层并自建每日备份

SayHear 面向真实用户的长期产品需要托管的完整账号生命周期、明确的数据归属与可恢复性。采用 Supabase Postgres 与 Supabase Auth，主要依据为改邮箱、删除用户、找回密码与 MFA 均有官方支持，集成边界相对明确。Neon Postgres 与 Managed Better Auth 在按量计算和时间点恢复成本上有优势，Free 层自带 6 小时恢复窗口，但当前 Auth SDK 为 beta，改邮箱有文档冲突，删除用户为 unknown，增加长期账号维护的不确定性。

Luke 于 2026-10-22 确认：业务恢复目标为最多丢失约 1 天数据；测试库与用户库都用 Free 层，接受闲置一周暂停并手动恢复；备份加密后存放于对象存储（如 Cloudflare R2），不依赖开发电脑。依据见[长期比较](../plans/stages/stage-0/evidence/database-auth-long-term-comparison.md)、[恢复与地区证据](../plans/stages/stage-0/evidence/database-recovery-and-region-evidence.md)、[Supabase 证据](../plans/stages/stage-0/evidence/supabase-platform-research.md)、[Neon 证据](../plans/stages/stage-0/evidence/neon-platform-research.md)和[关键事实复核](../plans/stages/stage-0/evidence/database-auth-critical-check.md)。

## 取舍与边界

Free 层没有平台备份，恢复能力完全落在自建备份上。用户库每日执行一次 dump，加密后上传对象存储。Supabase CLI 的 `db dump` 默认排除 `auth`、`storage` 与扩展 schema，因此备份必须显式包含 `auth` schema；能否用该方式完整恢复账号并继续登录属于推断，首个非 Luke 用户前须在测试库完成恢复演练。每日一次的调度没有余量，失败需能被发现。

Free 层同时只能有 2 个 active 项目，闲置 7 天暂停；暂停后的可恢复期限文档不一致，记为 unknown。浏览器不直连 `supabase.co`，数据库与 Auth 请求经应用服务端，Free 层无法使用自定义域名。主 JS SDK 为稳定版，`@supabase/ssr` 官方仍标 beta。Storage、Realtime、phone MFA 与 RLS 的采用按需求另定。

两库均需由 SayHear 实现业务数据访问隔离、清理传播及恢复后的账号一致性验证。备份保留期不等于 RPO。

## 重评条件

邀请 Luke 以外的内测用户前，用户库升级 Pro（约 25 美元/月），获得平台每日备份且不再因闲置暂停，并重新确认恢复目标。恢复演练失败、`auth` schema 无法可靠导出恢复、Free 规则变化，或 Neon 补齐账号生命周期能力与 SDK 稳定性时，重新比较。本记录未创建云资源、连接数据库或执行恢复演练。
