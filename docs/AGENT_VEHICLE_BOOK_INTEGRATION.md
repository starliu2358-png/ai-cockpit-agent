# Agent Vehicle Book Integration

Cockpit Agent 通过 `vehicle_knowledge(question)` 访问 Vehicle Book。该工具是按请求动态注册的薄适配层：调用现有 `VehicleBookService`，返回答案、精简 Citation、`is_fallback` 与 `fallback_reason`，不实现检索、生成、评测或门禁逻辑。模型的 Tool schema 只包含问题；UI 选择的 Profile 与预发布权限由闭包在程序层绑定，模型不能替换车辆 ID 或自行开启预发布访问。

Cockpit Demo 的 Vehicle Profile 选择器默认不选择任何车型。选择器和“显式允许预发布 Profile 查询”开关会传入 Agent 指令；Tool 仍要求明确 `vehicle_id`。缺失或未知 ID 不会回退到其他车型。`alpha_aster_x1_max_v2` 是 pre-release，只有明确开启该开关后才允许服务读取。

`search_vehicle_manual` 仍保留为 legacy 通用手册检索，例如没有车辆上下文时的泛化告警说明；车型、版本或配置相关问题必须使用 `vehicle_knowledge`。控制请求继续使用 HVAC、座椅、导航等既有 Tool，开门仍由速度 Guardrail 决定。知识工具从不修改 Mock Vehicle State。

Agent 应将 Citation 简洁呈现为来源文档、章节、适用 Profile/文档版本。若资料不足，保留工具返回的 Fallback 文案和 `fallback_reason`，不改写为确定事实。本项目仅为本地模拟，不连接或控制真实车辆。
