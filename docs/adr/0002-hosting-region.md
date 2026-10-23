---
status: accepted
---

# 函数与数据库同置美国东部：Vercel `iad1` 与 Supabase `us-east-1`

SayHear 的主要目标用户在美国，不在欧盟上线，中国大陆仅 Luke 本人使用并自行解决境外访问。函数与数据库应放在同一地区，以减少每次请求在两者之间的往返。推荐 Vercel Functions 使用默认地区 `iad1`（华盛顿特区），Supabase 项目使用具体地区 `us-east-1`（北弗吉尼亚）。数据库地区在项目创建后不可修改，迁移需新建项目。

证据见[地区与可达性证据](../plans/stages/stage-0/evidence/stage-0-region-and-reachability-evidence.md)与[恢复与地区证据](../plans/stages/stage-0/evidence/database-recovery-and-region-evidence.md)。

## 取舍与边界

`iad1` 是 Vercel 默认地区，Hobby 无需额外配置；Vercel 官方建议函数与数据库同区。美国西部（`pdx1` 与 `us-west-2`）对西海岸用户更近，但目标用户分布尚无数据，东部作为默认起点。中国大陆访问稳定性不作为产品要求；部署仍使用自有域名，不依赖 `*.vercel.app`。

## 重评条件

美国用户分布明显偏西海岸、实测延迟不可接受，或主 Provider 托管地区使函数到 Provider 的往返成为瓶颈时重评。Luke 于 2026-10-22 确认。本记录未创建任何资源。
