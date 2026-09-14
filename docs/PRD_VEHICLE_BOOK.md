# AI Vehicle Knowledge Assistant / 车书

> Product Requirements Document (PRD)  
> Status: Draft for portfolio pivot  
> Product type: Simulated, local-first portfolio project  
> Repository baseline: `baseline-cockpit-agent`  
> Last updated: 2026-09-14

## 1. Product summary

车书是一个面向车主、售后支持人员和汽车知识运营人员的车辆知识助手。它根据用户当前选择的品牌、车型、年款、配置和软件版本，从本地模拟知识库中检索适用内容，给出带来源和适用范围的回答；同时为知识维护、检索评估、内容质量治理和发布门禁提供一套可演示的闭环。

本项目不会从零重建。现有 AI Cockpit Agent 已具备单 Agent、Function Calling、本地手册 BM25 检索、确定性安全规则、Mock Vehicle State、Gradio UI、pytest 和轻量 Eval。产品重心将从“执行座舱控制”转向“可信、版本感知的车辆知识问答”，原有工具调用与安全能力保留为辅助演示能力。

一句话定位：**能先确认“你问的是哪一辆车、哪个版本”，再基于匹配资料回答并说明依据的车辆知识助手。**

## 2. Background and opportunity

车辆知识天然具有强上下文依赖。同一问题的答案可能因 OEM、车型、年款、市场、动力类型、配置、选装包或车机软件版本不同而变化。仅把多份手册放入通用向量库，会带来几类典型风险：

- 跨车型误检：将另一车型的操作步骤回答给当前车辆。
- 跨配置误答：将高配或选装功能描述为全系标配。
- 版本过期：软件升级后菜单路径或功能行为已经改变。
- 来源不可审计：用户或内容人员无法判断答案来自哪份资料。
- 内容发布无门禁：新增资料可能提升覆盖率，却导致串车率、过期引用率或拒答质量恶化。

该项目的作品集价值不在于模拟一个“全知车载聊天框”，而在于展示一套可解释的产品与工程方法：车辆身份解析、元数据过滤、分层检索、证据约束生成、知识版本控制、离线评估、内容治理和发布质量门禁。

## 3. Goals and success definition

### 3.1 Product goals

1. 支持多个模拟 OEM、车型、年款、配置和软件版本的车辆知识问答。
2. 在检索前解析车辆上下文，并优先使用严格匹配的知识，降低跨车、跨配置和跨版本误答。
3. 每个事实性回答展示可核验的来源、文档版本和适用车辆范围。
4. 对证据不足、车辆信息缺失、知识冲突和高风险问题进行明确澄清、降级或拒答。
5. 建立从内容入库、校验、评估到发布的模拟知识治理流程。
6. 用可复现的测试集和质量门禁证明迭代没有破坏关键能力。

### 3.2 Portfolio success

项目演示应让评审者在 3–5 分钟内看清以下能力：

- 同一问题在不同车辆或软件版本下返回不同且正确的答案。
- 缺少关键车辆信息时，系统先澄清，而不是猜测。
- 回答可追溯到具体模拟文档与章节。
- 错误或冲突内容能够被治理流程拦截。
- 变更前后可通过离线 Eval 报告比较，发布由明确阈值决定。

### 3.3 Non-goals as success constraints

“看起来像生产系统”不是目标。所有车辆、文档、版本、账号、工单和发布流程均为本地模拟数据或测试夹具；界面必须持续展示这一边界，不得暗示已连接真实 OEM、车辆或售后系统。

## 4. User personas

### P1：车主 / 潜在车主

- 场景：查找功能使用方法、指示灯含义、保养建议、配置差异或软件更新后的菜单位置。
- 需求：答案简洁、适用于自己的车辆、能看到来源；在不确定时得到下一步建议。
- 痛点：纸质手册难搜索，网络答案车型混杂，软件更新后旧教程失效。

### P2：一线售后支持专员

- 场景：在模拟客服对话中快速定位适用说明，核对版本差异并形成可复述答复。
- 需求：高召回、明确适用范围、可复制的来源信息、对冲突或缺失内容有提示。
- 痛点：资料分散，人工判断车型版本耗时，误用其他车型资料会降低可信度。

### P3：汽车知识运营 / 内容管理员

- 场景：维护模拟手册、FAQ、版本说明，检查元数据，发起评估并决定是否发布。
- 需求：内容状态、版本关系、覆盖范围、冲突检测、评估结果和变更记录可见。
- 痛点：内容质量难量化，新增资料的检索副作用通常到上线后才暴露。

### P4：AI / 产品评审者

- 场景：审查作品集的系统设计、RAG 质量、测试方法和产品边界。
- 需求：能够复现实验、查看失败案例，并区分已实现能力与规划能力。

## 5. User stories

| ID | Persona | User story | Acceptance summary |
| --- | --- | --- | --- |
| US-01 | 车主 | 作为车主，我希望选择自己的车辆身份后提问，以得到只适用于该车的答案。 | 回答引用的内容满足硬性车辆元数据约束。 |
| US-02 | 车主 | 当我只说“怎么开启自动泊车”时，我希望系统在必要时询问车型或版本。 | 缺少会改变答案的关键上下文时不直接生成确定性步骤。 |
| US-03 | 车主 | 我希望看到答案来源和适用范围，以判断是否可信。 | 每个知识型回答至少包含一个可展开引用；无引用则降级。 |
| US-04 | 车主 | 我切换软件版本后，希望相同问题能返回对应版本的菜单路径。 | 版本化测试用例的答案和引用同步变化。 |
| US-05 | 售后 | 我希望同时看到命中文档、章节和版本冲突提示，以便快速核验。 | 调试视图展示查询上下文、候选来源、分数与过滤原因。 |
| US-06 | 内容管理员 | 我希望导入一批模拟资料并在发布前发现缺失或非法元数据。 | 校验失败的文档不能进入可检索的 published 集合。 |
| US-07 | 内容管理员 | 我希望比较候选知识版本与当前版本的评估结果。 | 报告包含整体、切片、回归和失败案例。 |
| US-08 | 内容管理员 | 我希望只有通过质量门禁的知识快照才可被标记为已发布。 | 任一硬门禁失败时发布被阻止并给出原因。 |
| US-09 | 评审者 | 我希望一键运行单元测试和离线 Eval，复现项目声明的指标。 | 仓库内命令、固定数据集和结果格式明确。 |
| US-10 | 车主 | 对安全或维修高风险问题，我希望得到谨慎且不越界的建议。 | 不提供无证据诊断；建议安全停车、查阅适用资料或联系专业服务。 |

## 6. Scope

### 6.1 MVP scope

- 使用本地模拟资料覆盖至少 2 个虚构 OEM、每个 OEM 至少 2 个车型，并包含可验证的配置或软件版本差异。
- 提供显式车辆选择器，并在会话中保存当前车辆上下文。
- 建立规范化车辆元数据模型、知识分类体系和文档生命周期状态。
- 将现有单手册 BM25 扩展为“元数据硬过滤 + 词法检索”的可解释检索流程；是否增加语义检索由实现阶段实验决定，不作为 MVP 必需项。
- 回答包含结论、适用范围、来源引用和必要的风险提示。
- 支持上下文缺失澄清、无结果降级、版本回退提示、冲突提示和安全拒答。
- 提供面向作品集的知识管理视图或报告：文档列表、版本、状态、校验问题和覆盖统计。
- 建立检索级与回答级离线评估集、切片指标、回归对比和发布质量门禁。
- 保留现有 Mock Vehicle State、Tool Calling 和安全 Guardrail，作为“知识问答 + 有限模拟操作”的次要能力。

### 6.2 Non-scope

- 不接入真实车辆 CAN、SOME/IP、DDS、车云平台或远程控车能力。
- 不接入真实 OEM 内容管理系统、经销商系统、工单、VIN 服务或账号体系。
- 不抓取、复制或声称拥有真实厂商受版权保护的完整手册；演示内容使用原创的虚构资料或最小测试夹具。
- 不提供真实故障诊断、维修决策、紧急救援或自动驾驶建议。
- 不承诺生产级信息安全、功能安全、隐私合规、SLA 或安全认证。
- 不训练或微调基础模型；MVP 不建设复杂多 Agent 架构。
- 不做语音 ASR/TTS、高保真车机 HMI、移动 App 或真实多租户权限系统。
- 不将“联网搜索”作为车辆事实的默认兜底来源。

## 7. Product principles

1. **Vehicle context before answer**：先确定车辆适用范围，再检索和生成。
2. **Metadata is a hard boundary**：OEM、车型、市场等硬约束不能仅靠相关性分数覆盖。
3. **Evidence over fluency**：证据不足时宁可澄清或拒答，不用语言流畅度掩盖缺口。
4. **Version is visible**：用户能看到所依据的软件和文档版本以及回退情况。
5. **Safe by deterministic rule**：关键安全限制继续由工具侧确定性规则执行。
6. **Evaluation by slices**：总体平均分不能掩盖某 OEM、车型、版本或风险类别的失败。
7. **Simulated honestly**：所有界面、文档和演示均明确标注 Mock / Simulated。

## 8. Core flows

### 8.1 Vehicle-scoped Q&A

1. 用户从预置目录选择 OEM → 车型 → 年款 → 配置 → 市场 → 软件版本。
2. 系统生成规范化 `vehicle_context` 并展示在会话顶部。
3. 用户提出车辆知识问题。
4. 查询理解模块识别主题、意图、风险等级和可能的版本敏感性。
5. 检索器先按车辆与内容状态做硬过滤，再对剩余章节评分并返回候选证据。
6. 回答模块只根据合格证据生成答案，并附引用、适用范围和置信状态。
7. 用户可展开“为什么是这个答案”，查看命中章节、版本和过滤摘要。

### 8.2 Missing-context clarification

1. 用户未选择车辆，或问题涉及一个会改变答案但尚未提供的字段。
2. 系统检查候选内容是否存在多种互斥答案。
3. 若存在歧义，系统提出一个最小化澄清问题，例如车型、配置或软件版本。
4. 用户补充后更新会话上下文并重新检索；若无法补充，则仅提供明确标注的通用信息或说明无法确认。

### 8.3 Version-aware answer and controlled fallback

1. 系统优先匹配目标软件版本和目标文档的有效期。
2. 若无精确版本内容，可按已声明的兼容关系查找同一版本系列或最近的较低兼容版本。
3. 任何回退都必须在答案中显式说明“未找到精确版本资料”、实际引用版本及可能差异。
4. 不得跨 OEM、车型或市场自动回退；不得将更高软件版本内容默认用于更低版本。

### 8.4 Knowledge ingestion and review

1. 内容管理员添加本地模拟 Markdown/JSON 文档及其 manifest。
2. 系统校验必填元数据、枚举值、版本格式、有效期、重复 ID、引用锚点和内容完整性。
3. 文档被切分为可引用章节，并继承文档级元数据。
4. 校验通过后进入 `validated` 候选快照；校验失败则保留报告但不进入发布索引。
5. 管理员查看覆盖、冲突和变更摘要，运行离线 Eval。
6. 仅当发布门禁全部通过，候选快照才可标记为 `published`；旧快照保留以支持回滚演示。

### 8.5 Retrieval evaluation and release

1. 固定评估集包含问题、车辆上下文、期望文档/章节、不可接受来源和期望回答要点。
2. 在当前已发布快照与候选快照上分别运行评估。
3. 报告展示整体指标以及 OEM、车型、软件版本、主题、风险等级和问题类型切片。
4. 系统列出新增失败与已修复案例。
5. 硬门禁自动给出 Pass/Fail；失败时不得发布，管理员可修复内容或显式放弃候选版本。

### 8.6 Existing simulated action flow

1. 用户提出有限的座舱操作请求。
2. Agent 调用现有本地工具更新 Mock Vehicle State，而不是声称控制真实车辆。
3. 工具侧验证参数范围和车门安全规则。
4. 操作被拒绝时，Agent解释原因且不能绕过 Guardrail。

该流程为兼容能力，不是车书 MVP 的主叙事；知识问答与操作请求必须在 UI 和评估中可区分。

## 9. Knowledge taxonomy

每个知识单元必须属于一个一级分类，并可拥有多个二级标签。

| Level 1 | Example Level 2 tags | Typical questions | Default risk |
| --- | --- | --- | --- |
| Getting started / 快速入门 | 交付检查、钥匙、账号、首次设置 | “提车后先设置什么？” | Low |
| Controls & HMI / 操作与界面 | 中控、仪表、方向盘、快捷入口 | “在哪里开启自动驻车？” | Low |
| Comfort / 舒适功能 | HVAC、座椅、车窗、灯光 | “座椅加热有几档？” | Low |
| Infotainment / 车机娱乐 | 蓝牙、媒体、语音、应用 | “怎么连接手机？” | Low |
| Connectivity / 互联 | Wi-Fi、手机钥匙、远程能力说明 | “为什么手机钥匙不可用？” | Medium |
| Driving & ADAS / 驾驶辅助 | 巡航、泊车、车道辅助、限制条件 | “雨天能用车道保持吗？” | High |
| Charging & Energy / 补能与能耗 | 充电、续航、能量回收、燃油 | “快充功率为什么下降？” | Medium |
| Warnings & Troubleshooting / 告警与排查 | 指示灯、提示语、基础自查 | “胎压灯亮了怎么办？” | High |
| Maintenance / 保养维护 | 周期、耗材、轮胎、存放 | “多久更换制动液？” | High |
| Safety & Emergency / 安全与应急 | 车门、儿童安全、事故、拖车 | “车辆冒烟怎么办？” | Critical |
| Specifications / 参数配置 | 尺寸、容量、配置、选装 | “这个版本有热泵吗？” | Medium |
| Software & Release Notes / 软件与版本 | OTA、菜单变化、已知限制 | “升级后入口在哪里？” | Medium |
| Policy & Service / 服务说明 | 保修说明、服务渠道、术语 | “这个问题是否属于保修？” | High |

内容类型 `content_type` 至少支持：`owner_manual`、`quick_guide`、`faq`、`release_note`、`service_bulletin_mock`、`safety_notice_mock`。后两类必须带 `mock` 命名，避免被误认为真实厂商材料。

## 10. Vehicle and knowledge metadata

### 10.1 Vehicle identity

MVP 使用显式选择器和虚构 `vehicle_profile_id`，不解析真实 VIN。

| Field | Required | Example | Rule |
| --- | --- | --- | --- |
| `oem_id` | Yes | `aurora_motors` | 规范化 ID；检索硬过滤。 |
| `brand_name` | Yes | `Aurora` | 展示名称，不参与唯一性判断。 |
| `model_id` | Yes | `a7` | 在 OEM 内唯一；检索硬过滤。 |
| `model_year` | Yes | `2026` | 四位整数；允许文档声明范围。 |
| `market` | Yes | `CN` | ISO 风格受控枚举；检索硬过滤。 |
| `language` | Yes | `zh-CN` | 首选内容语言；允许显式跨语言降级。 |
| `powertrain` | Yes | `BEV` | 受控枚举：BEV/PHEV/ICE/HEV（仅模拟）。 |
| `trim_id` | Yes | `premium` | 配置版本；可由文档声明 `all`。 |
| `option_codes` | No | `["PKG_ADAS_P"]` | 用于选装能力判断；不应从自然语言臆测。 |
| `head_unit_version` | Yes | `OS 3.2.1` | SemVer-like 规范化值。 |
| `region_config` | No | `CN-mainland` | 仅在资料明确依赖地区设置时使用。 |
| `vehicle_profile_id` | Yes | `aurora-a7-2026-cn-premium-os321` | 上述字段的稳定引用。 |

### 10.2 Document metadata

| Field | Required | Purpose |
| --- | --- | --- |
| `document_id` | Yes | 跨版本稳定的逻辑文档 ID。 |
| `document_version` | Yes | 内容自身版本，与车机软件版本分离。 |
| `title` | Yes | 人可读名称。 |
| `content_type` | Yes | 知识类型与来源优先级。 |
| `source_uri` | Yes | 本地相对路径或模拟 URI；不得伪造生产链接。 |
| `source_label` | Yes | 引用中展示的来源名称。 |
| `status` | Yes | `draft` / `validated` / `published` / `retired`。 |
| `effective_from` | Yes | 内容生效日期。 |
| `effective_to` | No | 内容失效日期；为空表示尚未声明失效。 |
| `supersedes` | No | 被当前版本替代的文档版本。 |
| `applicability` | Yes | OEM、车型、年款、市场、动力、配置、选装和软件版本约束。 |
| `taxonomy` | Yes | 一级分类与二级标签。 |
| `risk_level` | Yes | `low` / `medium` / `high` / `critical`。 |
| `locale` | Yes | 文档语言和地区。 |
| `owner` | Yes | 模拟内容责任角色，不使用真实个人信息。 |
| `reviewed_at` | Yes for publish | 最近一次模拟审核时间。 |
| `checksum` | Yes for publish | 支持快照一致性和变更检测。 |

### 10.3 Chunk metadata

每个切分后的知识单元至少包含：`chunk_id`、`document_id`、`document_version`、`section_path`、`anchor`、`text`、`applicability`、`taxonomy`、`risk_level`、`effective_from/to`、`status` 和 `checksum`。引用必须能够定位到章节，而不只定位到整份文件。

### 10.4 Matching rules

- **Hard match**：`oem_id`、`model_id`、`market`、`status=published` 和有效期必须匹配。
- **Applicable match**：年款、动力、配置、选装与软件版本必须命中明确范围、`all` 或声明的兼容关系。
- **Soft preference**：语言、内容类型优先级和文档新鲜度可参与排序，但不得突破硬约束。
- **Version order**：精确版本 > 明确兼容版本范围 > 同系列已声明回退版本。无兼容声明则视为不适用。
- **Source precedence**：在同等适用性下，安全通知 > 车主手册 > 快速指南 > FAQ > Release Note；若来源互相矛盾，不静默选择，进入冲突处理。

## 11. Functional requirements

优先级：P0 = MVP 必须；P1 = MVP 后优先；P2 = 未来探索。

### 11.1 Vehicle context

| ID | Priority | Requirement | Acceptance criteria |
| --- | --- | --- | --- |
| FR-VC-01 | P0 | 提供层级车辆选择器。 | 后续选项受上级约束，不出现不存在的组合。 |
| FR-VC-02 | P0 | 会话保存并展示当前车辆上下文。 | 每次回答可追溯到一次确定的 context snapshot。 |
| FR-VC-03 | P0 | 支持会话中切换车辆并清除旧检索上下文。 | 切换后相同问题按新车辆重新检索，不复用旧引用。 |
| FR-VC-04 | P0 | 缺少关键字段时触发最小澄清。 | 版本敏感问题缺版本时不输出唯一确定步骤。 |
| FR-VC-05 | P1 | 从自然语言提出上下文候选。 | 仅作为待确认候选，用户确认前不作为硬事实。 |

### 11.2 Retrieval and answer generation

| ID | Priority | Requirement | Acceptance criteria |
| --- | --- | --- | --- |
| FR-RG-01 | P0 | 查询进入排序前执行元数据硬过滤。 | 评估日志可见过滤前后数量，跨 OEM/车型硬违规为 0。 |
| FR-RG-02 | P0 | 支持 top-k 章节检索并保留分数与理由。 | 调试视图能展示候选、分数、适用性和排除原因。 |
| FR-RG-03 | P0 | 仅基于合格证据生成事实性答案。 | 回答中的关键可验证主张能映射到引用章节。 |
| FR-RG-04 | P0 | 回答展示来源、章节、文档版本、适用车辆和软件版本。 | 用户无需进入日志即可看到最小引用信息。 |
| FR-RG-05 | P0 | 支持无答案阈值和证据不足降级。 | 无合格证据的用例不产生具体操作步骤或参数。 |
| FR-RG-06 | P0 | 实现受控版本回退。 | 回退仅沿 manifest 声明关系，并在答案中提示。 |
| FR-RG-07 | P0 | 检测候选证据中的显著冲突。 | 互斥参数或步骤被标记，回答不静默合并。 |
| FR-RG-08 | P1 | 支持词法与语义混合检索及可选重排。 | 仅在固定评估集上优于 P0 基线且不破坏延迟门禁时启用。 |
| FR-RG-09 | P1 | 支持多轮指代解析。 | “那旧版本呢”等追问继承主题，但重新应用版本过滤。 |

### 11.3 Knowledge management and governance

| ID | Priority | Requirement | Acceptance criteria |
| --- | --- | --- | --- |
| FR-KM-01 | P0 | 使用 manifest 管理文档和适用性元数据。 | 所有 published 文档通过 schema 校验。 |
| FR-KM-02 | P0 | 内容按章节切分并生成稳定 chunk ID。 | 未改变章节的 ID 在重新构建后保持稳定。 |
| FR-KM-03 | P0 | 支持 draft → validated → published → retired 生命周期。 | 只有 published 且在有效期内的内容进入默认检索。 |
| FR-KM-04 | P0 | 生成元数据、重复、空内容、孤立引用和重叠适用性检查报告。 | 任一阻断级问题导致候选构建失败。 |
| FR-KM-05 | P0 | 每次构建产生不可变知识快照 ID 和变更摘要。 | Eval 结果记录快照 ID，可复现对应语料。 |
| FR-KM-06 | P0 | 保留最近一个已发布快照用于回滚演示。 | 回滚后查询和 Eval 均指向旧快照。 |
| FR-KM-07 | P1 | 提供冲突审阅队列和覆盖缺口视图。 | 可按车辆/分类筛选并记录模拟处置结果。 |

### 11.4 Evaluation and release

| ID | Priority | Requirement | Acceptance criteria |
| --- | --- | --- | --- |
| FR-EV-01 | P0 | 评估集同时记录查询、车辆上下文、gold 引用、answer key points 和负例来源。 | 测试集 schema 可自动校验。 |
| FR-EV-02 | P0 | 分离检索评估、回答评估、安全评估和系统回归。 | 报告按四层输出，不以单一总分替代。 |
| FR-EV-03 | P0 | 输出整体与关键切片指标。 | 至少按 OEM、车型、版本、taxonomy、risk 切片。 |
| FR-EV-04 | P0 | 比较 candidate 与 baseline 快照。 | 报告列出绝对变化、新增失败和已修复案例。 |
| FR-EV-05 | P0 | 自动执行硬性发布门禁。 | 任一硬门禁失败时状态为 FAIL，无法标记 published。 |
| FR-EV-06 | P1 | 对评估集做版本化与污染检查。 | 训练/调优集与最终 holdout 的 ID 不重叠。 |

### 11.5 UI and observability

| ID | Priority | Requirement | Acceptance criteria |
| --- | --- | --- | --- |
| FR-UI-01 | P0 | Gradio 主界面突出车辆知识问答与当前车辆。 | 首屏显示“Simulated portfolio project”边界。 |
| FR-UI-02 | P0 | 提供普通用户视图与检索调试视图。 | 普通视图简洁；调试视图展示上下文、过滤、候选和耗时。 |
| FR-UI-03 | P0 | 每轮生成结构化本地 trace。 | trace 包含 request ID、快照 ID、车辆上下文、候选、引用、fallback 和 latency，且不含密钥。 |
| FR-UI-04 | P0 | 展示知识快照和 Eval 摘要。 | 评审者能从 UI 或静态报告确认当前版本是否过门禁。 |
| FR-UI-05 | P1 | 提供内容管理演示页。 | 可浏览文档状态和校验结果；不伪装真实 CMS。 |

### 11.6 Existing tools and safety

| ID | Priority | Requirement | Acceptance criteria |
| --- | --- | --- | --- |
| FR-SF-01 | P0 | 保留工具侧参数验证与移动中禁止开门规则。 | 现有安全 pytest 持续通过。 |
| FR-SF-02 | P0 | 知识问答不能直接改变 Mock Vehicle State。 | 只有明确操作意图且成功调用工具才改变状态。 |
| FR-SF-03 | P0 | 对高风险知识问题应用更严格回答策略。 | Critical 问题必须引用合格证据；否则给出安全降级建议。 |
| FR-SF-04 | P0 | 始终声明系统不控制真实车辆。 | UI 常驻声明；回答不得声称真实动作已执行。 |

## 12. Answer contract

知识型回答使用统一的逻辑结构，UI 表现可以简化：

1. **Direct answer**：先回答用户问题，不堆砌检索过程。
2. **Applicability**：说明当前 OEM / 车型 / 年款 / 配置 / 软件版本。
3. **Steps or explanation**：仅包含证据支持的步骤、条件和限制。
4. **Safety note**：仅在风险等级或内容要求时展示。
5. **Sources**：文档标题、章节、文档版本、适用软件版本。
6. **Confidence state**：`grounded`、`fallback-version`、`conflict`、`insufficient-evidence` 之一；不展示伪精确概率。

回答不得：补全资料未提供的按钮名称、菜单路径、参数、保养周期或故障结论；混合多个车辆的步骤；把旧版本回退内容描述为当前版本确定事实；将模拟资料称为官方生产资料。

## 13. Failure and fallback behavior

| Failure condition | System behavior | User-facing behavior | Logging / evaluation |
| --- | --- | --- | --- |
| 未选择车辆 | 判断问题是否可用通用知识回答；否则澄清。 | 请求最少必要字段，不一次索取全部信息。 | `missing_vehicle_context`。 |
| 缺少配置或软件版本 | 检查答案是否随该字段变化。 | 有歧义则询问；无歧义则说明适用于已知范围。 | `missing_disambiguating_field`。 |
| 精确版本无资料 | 仅沿声明兼容关系回退。 | 明示实际引用版本和不确定性。 | `version_fallback` + source/target。 |
| 无合格检索结果 | 不生成具体事实或步骤。 | “当前模拟知识库没有适用于该车辆的资料”，建议核对车辆或使用专业渠道。 | `no_eligible_evidence`。 |
| 低相关度结果 | 视同证据不足，而非强行回答。 | 提供澄清选项或安全拒答。 | top score、threshold、候选摘要。 |
| 跨车型候选得分高 | 硬过滤排除。 | 不向普通用户展示错误候选。 | 记录 exclusion reason，用于评估串车风险。 |
| 内容冲突 | 暂停确定性回答，展示冲突范围。 | 说明资料不一致并列出可核验来源；高风险时停止给步骤。 | `content_conflict`，进入治理队列。 |
| 内容已过期或 retired | 默认不检索；仅调试模式可见。 | 若没有替代内容则按无证据处理。 | `expired_content_excluded`。 |
| 引用无法定位 | 该证据不允许进入最终回答。 | 使用其他合格证据或降级。 | 构建时优先阻断，运行时记录异常。 |
| LLM / API 不可用 | 不改变状态，不伪造答案。 | 展示简短可重试错误；可选显示纯检索结果。 | `generation_unavailable` 与耗时。 |
| 检索器异常 | Fail closed。 | 说明知识库暂不可用，不给无依据答案。 | 异常类型、request ID。 |
| Tool 参数非法 | 工具侧拒绝。 | 解释允许范围并请用户更正。 | 保留 validator 结果。 |
| 不安全操作 | 工具侧拒绝且不可绕过。 | 简短说明安全原因。 | 安全回归必须命中。 |
| 高风险诊断请求 | 只提供资料中的含义和安全下一步，不做确诊。 | 建议安全停车、检查或联系专业服务；紧急风险优先。 | risk slice 单独评估。 |

## 14. Evaluation framework

### 14.1 Evaluation dataset

MVP 评估集应为仓库内版本化的原创模拟数据，建议至少 80 条，覆盖：

- 精确车型与版本命中。
- 同问不同车、不同配置、不同软件版本的对照组。
- 缺上下文澄清。
- 无答案与超出范围问题。
- 同义词、缩写、中英文混合和轻微拼写错误。
- 冲突、过期、draft/retired 内容排除。
- 高风险安全、告警和维护问题。
- 现有 HVAC、座椅、导航、手册检索和车门安全回归。

每条用例至少包含：`case_id`、`query`、`vehicle_context`、`expected_behavior`、`gold_chunk_ids`、`forbidden_chunk_ids`、`answer_key_points`、`forbidden_claims`、`risk_level` 和 `tags`。

### 14.2 Retrieval metrics

- **Context Eligibility Rate**：top-k 结果中满足车辆、状态、有效期和版本规则的比例。
- **Recall@k**：gold chunk 是否出现在 top-k；报告 @1、@3、@5。
- **MRR**：第一个 gold chunk 的排名质量。
- **Wrong-Vehicle Retrieval Rate**：top-k 中跨 OEM / 车型硬违规的查询比例。
- **Wrong-Version Retrieval Rate**：未声明兼容却引用其他版本的查询比例。
- **No-answer Precision**：系统判定无答案的案例中，确实无合格证据的比例。

### 14.3 Answer metrics

- **Grounded Claim Precision**：抽取的可验证主张中被引用支持的比例。
- **Citation Correctness**：引用是否支持相邻主张且适用于当前车辆。
- **Answer Key-point Coverage**：gold 要点覆盖率。
- **Forbidden Claim Rate**：是否出现评估集中明确禁止的臆测或危险表述。
- **Clarification Accuracy**：需要澄清时是否澄清、不需要时是否避免多余追问。
- **Version Disclosure Accuracy**：精确命中或回退版本是否正确披露。
- **Safety Compliance Rate**：高风险回答与操作是否遵守确定性规则和回答策略。

LLM-as-judge 如被采用，只作为可复查的辅助评分；关键门禁优先使用确定性匹配、引用映射和人工标注的要点。评估报告必须记录模型配置和知识快照 ID，不把一次非确定性运行包装为绝对结论。

### 14.4 System metrics

- 端到端延迟 P50 / P95，以及过滤、检索、生成分段耗时。
- 运行错误率和 fallback 分布。
- 知识覆盖率：按车辆 × taxonomy 统计至少一条 published 内容的组合比例。
- 构建校验通过率、冲突数、过期内容数和未归类内容数。
- pytest 通过率及与 baseline 的回归情况。

## 15. Release criteria and quality gate

### 15.1 MVP release gate

候选知识快照只有同时满足以下条件才能发布：

| Gate | Threshold | Type |
| --- | --- | --- |
| Schema and metadata validation | 100% published candidates valid | Hard |
| Broken citation anchors | 0 | Hard |
| Duplicate active document/chunk IDs | 0 | Hard |
| Wrong-OEM / wrong-model retrieval | 0% on release set | Hard |
| Undeclared wrong-version citation | 0% on release set | Hard |
| Critical safety violations | 0 | Hard |
| Forbidden claims in high/critical cases | 0 | Hard |
| Retrieval Recall@3 | ≥ 90% overall and ≥ 80% per required slice | Hard |
| Citation correctness | ≥ 95% | Hard |
| No-answer precision | ≥ 90% | Hard |
| Clarification accuracy | ≥ 90% | Hard |
| Existing pytest suite | 100% pass | Hard |
| Existing five live-eval behaviors | No regression | Hard when API is configured; otherwise recorded as not run |
| P95 retrieval latency | ≤ 500 ms on documented local reference machine | Soft for portfolio MVP |
| Candidate vs baseline | No hard metric regression; any soft regression explained | Hard/Review |

关键切片至少包括每个 OEM、每个车型、每个软件版本族、`high/critical` 风险和 `no-answer`。若样本量过小，报告必须显示样本数，不得用百分比掩盖覆盖不足。

### 15.2 Release artifacts

每次模拟发布应产出：

- 知识快照 ID、manifest checksum 和构建时间。
- 新增、修改、retired 文档及适用范围变化。
- 全量 Eval 与 baseline 对比报告。
- 门禁 Pass/Fail、失败原因和已知限制。
- 可回滚的上一 published 快照指针。
- 演示使用的模型配置与运行环境说明，不包含密钥。

## 16. MVP delivery plan

### Phase 0 — Preserve and characterize baseline

- 冻结现有 cockpit agent 基线和五个端到端行为。
- 将当前单份 `vehicle_manual.md` 明确标记为 legacy mock fixture。
- 为现有 pytest 和 Eval 输出建立可比较基线。

### Phase 1 — Knowledge model and fixtures

- 定义车辆目录、document manifest、chunk schema 和生命周期。
- 创建至少 2 个虚构 OEM、4 个车型及明确版本差异的原创模拟资料。
- 实现 schema 校验、稳定 chunk ID、知识快照与变更摘要。

### Phase 2 — Version-aware retrieval

- 实现车辆上下文、硬过滤、版本兼容规则和可解释 BM25 排序。
- 增加引用锚点、无答案阈值、冲突检测和受控版本回退。
- 用检索级固定数据集迭代 Recall@k、串车率和版本错误率。

### Phase 3 — Vehicle Book experience

- 将 Gradio 主叙事改为车书，加入车辆选择器、回答引用和调试面板。
- 增加知识清单、快照、覆盖与校验结果的只读治理视图。
- 保留 Cockpit Tools 作为独立的模拟能力区，避免与知识回答混淆。

### Phase 4 — Evaluation and release gate

- 建立至少 80 条评估集和关键切片。
- 产出 candidate vs baseline 报告，实现自动门禁和回滚演示。
- 更新 README、Architecture、Demo Script，并录制核心对照场景。

### MVP exit criteria

- PRD 中所有 P0 项已实现或有明确、公开的偏差记录。
- 至少演示三组“同问不同车/版本不同答”、一组缺上下文澄清、一组无答案、一组冲突拦截和一组安全 Guardrail。
- 第 15 节全部硬门禁通过。
- 从干净环境可按 README 复现测试、构建知识快照和运行 Demo。

## 17. Future roadmap

### Near term

- 以评估结果决定是否引入 embeddings、hybrid retrieval 或轻量 reranker。
- 增加查询改写、别名词典、多轮指代和中英文跨语言检索。
- 改进内容 diff、冲突审阅、覆盖热力图和失败案例聚类。
- 增加基于合成模板与人工复核的评估集扩充工具。

### Medium term

- 模拟 VIN → Vehicle Profile 解析，但仍只使用虚构 VIN 与本地目录。
- 模拟角色权限、审核签核、灰度快照和多环境发布。
- 增加图片/表格章节的多模态检索实验，素材仍为原创或可安全使用的测试资产。
- 引入会话反馈和失败队列，离线演示“反馈 → 修复 → 评估 → 发布”闭环。

### Long term / research

- 探索时态知识图谱表达车型、部件、配置、软件与文档关系。
- 探索检索不确定性校准、自动冲突发现和证据覆盖分析。
- 探索端侧小模型或离线检索，但不在本项目中声称真实车规部署。
- 若未来获得合法数据与明确授权，再单独评估真实 OEM 接入、合规、安全和运维需求；这些不属于当前承诺。

## 18. Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| 模拟数据过于简单，无法证明版本感知价值 | Demo 缺乏说服力 | 设计最小对照集，让相同问题在车型/配置/版本间有可验证差异。 |
| 元数据错误比检索算法更隐蔽 | 产生高置信度误答 | schema、受控枚举、重叠适用性检查和 hard-filter 单测。 |
| 仅优化整体 Recall 导致串车 | 可信度和安全性下降 | 将 wrong-vehicle 与 wrong-version 设为 0 容忍硬门禁。 |
| LLM 评分不稳定 | 指标不可复现 | 确定性指标优先，固定配置，多次运行并保留逐案例结果。 |
| 文档数量小导致架构过度设计 | 交付速度下降 | MVP 保持本地文件 + BM25，只有评估证明收益后才引入新组件。 |
| 作品集被误解为真实车控或官方资料 | 诚信与安全风险 | UI 常驻模拟声明，使用虚构 OEM，文档和 README 明确边界。 |
| 保留操作工具分散主叙事 | 产品定位模糊 | 默认首页以知识问答为核心，操作工具放入独立兼容区。 |

## 19. Dependencies and constraints

- 复用当前 Python、OpenAI Agents SDK 兼容接口、Gradio、pytest 和本地文件结构。
- 当前生成模型通过环境配置调用兼容 API；Eval 应允许在未配置 API 时运行检索与确定性测试，并明确标记生成评估未运行。
- MVP 数据、索引、trace 和报告均保存在本地；不引入未在仓库中实现的生产服务依赖。
- 任何新增依赖都需要以评估收益、可复现性和作品集运行成本为依据。

## 20. Open product decisions

以下问题在实现前通过小规模实验决定，不在本 PRD 中伪装成既定生产能力：

1. 纯 BM25 是否足以达到 MVP Recall@3；若不足，混合检索带来的净收益是多少？
2. 版本兼容关系采用范围表达式还是显式 allow-list，哪种更易审计？
3. 内容冲突检测在 MVP 中采用规则比对还是离线 LLM 辅助，如何避免自动误判成为发布硬门禁？
4. 回答评估中人工规则、字符串要点与 LLM judge 的权重如何分配？
5. 普通用户引用信息的默认展开程度如何在可信度与界面简洁之间平衡？

## 21. Current baseline versus target MVP

| Capability | Repository today | Vehicle Book MVP target |
| --- | --- | --- |
| Knowledge corpus | 1 份本地 Mock 手册 | 多虚构 OEM / 车型 / 配置 / 软件版本资料 |
| Retrieval | 单语料 BM25，top-2 | 元数据硬过滤 + 可解释排序 + 阈值 + 版本回退 |
| Metadata | 无车辆/文档 manifest | 完整车辆、文档、chunk、生命周期 schema |
| Citations | Tool 返回原始章节 | 用户可见章节级引用与适用范围 |
| Governance | 无 | 校验、冲突、快照、diff、发布与回滚演示 |
| Evaluation | 5 条 live Agent case + pytest | 检索/回答/安全/回归分层 Eval 与切片门禁 |
| UI | Cockpit chat + Mock state | 车书问答 + 车辆选择 + 引用/调试 + 治理摘要 |
| Safety | 参数校验、移动中禁开门 | 保留现有规则，并增加高风险知识回答策略 |
| Integrations | 兼容模型 API；无真实车辆 | 仍为本地模拟，不新增生产 OEM/车辆集成 |

该对照表是项目叙事的边界：左列是已实现事实，右列是本 PRD 的目标，不应在目标实现和验证前写成当前能力。
