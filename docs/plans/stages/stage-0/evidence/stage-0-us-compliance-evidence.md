# 阶段 0 美国市场合规证据：SayHear 作为 AI 陪伴日记应用可能触发的义务

核验日期：2026-10-22。只读调研。未读取任何凭据，未调用任何 API，未提交 git，未修改其他文件。
本文件不构成法律意见，只整理权威原文与推断，供决策使用。

## 主会话复核说明（2026-10-22）

下文是研究材料，不是已确定的适用性结论。以下限定优先于正文与三阶段表中较强的表述：

- 邀请制内测不会自动触发所有州法。须逐项满足用户地域、经营关联、产品行为及法定定义。纽约 §1700 的三项行为由 `and` 连接，主会话已直接核实；不能仅凭其中两项认定适用。
- 年龄声明不是 COPPA 豁免。主会话已核实 FTC FAQ：面向儿童的服务或实际知道正在收集 13 岁以下儿童信息的通用服务，不能靠条款中的年龄限制免除义务。https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions
- DOJ Part 202 不能按“美国注册用户超过 10,000”单独判断。必须核对受规制主体、交易类型、实际数据类别、过去 12 个月聚合量与例外；政府相关数据另有不依赖 bulk 数量的规则。不能把内测人数少概括为全面不适用，也不能把更换 Provider 概括为自动合规。
- 不宣称治疗不等于一定落入 NV / IL 例外，实际功能与行为仍需核对。HBNR 适用性亦未确定。
- 本轮不需要询问 Luke 国籍等个人身份信息；涉及真实美国用户前，再按实际运营主体和数据流定点核查。
- 原文中罚款、豁免与报告日期均仅作核验线索；上线前需按届时有效官方法条复核。第三方托管的法条 PDF 不能标作官方托管来源。

## 证据等级

| 标记 | 含义 |
| --- | --- |
| `[文档]` | 官方或一手来源在核验当日写明的原文，附链接 |
| `[推断]` | 从 `[文档]` 推出的判断，可被反驳 |
| `[unknown]` | 一手资料未给出答案，或页面不可访问 |

官方页面是滚动文档，接入前应重新核对。

## 产品事实与适用性前提

- 私人日记式 AI 陪伴聊天 Web 应用：有稳定人格、共情、记住用户经历与情绪；非人类 AI；不经营浪漫关系。
- 部署 Vercel 美国东部，数据在 Supabase 美国；LLM 主路径 OpenCode Go，fallback 为 DeepSeek 官方 API（数据存中国境内，可更换）。
- 用户会输入情绪、心理状态等内容。
- 阶段：A 仅开发者本人（中国大陆使用）→ B 邀请制内测（几十人以内，免费，美国用户，不上架商店）→ C 公开上线（美国用户）。不在欧盟上线。
- `[unknown]` 开发者本人的国籍 / 居住地 / 是否美国税务或移民意义上的 U.S. person。这一项直接决定阶段 A 下 DOJ Part 202 与各州法的适用性，需 Luke 确认后才能闭环。

---

## 1. AI companion chatbot 州法

### 1.1 加州 SB 243（Bus. & Prof. Code 第 22.6 章，§§22601–22606）

签署 2025-10-13（Ch. 677, Stats. 2025），**生效 2026-01-01**，即今天已生效。`[文档]`

来源：[SB 243 定稿文本 PDF（加州立法局）](https://www.biodiritto.org/ocmultibinary/download/5055/58733/1/659e3f370272cb0d35bd4e2f5a1ad799/file/20250SB243_92.pdf)（核验 2026-10-22，PDF 正文已逐字比对）；[leginfo 第 22.6 章目录](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?article=&chapter=22.6.&division=8.&lawCode=BPC)（核验 2026-10-22，leginfo 对自动化访问返回 403，仅能确认章节编号范围，正文以定稿 PDF 为准）。

定义（§22601）：

> "Companion chatbot" means an artificial intelligence system with a natural language interface that provides adaptive, human-like responses to user inputs and is capable of meeting a user's social needs, including by exhibiting anthropomorphic features and being able to sustain a relationship across multiple interactions.
> "Operator" means a person who makes a companion chatbot platform available to a user in the state.

排除项（§22601(b)(2)）只覆盖：仅用于客服 / 业务运营 / 内部研究的 bot、电子游戏中受限话题的 bot、不维持跨次关系的智能音箱类设备。SayHear 不在任何一项排除内。`[推断]`

义务：

| 条款 | 内容 | 原文 |
| --- | --- | --- |
| §22602(a) | AI 身份披露 | "If a reasonable person interacting with a companion chatbot would be misled to believe that the person is interacting with a human, an operator shall issue a clear and conspicuous notification indicating that the companion chatbot is artificially generated and not human." |
| §22602(b)(1) | 自杀 / 自伤规程 | "An operator shall prevent a companion chatbot on its companion chatbot platform from engaging with users unless the operator maintains a protocol for preventing the production of suicidal ideation, suicide, or self-harm content to the user, including ... providing a notification to the user that refers the user to crisis service providers, including a suicide hotline or crisis text line, if the user expresses suicidal ideation, suicide, or self-harm." |
| §22602(b)(2) | 规程须公开 | "The operator shall publish details on the protocol required by this subdivision on the operator's internet website." |
| §22603(d) | 检测方法 | "An operator shall use evidence-based methods for measuring suicidal ideation." |
| §22604 | 未成年人警示 | "An operator shall disclose to a user of its companion chatbot platform, on the application, the browser, or any other format that a user can use to access the companion chatbot platform, that companion chatbots may not be suitable for some minors." |
| §22602(c) | 已知未成年用户 | 三项：披露 AI 身份；"at least every three hours" 的休息提醒；"Institute reasonable measures to prevent its companion chatbot from producing visual material of sexually explicit conduct or directly stating that the minor should engage in sexually explicit conduct." |
| §22603(a) | 年度报告 | "Beginning July 1, 2027, an operator shall annually report to the office" 三类信息：危机转介次数、检测 / 移除 / 响应规程、禁止回应自杀内容的规程；"(b) ... shall not include any identifiers or personal information about users." |
| §22605 | **私人诉权** | "A person who suffers injury in fact as a result of a violation of this chapter may bring a civil action to recover ... Injunctive relief. Damages in an amount equal to the greater of actual damages or one thousand dollars ($1,000) per violation. Reasonable attorney's fees and costs." |

规模与收费门槛：**法条正文没有任何收入、用户量或收费门槛**。唯一的地域连接点是 operator "makes a companion chatbot platform available to a user in the state"。`[文档]`

### 1.2 纽约 General Business Law 第 47 条（§§1700–1704）

**生效 2025-11-05**（州长 Hochul 当日致函"All Companies Operating AI Companions in New York"宣布"New York's new AI Companion law is now in effect"）。`[文档]`

来源：[Hochul 州长函 PDF](https://www.governor.ny.gov/sites/default/files/2025-11/Companion_AI_Letter.pdf)（核验 2026-10-22，已从 PDF 内抽取正文）；[GBL §1700](https://www.nysenate.gov/legislation/laws/GBS/1700)、[§1701](https://www.nysenate.gov/legislation/laws/GBS/1701)、[§1702](https://www.nysenate.gov/legislation/laws/GBS/1702)、[§1703](https://www.nysenate.gov/legislation/laws/GBS/1703)（页面标注 "Viewing most recent revision (from 2025-11-07)"，核验 2026-10-22）。

定义（§1700）："AI companion" 须同时满足三项：(i) "retaining information on prior interactions or user sessions and user preferences to personalize the interaction"；(ii) "asking unprompted or unsolicited emotion-based questions that go beyond a direct response to a user prompt"；(iii) "sustaining an ongoing dialogue concerning matters personal to the user." 关系可以是 "intimate, romantic or platonic interactions or companionship"。排除：仅客服、主要为效率 / 研究 / 技术协助、仅内部或员工生产力用途的系统。`[文档]`

SayHear 逐项比对：(i) 记住用户经历与情绪 → 命中；(iii) 持续讨论个人事务（日记）→ 命中；(ii) 是否会主动提出情绪相关问题取决于产品设计。`[推断]` 满足 (i)+(iii) 已足以构成"拟人持续关系"，但严格按文本三项是并列的，这一点建议在产品设计上确认（见 unknown）。

"User" = "any person who uses an AI companion for personal use within the state"，"Operator" = "any person, partnership, association, firm, or business entity ... that operates or supplies an AI companion to a user"。同样**无规模或收费门槛**。`[文档]`

义务：

| 条款 | 内容 | 原文 |
| --- | --- | --- |
| §1701 | 自杀 / 自伤规程 | unlawful unless the companion "contains a protocol to take reasonable efforts for detecting and addressing suicidal ideation or expressions of self-harm"，含 "detection of user expressions" 与 "a notification to the user that refers them to crisis service providers"（点名 9-8-8 热线、crisis text line） |
| §1702 | AI 身份披露 | "a clear and conspicuous notification ... at the beginning of any AI companion interaction"，且 "need not exceed once per day and at least every three hours for continuing AI companion interactions"，内容须 "state[] either verbally or in writing that the user is not communicating with a human" |
| §1703 | 执法 | 仅 AG；"civil penalties of up to fifteen thousand dollars per day"；罚款入自杀防治基金。**无私人诉权**。`[文档]` |

### 1.3 其他已生效州法（AI + 心理健康方向）

**内华达 NRS 433.567**（AB 406，2025 Nev. Stat. ch. 283；加入 NRS 标注 "Added to NRS by 2025, 1894"，生效 2025-07-01）。`[文档]`

来源：[NRS 第 433 章正文](https://www.leg.state.nv.us/NRS/NRS-433.html)（核验 2026-10-22，正文已逐字抽取）。

> "An artificial intelligence provider shall not make any representation or statement or knowingly cause or program an artificial intelligence system made available for use by a person in this State to make any representation or statement that explicitly or implicitly indicates that: (a) The artificial intelligence system is capable of providing professional mental or behavioral health care; (b) A user ... may interact with any feature ... which simulates human conversation in order to obtain professional mental or behavioral health care; or (c) The artificial intelligence system ... is a provider of mental or behavioral health care, a therapist, a clinical therapist, a counselor, a psychiatrist, a doctor ..."
> "An artificial intelligence provider shall not make available for use by a person in this State an artificial intelligence system that is specifically programmed to provide a service or experience to a user that would constitute the practice of professional mental or behavioral health care if provided by a natural person."
> "A person who violates any provision of subsection 1, 2 or 3 is subject to a civil penalty not to exceed $15,000 per violation."
> 例外："self-help relating to mental or behavioral health, if the material, literature or product does not purport to offer or provide professional mental or behavioral health care."

**伊利诺伊 WOPR Act（Public Act 104-0054，HB1806）**，签署 2025-08-01，"This Act takes effect upon becoming law"。`[文档]`

来源：[PA 104-0054 全文](https://witnessslips.ilga.gov/ftp/Public%20Acts/104/104-0054.htm)（核验 2026-10-22，正文已逐字抽取）。

> "An individual, corporation, or entity may not provide, advertise, or otherwise offer therapy or psychotherapy services, including through the use of Internet-based artificial intelligence, to the public in this State unless the therapy or psychotherapy services are conducted by an individual who is a licensed professional."
> "Therapy or psychotherapy services" means services provided to diagnose, treat, or improve an individual's mental health or behavioral health. ... does not include religious counseling or peer support.
> 例外（§35）："self-help materials and educational resources that are available to the public and do not purport to offer therapy or psychotherapy services."
> 罚则："a civil penalty to the Department in an amount not to exceed $10,000 per violation"。

**其他州的 AI 披露义务**：加州、科罗拉多、缅因、新泽西、德克萨斯、犹他等州有程度不一的"告知用户正在与 AI 交流"义务。来源：[AGG《AI Chatbot Compliance ... in 2026》（2026-03-25）](https://www.agg.com/news-insights/publications/ai-chatbot-compliance-key-legal-risks-and-regulatory-considerations-for-businesses-in-2026/)（核验 2026-10-22）。该文只给出州名与"触发时点各异"的描述，**未给法条编号、生效日、罚则**，因此相关细节记为 `[unknown]`，需要逐州查原文后才能列入清单。

**监管风向**：FTC 于 2025-09-11 依 §6(b) 向 Alphabet、Character Technologies、Instagram、Meta、OpenAI、Snap、xAI 七家发出命令，询问其如何 "measure, test, and monitor for negative impacts of this technology on children and teens"、如何使用或共享用户对话中的个人信息。来源：[FTC 新闻稿](https://www.ftc.gov/news-events/news/press-releases/2025/09/ftc-launches-inquiry-ai-chatbots-acting-companions)（核验 2026-10-22）。SayHear 不在七家之列，但这说明陪伴型聊天是该机构的关注方向。`[文档]`

---

## 2. 心理 / 健康类数据

### 2.1 华盛顿 My Health My Data Act（RCW 19.373）

一般主体 2024-03-31 起、small business 2024-06-30 起合规。`[文档]`

来源：[RCW 19.373.010](https://app.leg.wa.gov/rcw/default.aspx?cite=19.373.010)（核验 2026-10-22）；[HB 1155 众议院报告](https://lawfilesext.leg.wa.gov/biennium/2023-24/Htm/Bill%20Reports/House/1155-S.E%20HBR%20PL%2023.htm)（核验 2026-10-22）。

> "Consumer health data" means "personal information that is linked or reasonably linkable to a consumer" which "identifies the consumer's past, present, or future physical or mental health status."
> 列举项含 "Reproductive or sexual health information"、biometric data，以及 "derived or inferred from nonhealth data ... through an algorithm or machine learning"。
> "Regulated entity" means a legal entity that "Conducts business in Washington, or produces or provides products or services that are targeted to consumers in Washington," and that "alone or jointly with others, determines the purpose and means of collecting, processing, sharing, or selling" such data.
> "Small business" 的两个门槛：处理 "<100,000 consumers during a calendar year"，或 "<25,000 consumers" 且 "Derives less than 50 percent of gross revenue from the collection, processing, selling, or sharing"。

关键点：**small business 定义只影响合规起算日，不影响是否适用**。报告原文："The text does not set any general revenue-based trigger for whether an entity is covered." `[文档]` 也就是说，一个 WA 用户即可触发。`[推断]`

义务要点：`[文档]`（章节标题）+ `[推断]`（具体适用）——须有 consumer health data 隐私政策（§19.373.020）、收集与共享须有同意（§19.373.030）、消费者访问 / 删除 / 撤回权（§19.373.040）、禁止在医疗机构周边设地理围栏（§19.373.080）；依 Consumer Protection Act 执法，**有私人诉权**（§19.373.090）。

### 2.2 内华达 Consumer Health Data Privacy（NRS 603A.400–.550，SB 370）

生效 2024-03-31（NRS 标注 "Added to NRS by 2023, 3453/3454"）。`[文档]`

来源：[NRS 603A](https://www.leg.state.nv.us/NRS/NRS-603A.html)（核验 2026-10-22，正文已逐字抽取）。

> "Consumer health data" means personally identifiable information that is linked or reasonably capable of being linked to a consumer and that a regulated entity uses to identify the past, present or future health status of the consumer. The term: Includes, without limitation: (a)(2) "Social, psychological, behavioral or medical interventions"; ... (d) "Any information described in paragraph (a), (b) or (c) that is derived or extrapolated from information that is not consumer health data, including ... inferred or emergent data derived through the algorithm, machine learning or any other means."
> "Regulated entity" means any person who: 1. "Conducts business in this State or produces or provides products or services that are targeted to consumers in this State"; and 2. "Alone or with other persons, determines the purpose and means of processing, sharing or selling consumer health data."
> §603A.490 适用范围排除 HIPAA、GLBA、42 CFR Part 2 等，不含小型企业。

同样**无规模门槛**。`[文档]`

### 2.3 康涅狄格 CTDPA 的 consumer health data

来源：[Manatt《Connecticut's New Law on Consumer Health Data Is Now in Effect》](https://www.manatt.com/connecticuts-new-law-on-consumer-health-data-is-n)（核验 2026-10-22）；[Latham & Watkins](https://www.lw.com/en/insights/2023/07/Connecticut%20Passes%20Significant%20Amendments%20to%20the%20Connecticut%20Data%20Privacy%20Act)（核验 2026-10-22）。健康数据条款自 2023-10-01 起适用。`[文档]`

consumer health data 被列入 "sensitive data"，处理前须 **opt-in 同意**；并且"consumer health data provisions apply to any person/entity that conducts business in Connecticut or targets products/services to CT residents — not just those meeting the CTDPA's volume thresholds"（二手来源概括，`[推断]`）。2026 年修正案（PA 25-113 / SB 1295，2026-07-01 生效）把门槛降到 35,000 消费者，并新增"处理 sensitive data 即适用、无数量门槛"的触发条件。`[unknown]`：该 2026 修正案的原文未逐字核验，只依据律所与合规厂商的概括。

### 2.4 FTC Health Breach Notification Rule（16 CFR Part 318）

2024 修正案 2024-05-30 公布、**2024-07-29 生效**。`[文档]`

来源：[16 CFR 318.2（Cornell LII）](https://www.law.cornell.edu/cfr/text/16/318.2)、[318.3](https://www.law.cornell.edu/cfr/text/16/318.3)、[318.4](https://www.law.cornell.edu/cfr/text/16/318.4)（均核验 2026-10-22）；[89 FR 47028 定稿公告](https://www.govinfo.gov/content/pkg/FR-2024-05-30/html/2024-10855.htm)（核验 2026-10-22）。

> "Covered health care provider" means "a provider of services (as defined in 42 U.S.C. 1395x(u)), a provider of medical or other health services (as defined in 42 U.S.C. 1395x(s)), or any other entity furnishing health care services or supplies."
> "Health care services or supplies means any online service such as a website, mobile application, or internet-connected device that provides mechanisms to track diseases, health conditions, diagnoses or diagnostic testing, treatment, medications, vital signs, symptoms, bodily functions, fitness, fertility, sexual health, sleep, mental health, genetic information, diet, or that provides other health-related services or tools."
> "Personal health record (PHR) means an electronic record of PHR identifiable health information on an individual" that "has the technical capacity to draw information from multiple sources" and "is managed, shared, and controlled by or primarily for the individual."
> "PHR identifiable health information" ... "Relates to the past, present, or future physical or mental health or condition of an individual" ... "Is created or received by a: (i) Covered health care provider; (ii) Health plan ...; (iii) Employer; or (iv) Health care clearinghouse ..."
> §318.4(a)：通知须 "without unreasonable delay and in no case later than 60 calendar days after the discovery of a breach"。
> §318.3(a)：须通知受影响个人、FTC，以及 500 人以上州 / 司法辖区的 prominent media outlets。

FTC 已于 2026-09-09 撤回 2021 年的 Health App Breach Policy Statement，理由是规则本身已覆盖同类情形；**16 CFR Part 318 仍然有效**。`[文档]`（依据多家律所与合规媒体对撤回公告的报道，撤回公告原文未逐字核验，记为 `[unknown]`。）

**适用性判断**：SayHear 记录用户情绪与心理状态，是"electronic record"，由用户本人控制；若被认为提供 tracking mental health 的 online service，则可能同时落入 "covered health care provider" 与 "vendor of personal health records" 两个角色。`[推断]` 触发条件是发生"breach of security"（含未经授权的**披露**，不只是黑客入侵）时的通知义务，**无规模门槛**。`[推断]` 这是本清单中最容易被漏掉、且在把数据发往第三方 LLM 时最相关的一条。

---

## 3. 一般州隐私法与 FTC Act §5

### 3.1 CCPA/CPRA 适用门槛

来源：[Cal. Civ. Code §1798.140](https://california.public.law/codes/civil_code_section_1798.140)（核验 2026-10-22）；[CPPA 通胀调整页](https://cppa.ca.gov/regulations/cpi_adjustment.html)（核验 2026-10-22）。

> §1798.140(d)(1)：for-profit，doing business in California，并满足以下**之一**：
> (A) "had annual gross revenues in excess of twenty-five million dollars ($25,000,000) in the preceding calendar year"（"as adjusted pursuant to subdivision (d) of Section 1798.199.95"）；
> (B) "[a]lone or in combination, annually buys, sells, or shares the personal information of 100,000 or more consumers or households."；
> (C) "Derives 50 percent or more of its annual revenues from selling or sharing consumers' personal information."
> CPPA："$26,625,000"（原 $25,000,000），"Effective 1/1/2025; posted 12/17/2024"，对应 "Civil Code § 1798.140(d)(1)(A)"。

判断：几十人免费内测，年收入远低于 $26,625,000，用户量远低于 100,000，且不售卖 / 共享个人信息（不上第三方广告与行为追踪）→ **不触发 CCPA/CPRA**。`[推断]` 注意 (B) 的 "shares" 口径包含为跨上下文行为广告目的的披露；只要不接第三方追踪 / 广告 SDK，这一条也不成立。`[推断]`

### 3.2 FTC Act §5：隐私政策须与实际做法一致

FTC 的执法理论：隐私政策是向消费者作出的 affirmative representation，实际做法与政策不一致即构成 deceptive practice，无论是否有意。`[文档]`（依据 FTC 健康 App 执法史的律所分析：[Holland & Knight](https://www.hklaw.com/en/insights/publications/2023/02/ftc-seeks-firstever-health-breach-notification-rule-enforcement)、[FTC Legal Library: U.S. v. Easy Healthcare Corp.](https://www.ftc.gov/legal-library/browse/cases-proceedings/202-3186-easy-healthcare-corporation-us-v)，均核验 2026-10-22。）

最相关的先例：**Easy Healthcare / Premom（2023）**，FTC 指其 fertility app 违反隐私表述与包括两家中国公司在内的第三方共享敏感个人信息，同时也是首例 HBNR 执法。`[文档]`

对 SayHear 的直接含义：只要产品把用户内容发往 DeepSeek（数据存中国境内），隐私政策就必须**明确写出**这一点（接收方、所在地、用途、保留期），不能只写"与可信服务提供商共享"。`[推断]` 若隐私政策说"数据仅存于美国"而实际 fallback 发往中国，就同时踩中 §5 deceptive 与 HBNR 的"未经授权披露"两条线。`[推断]`

---

## 4. 把美国人数据发往中国的限制：DOJ 28 CFR Part 202

2025-01-08 公布（90 FR 1706），2025-04-08 生效，2025-07-08 起全面合规。`[文档]`

来源：[28 CFR 202.205](https://www.law.cornell.edu/cfr/text/28/202.205)、[202.208](https://www.law.cornell.edu/cfr/text/28/202.208)、[202.209](https://www.law.cornell.edu/cfr/text/28/202.209)、[202.210](https://www.law.cornell.edu/cfr/text/28/202.210)、[202.241](https://www.law.cornell.edu/cfr/text/28/202.241)、[202.301](https://www.law.cornell.edu/cfr/text/28/202.301)、[202.401](https://www.law.cornell.edu/cfr/text/28/202.401)（均核验 2026-10-22）。

"Bulk" 门槛（§202.205），按"at any point in the preceding 12 months"计算，且可 "aggregated across covered data transactions involving the same U.S. person and the same foreign person or covered person"：

| 数据类别 | 门槛 |
| --- | --- |
| Personal health data | "more than 10,000 U.S. persons" |
| Covered personal identifiers | "more than 100,000 U.S. persons" |
| Biometric identifiers | "more than 1,000 U.S. persons" |
| Precise geolocation data | "more than 1,000 U.S. devices" |
| Human genomic data | "more than 100 U.S. persons" |

§202.241 "Personal health data" 明文覆盖 "past, present, or future physical or **mental health or condition** of an individual"，并含 "social, psychological, behavioral, and medical diagnostic, intervention, and treatment history"。SayHear 的日记内容落在这一类。`[文档]`

§202.208："The term China means the People's Republic of China"，含香港、澳门特区及其政治分区、机构。`[文档]`

§202.210：covered data transaction = 涉及 country of concern 或 covered person 对 bulk U.S. sensitive personal data 的访问，且属于 data brokerage / vendor agreement / employment agreement / investment agreement 之一。`[文档]`

§202.301(a) 禁止 data brokerage；§202.401(a) 的 vendor agreement 属"受限交易"，须满足 subpart D 的 security requirements 才被授权。§202.401(c) Example 2 原文：一家美国公司与 covered person 签 vendor agreement 存储 bulk personal health data，自认为采取了替代控制措施，"Because the U.S. person has not complied with the security requirements, the vendor agreement is not authorized" 因而 "is a prohibited transaction"。`[文档]`

**对 SayHear 的判断**：内测几十人时，personal health data 门槛 10,000 人、identifiers 门槛 100,000 人都远未达到 → **不触发**。`[推断]` 但这是数量型触发，不是结构型豁免：一旦美国用户跨过 10,000 而 fallback 仍走中国境内 Provider，就进入受限交易区间。`[推断]` 另外，[Christian & Barton 的分析](https://www.cblaw.com/wp-content/uploads/2025/08/ChristianBarton_DOJ-Data-Security-Program.pdf)指出匿名化 / 假名化 / 加密在 Part 202 下**不构成**豁免，这是二手来源，记为 `[推断]`。

其他相关限制：财政部 31 CFR Part 850（outbound investment，2025-01-02 生效）与 SayHear 无直接关系（非投资行为）。`[推断]`

---

## 5. COPPA（16 CFR Part 312）

来源：[FTC COPPA Rule 页](https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa)（核验 2026-10-22）；[Kirkland 2025-04 提示](https://www.kirkland.com/publications/2025/04/ftc-publishes-coppa-rule)（核验 2026-10-22）。

> 规则适用于 "operators of websites or online services directed to children under 13 years of age" 或 "that have actual knowledge that they are collecting personal information online from a child under 13 years of age"。

2025 修正案 2025-04-22 公布、2025-06-21 生效、**2026-04-22 起全面合规**（今天已过全面合规日）。要点：向第三方披露前须单独 opt-in 的 verifiable parental consent；biometric identifiers 纳入 personal information；须有书面数据保留政策（不得无限期保留）。`[文档]`

对 SayHear：产品不面向儿童，且情绪 / 心理状态内容对未成年人风险高，**常见且低成本的做法是设置 13 岁或 18 岁年龄门槛并在注册处声明**，从而落在 "actual knowledge" 之外。`[推断]` 同时这与 CA §22604（"companion chatbots may not be suitable for some minors"）和 CA §22602(c)（仅对 operator **knows** 是 minor 的用户生效）的方向一致：年龄门槛做严，未成年人义务就不触发。`[推断]` 民事罚则约 $53,088 / 次（2025 通胀调整，二手来源）。`[推断]`

---

## 6. 三阶段义务触发清单

| 义务 | A：仅开发者本人 | B：邀请制内测（几十美国用户，免费） | C：公开上线（美国用户） |
| --- | --- | --- | --- |
| CA SB 243 §§22601–22606 | `[推断]` 不触发（无加州用户；operator 定义以"a user in the state"为要件） | **触发**（无规模门槛）：AI 披露、自杀 / 自伤规程 + 网站上公布、§22604 未成年人警示；§22603 年度报告自 2027-07-01 起；有私人诉权（≥$1,000/次） | 全部触发，含 2027-07-01 起的年度报告 |
| NY GBL Art. 47 | `[推断]` 不触发（无纽约用户） | **触发**（无规模门槛）：检测 + 转介规程、会话开始及至少每 3 小时的"非人类"披露；AG 执法 ≤$15,000/天，无私人诉权 | 全部触发 |
| NV NRS 433.567 | `[推断]` 不触发（不在该州提供） | **只要不宣称提供心理治疗、不用 therapist/counselor 等称谓、不构成"practice of professional mental or behavioral health care"**，可落在自我帮助例外内；话术涉"疗愈 / 治疗情绪问题"则风险上升。≤$15,000/次 | 同左，但营销面扩大后话术风险显著上升 |
| IL WOPR Act | `[推断]` 不触发 | 同左逻辑：产品定位为"日记 / 陪伴"而非 therapy or psychotherapy services（"diagnose, treat, or improve"）即可落在 self-help 例外；≤$10,000/次 | 同左 |
| WA MHMDA / NV 603A / CT 健康数据 | `[推断]` 不触发（无该州用户；且"targeted to"存疑） | **触发，无规模门槛**：隐私政策、收集 / 共享同意、消费者访问 / 删除权、geofence 禁止。WA 有私人诉权 | 全部触发 |
| FTC HBNR 16 CFR 318 | `[推断]` 不触发（用户即本人，非美国消费者） | **可能触发，无规模门槛**：一旦发生未经授权披露（含发给第三方）须 60 日内通知个人 + FTC +（500+）媒体 | 触发 |
| CCPA/CPRA | 不触发 | `[推断]` 不触发（<100,000、<$26.625M、无售卖 / 共享） | `[推断]` 初期不触发；用户或收入过线即触发 |
| FTC Act §5 | `[推断]` 不触发（无消费者） | **触发（一般性、无门槛）**：隐私政策必须与实际一致，含 DeepSeek fallback 数据落在中国境内这一事实 | 触发 |
| DOJ 28 CFR Part 202 | `[unknown]` 取决于开发者是否为 U.S. person | `[推断]` 不触发（远低于 10,000 / 100,000 门槛） | **超过 10,000 美国用户且 fallback 仍走中国境内即进入受限交易区间**；换 fallback 可结构性规避 |
| COPPA 16 CFR 312 | 不触发 | `[推断]` 不触发（设 13+/18+ 年龄门槛且无 actual knowledge） | 同左 |

---

## 7. 关键 unknown 与决策点

1. `[unknown]` 开发者本人是否为 U.S. person（国籍 / 永久居留）。这决定阶段 A 下 DOJ Part 202 与部分州法是否适用。需 Luke 确认。
2. `[unknown]` 产品是否会"主动提出情绪相关问题"（NY §1700 定义的第 (ii) 项）。若从不主动提问，纽约法的适用性存在解释空间；若会，则第 (i)+(ii)+(iii) 三项全部命中，没有任何争辩余地。这是产品设计问题，不是法律问题。
3. `[unknown]` 各州 AI 披露法（CO / ME / NJ / TX / UT 等）的法条编号、生效日与罚则未逐字核验，只依据 AGG 2026-03-25 的概括。需要逐州查原文。
4. `[unknown]` Connecticut 2026 修正案（PA 25-113）原文未核验，"处理 sensitive data 无数量门槛即适用"这一条来自律所概括。
5. `[unknown]` FTC 撤回 2021 Health App Breach Policy Statement 的公告原文未逐字核验；结论是 16 CFR Part 318 仍有效，依据多家律所的一致报道。
6. `[unknown]` SayHear 是否会被 FTC 认定为 HBNR 下的 "covered health care provider" / "vendor of personal health records"。定义文本对 app 开放，但 SayHear 是"日记 + 陪伴"而不是"追踪疾病 / 症状"的工具，落在哪一侧没有先例。
7. `[unknown]` 邀请制内测用户的实际州分布。上面所有"触发"判断都以"至少一名用户在该州"为前提；如果内测名单可以先做州筛选（例如只邀请非 CA/NY/WA/NV/IL/CT 的用户），可以显著推迟多数义务，但这会限制内测代表性，属产品决策。

**足以支撑决策的最小结论**：阶段 B 就已经确定触发 CA SB 243、NY GBL 47 与 consumer health data 三法（只要有一名该州用户，且都无规模门槛），且 CA 有私人诉权。这三项义务的技术成本都不高（身份披露、危机转介、规程公开、隐私政策 + 同意 + 删除通道），可以在阶段 B 前一次做完。真正会随规模变化的是 DOJ Part 202 与 CCPA：两者都是数量型触发，可以在用户接近 10,000 美国用户前把 fallback 从 DeepSeek 换成美国境内 Provider，从而结构性规避。
