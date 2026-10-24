# 流式回复的令牌有效期与登出边界

日期：2026-10-23。来源：本次定点调研 agent 报告及主会话核对。未连接数据库、安装依赖或运行探针。不能将源码调查记为运行通过。

## 主会话已独立核对的官方约束

- [Next.js cookies](https://nextjs.org/docs/app/api-reference/functions/cookies)：HTTP 不允许在 streaming 开始后设置 cookie。因此续期及 cookie 回写必须在流式响应开始前准备完毕，不能把 cookies().set 未报错当作浏览器已收到。
- [Supabase sessions](https://supabase.com/docs/guides/auth/sessions)：默认 access token 有效期 1 小时；建议覆盖应用最长请求。refresh token 复用默认宽限 10 秒，另有 active token 的 parent 例外，不能简化成“重复刷新必然撤销”。
- ADR 0006 已将单次运行总预算限制为低于 300 秒。这与默认 1 小时 JWT 寿命兼容，但须核实部署配置与 SDK 临期刷新窗口。

## Agent 源码调查（未由主会话逐行复核，实施前重核锁定版本）

- [SSR 固定提交](https://github.com/supabase/ssr/blob/9b28f495a358393046851b926551b706d7e4d267/src/createServerClient.ts)：报告称 @supabase/ssr 0.12.7 禁用后台 autoRefreshToken，TOKEN_REFRESHED 事件将缓存中的新会话写入 setAll。
- [supabase-js/auth-js 固定提交](https://github.com/supabase/supabase-js/blob/6ede0cbfc8801bee14f61043578d2f3acf7fa831/packages/core/auth-js/src/GoTrueClient.ts)：报告称 2.118.0 的 Data API fetch 会取当前 session，临期 90 秒内触发按需刷新；同请求内存里的 session 可更新，而浏览器可能未拿到新 cookie。故预算还要避开 SDK 临期刷新窗口，不能只比较 exp 与流时长。
- [Auth 服务固定提交](https://github.com/supabase/auth/blob/4eee58f296d9698a1c2c0ae14d7a0b379c7622d3/internal/api/auth.go)：报告称 v2.197.0 的 /user 路径加载 session，缺失时拒绝；支持 getUser 发现已删除会话。实际托管版本与登出重放行为仍需验收。
- [PostgREST 固定文档](https://github.com/PostgREST/postgrest/blob/798523c910c09dc56d92ba2c42bcb78e5f59ecb3/docs/references/auth.rst)：报告指出 JWT 校验无状态，默认不额外查询会话撤销；不可将 Auth 端点的行为推广到 Data API。

Agent 关于多次 refresh rotation 必定导致撤销的推断涉及并发和 active parent 状态，未采为普遍保证；方案不依赖这些例外实现正确性。Next.js 特定版本中晚设置 cookie 是否静默丢弃也留作探针，不作为通用 API 承诺。

## 已接受的决定与验证

Luke 接受：登出后新请求立即拒绝，已开始的回复允许在原预算内完成并保存。ADR 0009/0011/0013 已同步；不因 agent 建议自行扩大或缩小撤销语义。

实施验证：入口续期前后及运行预算关系；响应携带新 cookie；跨原到期点保存成功；浏览器下一次请求正常；续期失败不启动生成；登出后新请求拒绝且已有流可完成。使用隔离合成环境。锁定 SDK 的临期刷新阈值与自定义授权头行为须核实，日志不得记录令牌。
