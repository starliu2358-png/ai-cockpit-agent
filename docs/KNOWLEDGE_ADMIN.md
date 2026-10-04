# Knowledge Admin（只读）

`python -m cockpit_agent.ui` 启动后，打开 **Knowledge Admin（只读）** Tab 可查看本地知识治理演示。

页面安全展示 Registry 中的 Vehicle Profile 标识、OEM、车型、配置、软件版本、发布状态，以及适用文档的 ID、标题、类型、版本、状态、语言和相对 `source_path`。文档按 Profile 隔离显示；预发布 Profile 仅用于管理浏览，不会改变检索的默认发布过滤规则。

Release Gate 区域只读取已有的 `outputs/release_gate/release_gate_summary.json`，展示总体 `PASS`、`FAIL` 或 `BLOCKED` 状态和可折叠的有限门禁明细。打开页面不会重新运行门禁，也不会调用模型。若摘要不存在，状态明确显示为 `NOT_RUN` 和“未运行”。损坏或格式无效的报告显示为 `BLOCKED`。

这不是生产 CMS：没有上传、编辑、删除、发布、权限或审批能力，不更改 Registry、文档状态或 Release Gate 报告。页面不会展示 `.env`、API Key、文档正文或完整 Prompt。

本项目为本地模拟，不控制真实车辆。
