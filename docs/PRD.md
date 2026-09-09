# AI Cockpit Agent — MVP PRD

## 1. 目标
在 1 周内完成一个可演示、可开源、可写进简历的 AI 座舱 Agent MVP，重点证明以下能力：

- LLM 自然语言意图理解
- Tool Calling 执行座舱动作
- 本地车辆手册 RAG
- 安全 Guardrail
- 基础 Eval / Test
- GitHub 工程化交付

## 2. 非目标

- 不接真实车辆 CAN / SOME-IP / DDS
- 不训练或微调模型
- 不做 ASR/TTS
- 不做复杂多 Agent
- 不做高保真座舱 UI
- 不追求生产级安全认证

## 3. MVP 用户故事

1. 用户说“我有点冷，把空调调到 23 度”，Agent 调用工具完成设置。
2. 用户说“把主驾座椅加热调到 2 档”，Agent 调用工具完成设置。
3. 用户问“胎压报警是什么意思”，Agent 检索本地手册并回答。
4. 用户说“导航到北京南站”，Agent 更新 Mock 导航目的地。
5. 行驶状态下用户要求开门，系统必须拒绝并解释原因。

## 4. 验收标准

- [ ] Gradio 页面可运行
- [ ] 至少 6 个 Function Tools
- [ ] 至少 1 个 RAG Tool
- [ ] 至少 1 个 hard safety rule
- [ ] pytest 全绿
- [ ] README 有架构、运行方式、Demo 用例
- [ ] GitHub 有至少 3 个有意义 commit
- [ ] 录制 60~90 秒演示视频/GIF
