# 阶段 0：地区与可达性证据

状态为 Draft，供主会话集中决策。核验日期：2026-10-22。本文只记录证据、条件与事实，不表示阶段 0 已通过，也不替 Luke 选定地区。

## 范围与限制

本文补充四个问题：中国大陆可达性（Vercel 默认域名 / 自有域名 / `*.supabase.co`）、服务端代理能否规避、延迟与函数地区、跨境与 GDPR 合规事实。

地区事实（数据库可选地区、Vercel 默认 `iad1`）已在 `stage-0-data-and-delivery-evidence.md` 第 46-80 行记录，本文只补足该文件未覆盖的可达性与合规面，不重复其地区清单。

本次没有创建云资源、连接数据库、读取凭据、部署、调用 Provider，也没有从中国大陆实测任何域名。所有大陆访问结论要么是官方原文，要么标注 `[线索]` 的社区报告。本文不是法律意见。

## 证据分级

沿用 `stage-0-data-and-delivery-evidence.md` 的五个标签，另加四个来源标签。

| 来源标签 | 含义 |
| --- | --- |
| `[文档原文]` | 官方文档或法规原文，附 URL 与短引。 |
| `[推断]` | 由原文推出的结论，推理过程写在括号内。 |
| `[线索]` | 社区报告或第三方页面，注明来源与日期，未经官方确认。 |
| `[unknown]` | 官方文档未回答，需实测或另行确认。 |

## 问题 1：中国大陆访问可达性

### Vercel 官方说明（存在，且明确）

Vercel 有一篇专门的知识库指南 `Accessing Vercel-hosted sites from mainland China`。核验于 2026-10-22，页面标注 Published 2025-11-03、last updated 2026-09-11。

`[文档原文]` 三条成因，短引：

- 「Vercel has no servers or CDN nodes in mainland China.」（无大陆节点，请求由邻近区域服务）
- 「China's network controls can block or throttle traffic to foreign domains,」明确点名 `*.vercel.app` 子域在可能被阻断或限速之列。
- 「Hosting within China requires an ICP license」并需遵守当地法规；Vercel 不提供境内托管或监管支持。

`[文档原文]` 结论句：「Even with these optimizations, Vercel can't guarantee availability or performance within mainland China.」

`[文档原文]` 对域名的原话：「Custom domains are less likely to be flagged or blocked, though no domain is immune.」同一指南还说明封锁是按域名执行的，会随时间与不同 ISP 变化，可能不另行通知。

`[文档原文]` 关于前置代理：指南明确 Vercel「does not recommend placing a proxy in front」of a deployment，并列出四个选项——自有域名、自托管外部资源（Google Fonts、外部统计脚本）、境外静态镜像、境内部署（需 ICP，最可靠但合规负担最重）。

URL：https://vercel.com/guides/accessing-vercel-hosted-sites-from-mainland-china ，知识库镜像 https://vercel.com/kb/guide/accessing-vercel-hosted-sites-from-mainland-china

### 结论一（Vercel 域名）

- `*.vercel.app` 默认域名在大陆被官方文档点名可能被阻断或限速，且 Vercel 不保证其可用性或性能。`[文档原文]`
- 绑定自有域名后，官方口径是「更不容易被标记或封锁」，但没有域名能免疫；官方仍不保证可用性。`[文档原文]`
- `[推断]` 自有域名不改变「大陆无节点」这一条，因此延迟与跨境链路仍在，改域名只降低被 GFW 针对性处置的概率。
- `[线索]` 社区一致把 `*.vercel.app` 描述为 DNS 污染导致的解析失败或长时间转圈。来源：Vercel 社区帖 `China project access, network access failed`（community.vercel.com/t/china-project-access-network-access-failed/10968，2025-05-19 与 2025-05-22 两帖，无 Vercel 员工回复），用户描述「stuck in the loading page」「must use VPN」；GitHub Issue whisper-xiang/daily-notes#43（2025-03-28）称大部分情况下大陆访问不稳定或无法访问。均为 `[线索]`，与官方文档方向一致但细节未经官方确认。

### Supabase 官方说明

`[文档原文]` Supabase 官方博客《Navigating Regional Network Blocks》记录了真实封锁事件，并给出共性结论：「In each case, local ISPs or government authorities had blocked access to `supabase.co` domains.」

该文列出三起：UAE（2025-09-02 起约 18 天，Etisalat 与 Du 网络无法访问项目）；Yemen（2026-02-02 至 02-10，传输层 TCP 连接被重置）；India（2026-02-24 至 03-03，MeitY 依 Section 69A 对 `supabase.co` 的临时限制）。

URL：https://supabase.com/blog/navigating-regional-network-blocks

`[文档原文]` 官方排查文档《NXDOMAIN error when connecting to a Supabase project》指出：若 `supabase.co` 与若干无关的 `*.supabase.co` 主机名在某网络上无法解析但 VPN 下正常，「the problem could be with that network's DNS resolver rather than with Supabase」，并称这常见于「restrictive mobile carrier, office, or ISP networks」。

URL：https://supabase.com/docs/guides/troubleshooting/nxdomain-error-connecting-to-a-supabase-project

`[文档原文]` 地区文档本身不提及中国大陆，可选地区中无大陆节点，最近的是东京、首尔、新加坡、孟买、悉尼。URL：https://supabase.com/docs/guides/platform/regions

### 结论二（supabase.co）

- `supabase.co` 在 UAE、Yemen、India 发生过 ISP 或政府层面的域名级封锁，是官方确认的事实；这三地都不是中国大陆，但证明 `supabase.co` 域名可被区域网络整体处置。`[文档原文]`
- `[unknown]` Supabase 官方没有针对中国大陆的专门说明，也没有官方页面确认 `*.supabase.co` 在大陆是否被封锁或不稳定。官方排查文档只描述「限制性网络上的 DNS 解析失败」这一症状模式，未指明具体国家。
- `[线索]` 21YunBox 页面称 2026-08-27 从阿里云 cn-zhangjiakou 探测 supabase.com 三次均完成加载，中位 TTFB 约 393ms，结论是「未被完全封锁但慢」。该站点是商业服务方，有加速业务立场，仅作 `[线索]`。URL：https://launch-in-china.21cloudbox.com/support/supabase-china.html
- `[线索]` 中文社区（CSDN ask.csdn.net/questions/8598092）报告国内 DNS 解析慢或被劫持。同为 `[线索]`。

## 问题 2：服务端代理能否规避 supabase.co 可达性

### 架构层面：可以，但需要 Auth 也走服务端

`[文档原文]` Supabase SSR 文档把客户端明确二分：「Use the browser client in code that runs on the browser, and the server client in code that runs on the server.」Server Component client 的说明是「To access Supabase from Server Components, Server Actions, and Route Handlers, which run only on the server.」Session 存在 cookie 中：「The cookies object lets the Supabase client know how to access the cookies, so it can read and write the user session data.」

`[推断]` 因此浏览器侧只持有自己的 cookie，不发请求到 `*.supabase.co`；所有 Auth 校验（middleware / proxy 刷新 token）与数据读写都由 Vercel 函数以 `createServerClient` 完成。架构上可以让浏览器全程只访问 Vercel 自有域名。

`[文档原文]` 前提是密钥边界：publishable（anon）key 可进浏览器，`service_role` key 不可暴露给客户端（服务端专用）。这与阶段 0 已定的「访问控制先放应用层」一致。

`[unknown]` Supabase 官方文档没有一句话直接断言「Auth 可以全部经由服务端、浏览器零直连」。上述结论是从 SSR 客户端二分与 cookie 会话模型推出的。若产品未来要 client-side OAuth 跳转、Realtime 订阅或 Storage 直传，浏览器就会重新直连 `supabase.co`，届时规避失效。

### Supabase custom domain：价格与套餐

`[文档原文]` 官方 custom domains 文档：「These are available as a paid add-on for projects on a paid plan.」vanity subdomain 同样要求组织在付费套餐（Pro/Team/Enterprise）。

限制原文：

- 「You can only attach a single custom domain to any given Supabase project.」且「It is not possible to break out your project's resources into multiple custom domains.」
- 「Custom domains can only be powered by CNAME records.」且「Currently, only subdomains are supported.」
- 「Custom domains are not intended to enable hosting of frontend applications through Edge Functions.」
- 一个项目只能二选一：「You can choose either a custom domain or vanity subdomain for each project.」
- 激活后 Auth 立即切换到新域名：「Supabase Auth will use the custom domain immediately once activated.」OAuth「will advertise the custom domain as a callback URL.」SAML 同理。
- 旧域名不会失效：原文说它「continues to work and serve requests」。移除自定义域名「may cause some issues when using Supabase Auth with OAuth or SAML」。

覆盖范围：API（`createClient('https://api.example.com', ...)`）、Edge Functions、Storage、Auth、SAML。文档未提及 Realtime。

URL：https://supabase.com/docs/guides/platform/custom-domains

`[文档原文]` 价格见 usage 文档：「$0.0137 per hour ($10 per month).」「You are charged for all custom domains configured across your projects.」且「Custom Domains are not covered by the Spend Cap.」官方示例给出一条 Pro $25 + Micro 计算 $10 + Custom Domain $10、减去 $10 计算额度后合计 $35/月 的账单。

URL：https://supabase.com/docs/guides/platform/manage-your-usage/custom-domains

### 结论三（规避）

- `[推断]` 若浏览器只访问 Vercel 自有域名、服务端连 Supabase 与 LLM，则浏览器侧不再受 `supabase.co` 可达性影响。Supabase 的封锁事件（UAE、Yemen、India）都发生在浏览器或客户端能直连该域名的场景；服务端在 Vercel 函数内出网是否会被同一机制处置，`[unknown]`，但 Vercel 函数位于美国/新加坡/日本等地，与大陆用户网络路径不同。
- `[unknown]` 服务端（Vercel 函数）访问 `*.supabase.co` 是否可能被区域性封锁波及，官方无说明。三起已知事件的受害者都是终端用户网络，不是服务端。
- 若坚持 Free 层：Free 项目不能开 custom domain（`[文档原文]` 需付费套餐），因此无法用自有域名替代 `*.supabase.co`。此时「服务端代理」不是可选优化，而是唯一让浏览器不碰 `supabase.co` 的办法。
- 若上 Pro：custom domain $10/月可把 Auth 与 API 都放到自有域名下，进一步降低对 `supabase.co` 的依赖；但它仍只覆盖一个域名、仅 CNAME、且不覆盖 Realtime。

## 问题 3：延迟与函数地区

### Vercel 函数地区事实

`[文档原文]` 「By default, Vercel Functions execute in *Washington, D.C., USA* (`iad1`) **for all new projects**」，理由是该地靠近多数托管在美国东海岸的外部数据源。

URL：https://vercel.com/docs/functions/configuring-functions/region （last updated 2026-08-11）

`[文档原文]` 套餐地区上限：

| Plan | Function regions |
| --- | --- |
| Hobby | Single region |
| Pro | 5 regions |
| Enterprise | All regions |

原文并说明「Deploying to more regions than your plan allows causes the deployment to fail before the build step.」

`[文档原文]` 19 个可计算地区代码：`arn1` Stockholm、`bom1` Mumbai、`cdg1` Paris、`cle1` Cleveland、`cpt1` Cape Town、`dub1` Dublin、`fra1` Frankfurt、`gru1` São Paulo、`hkg1` Hong Kong、`hnd1` Tokyo、`iad1` Washington D.C.、`icn1` Seoul、`kix1` Osaka、`lhr1` London、`pdx1` Portland、`sfo1` San Francisco、`sin1` Singapore、`syd1` Sydney、`yul1` Montréal。

URL：https://vercel.com/docs/regions

`[文档原文]` 官方建议：「Functions should be executed in the same region as your database, or as close to it as possible, for the lowest latency.」

`[文档原文]` 静态内容由 CDN 就近服务：「your users will always get static files like HTML, CSS, and JavaScript served from the region that is closest to them」，PoP 到地区为「single-digit millisecond latency」。Vercel CDN 有 126 个 PoP / 19 个可计算地区。

### 延迟折中的事实与推断

对「大陆 + 欧美」双群体用户，Vercel Hobby 只能选单一函数地区（`[文档原文]`），因此不存在「同时贴近两边」的函数部署。可选事实组合：

| 组合 | 函数地区 | Supabase 具体地区 | 事实基础 |
| --- | --- | --- | --- |
| 亚太折中 | `hnd1` Tokyo 或 `sin1` Singapore | `ap-northeast-1` Tokyo 或 `ap-southeast-1` Singapore | 同为最近亚太选项，函数与库同区延迟最低 |
| 美国折中 | `iad1` Washington D.C.（默认） | `us-east-1` North Virginia | 官方默认，贴近多数外部数据源 |

`[推断]` 三点的推理，均需 Luke 确认，不构成建议：

- LLM Provider 调用不构成地区约束。OpenCode Go 与 DeepSeek 官方 API 都是公网 HTTPS 端点，函数在哪个地区都可达；选地区主要取决于库的位置，不是 Provider。
- 大陆用户的瓶颈大概率不在函数与库之间（同区可达个位数到数十毫秒），而在大陆到境外 PoP 的跨境链路。Vercel 官方指南已说明大陆无节点且不保证可用性，`[推断]` 这意味着任何非 ICP 方案的大陆侧延迟都由跨境链路主导，换 `sin1`/`hnd1` 只能改善其中一段。
- 欧美用户的体验则随函数远离 `iad1` 而变差。Hobby 单地区下，这是同一个变量的两端，不是两个可分别优化的项。
- `[unknown]` 官方未给出任何地区到大陆或到欧美的实测延迟数字。本文不给毫秒数。
- `[unknown]` Vercel 是否有大陆就近 PoP（如香港 `hkg1` 是计算地区而非 PoP 归属地）未在文档中说明，`hkg1` 在 Functions 可选列表内。

## 问题 4：合规风险提示

只列官方/权威来源，不构成法律意见。SayHear 是私人日记式聊天 Agent，日记正文属于个人信息，且可能触及敏感事项。

### 中国：向境外提供个人信息

`[文档原文]` 《中华人民共和国个人信息保护法》第三十八条：因业务需要确需向境外提供个人信息的，应具备下列条件之一——安全评估（依第四十条）、个人信息保护认证、按网信部门制定的标准合同与境外接收方订立合同、或其他法定条件；并「应当采取必要措施，保障境外接收方处理个人信息的活动达到本法规定的个人信息保护标准」。

`[文档原文]` 第三十九条：应向个人告知境外接收方名称、联系方式、处理目的与方式、个人信息种类、行使权利的方式程序，并取得个人的**单独同意**。

`[文档原文]` 第四十条：关键信息基础设施运营者（CIIO）和处理个人信息达到国家网信部门规定数量的处理者，应境内存储；确需出境的应通过安全评估。

`[文档原文]` 第五十五条：向境外提供前应进行个人信息保护影响评估并留存报告至少三年。

来源（人民网转载全文）：https://cpc.people.com.cn/n1/2021/0823/c64387-32203184.html

### 2024 年《促进和规范数据跨境流动规定》的数量门槛

`[文档原文]` 国家互联网信息办公室 2024-03-22 公布施行，全文见 https://www.gov.cn/zhengce/202501/content_6997438.htm 。门槛按「自当年 1 月 1 日起累计」计算：

| 当年累计向境外提供 | 要求 | 条文 |
| --- | --- | --- |
| 不满 10 万人（不含敏感个人信息） | 免予申报安全评估、免订标准合同、免认证 | 第五条第四项 |
| 10 万人以上不满 100 万人，或不满 1 万人敏感个人信息 | 订立标准合同或通过个人信息保护认证 | 第八条 |
| 100 万人以上，或 1 万人以上敏感个人信息，或重要数据 | 申报数据出境安全评估 | 第七条第二项 |

`[文档原文]` 原文短引：非 CIIO 且「自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息）的」适用豁免；第七条第二项对应「100万人以上个人信息（不含敏感个人信息）或者1万人以上敏感个人信息」。

`[推断]` 三条与 SayHear 相关的读法，均非法律意见：

- 小规模内测（用户数远小于 10 万）落在第五条第四项的完全豁免内，不需要安全评估、标准合同或认证。这是数量门槛带来的实际豁免，不是「个人开发者身份」豁免——门槛按人数量，不按主体身份。
- 豁免只覆盖上述三个机制。第三十九条的告知与单独同意、第五十五条的影响评估与三年留存，条文不在豁免清单内，`[推断]` 仍然适用。
- 若日记内容被认定为敏感个人信息，1 万人的敏感门槛比 10 万人的一般门槛低一个量级。私人日记是否构成 PIPL 意义上的敏感个人信息，`[unknown]`，需 Luke 判断，本文不下结论。
- CIIO 与重要数据的判定不在 SayHear 情形内，第二条并明确未被相关部门告知或公布为重要数据的不按重要数据申报。`[文档原文]`

### 欧盟：GDPR 与 Supabase DPA

`[文档原文]` Supabase GDPR 文档：「If you need a formal data processing contract under GDPR, Supabase provides a Data Processing Agreement (DPA).」

同一文档的地区提示：「Choosing a specific region within the EU pins these services to that exact AWS region.」并警告通用 Europe 分组包含 London 与 Zurich（非欧盟成员国），需要 EU-only 存储时应「choose a specific EU region rather than the general Europe grouping」。这与阶段 0 已记录的地区事实一致（通用地区实际落点可能超出名称范围）。

同页并指出「sub-processors can affect your data residency and international transfer analysis」，以及地区选择「is a data-location control, not proof of regulatory compliance」。

URL：https://supabase.com/docs/guides/security/gdpr-compliance

`[文档原文]` DPA 正文（Version 1 — August 1, 2026）以 SCC 为转移机制，第十二条及 Schedule 2 约定「The Parties agree that acceptance of the Agreement shall have the same effect as signing the SCCs.」Schedule 2 含 UK Addendum 与 Swiss Addendum，并有「Transfers of personal data from Other Jurisdictions」一节。URL：https://www.supabase.com/legal/dpa

`[文档原文]` 该页另说明：DPA 有静态 PDF 可供审阅，但「To make the DPA legally binding, you need to sign and complete the details through a PandaDoc document that we prepare.」，并指向 Supabase dashboard 的 legal documents 页面获取。

`[unknown]` Free 层能否签 DPA：Supabase GDPR 文档与 DPA 正文均未按套餐区分签署资格，DPA 自述「effective as of the Effective Date of the Agreement」适用于协议下的所有客户。社区成员在 Supabase 社区页面称 free 与 paid 客户都可在 dashboard 签署，但这是社区内容而非官方原文，仅作 `[线索]`。`[unknown]` 需在 dashboard 的 legal documents 页实际确认。

`[推断]` GDPR 侧与地区选择的联动：Supabase 通用 Europe 地区可能落在 London 或 Zurich（均为欧盟充分性认定覆盖范围，但非欧盟成员国）。若要求数据只在欧盟成员国境内，应选具体 EU 地区而非通用 Europe。这一点阶段 0 已记，此处补上 GDPR 文档的原文依据。

`[unknown]` 欧盟用户数据存到亚洲（新加坡/东京）时的 GDPR 转移要求：Supabase 文档未给出亚洲地区的转移机制说明，DPA 的 SCC 与 UK/Swiss Addendum 未覆盖亚洲充分性认定。本文不展开。

## 对地区决策的影响

本文不选地区，只列约束：

- 大陆可达性的主要杠杆在域名与是否走 ICP，不在函数地区。`[推断]` 官方指南把自有域名列为第一项建议，并把境内部署列为唯一「最可靠」但需 ICP 的选项。
- 若大陆用户在内测范围内且可接受「多数时候可用、偶发不可用」，自有域名 + 服务端代理是文档支持度最高的路径，无需 ICP。`[推断]`
- 若要求大陆稳定可用，官方口径只剩境内部署（需 ICP）一条，且 Vercel 明确不建议在其部署前置代理。
- 服务端代理（浏览器不直连 `supabase.co`）在 Free 层是唯一选择，因为 Free 项目无法开 custom domain。`[文档原文]`
- Hobby 单函数地区意味着「大陆 + 欧美」必须在同一个地区上折中；Pro 可到 5 个地区，但仍不能覆盖大陆（大陆无可计算地区）。`[文档原文]`
- 合规侧，小规模内测落在 2024 年规定的完全豁免区间，但第三十九条的单独同意与第五十五条的影响评估不因该豁免而消失。`[推断]`

## 未决问题与缺口

- `[unknown]` `*.supabase.co` 在大陆的官方可达性说明不存在，需要实测或另找权威来源。
- `[unknown]` 服务端（Vercel 函数）访问 `*.supabase.co` 是否可能被区域封锁波及。
- `[unknown]` 私人日记内容是否构成 PIPL 敏感个人信息。
- `[unknown]` Free 层能否签 Supabase DPA，需在 dashboard 确认。
- `[unknown]` 官方未给出任何地区到大陆/欧美的实测延迟。
- `[unknown]` Supabase Auth 是否可以完全不经浏览器（官方文档无一句直接断言，现有结论是从 SSR 客户端二分推出）。
- `[unknown]` 大陆侧实测：需要阶段 1 用真实网络验证自有域名与 `*.vercel.app` 在大陆的实际表现。

## 来源

核验于 2026-10-22。

- Vercel 大陆访问指南：https://vercel.com/guides/accessing-vercel-hosted-sites-from-mainland-china
- Vercel 大陆访问知识库镜像：https://vercel.com/kb/guide/accessing-vercel-hosted-sites-from-mainland-china
- Vercel 函数地区配置：https://vercel.com/docs/functions/configuring-functions/region
- Vercel 全球网络与地区列表：https://vercel.com/docs/regions
- Vercel 函数限制：https://vercel.com/docs/functions/limitations
- Vercel Hobby 套餐：https://vercel.com/docs/plans/hobby
- Vercel 社区帖 China project access：https://community.vercel.com/t/china-project-access-network-access-failed/10968
- Supabase 区域网络封锁博客：https://supabase.com/blog/navigating-regional-network-blocks
- Supabase NXDOMAIN 排查：https://supabase.com/docs/guides/troubleshooting/nxdomain-error-connecting-to-a-supabase-project
- Supabase 地区：https://supabase.com/docs/guides/platform/regions
- Supabase 自定义域名：https://supabase.com/docs/guides/platform/custom-domains
- Supabase 自定义域名计费：https://supabase.com/docs/guides/platform/manage-your-usage/custom-domains
- Supabase SSR 客户端：https://supabase.com/docs/guides/auth/server-side/nextjs
- Supabase GDPR：https://supabase.com/docs/guides/security/gdpr-compliance
- Supabase DPA：https://www.supabase.com/legal/dpa
- 个人信息保护法（人民网转载）：https://cpc.people.com.cn/n1/2021/0823/c64387-32203184.html
- 促进和规范数据跨境流动规定（中国政府网）：https://www.gov.cn/zhengce/202501/content_6997438.htm
- `[线索]` GitHub Issue：https://github.com/whisper-xiang/daily-notes/issues/43
- `[线索]` 21YunBox Supabase in China：https://launch-in-china.21cloudbox.com/support/supabase-china.html
- `[线索]` CSDN 国内访问延迟：https://ask.csdn.net/questions/8598092
- 既有地区事实：`stage-0-data-and-delivery-evidence.md` 第 46-80 行
