# Evaluation Dashboard

启动 `python -m cockpit_agent.ui` 后，打开 **Evaluation Dashboard** Tab 可只读浏览本地评测产物。页面按 Release Decision、Hard/Soft Gate、Retrieval Metrics、Answer Metrics、Category/Slice Metrics、Baseline Comparison 和失败 Case ID 的顺序展示。

数据仅来自既有的 `outputs/eval/retrieval_summary.json`、`outputs/eval/answer_summary.json` 和 `outputs/release_gate/release_gate_summary.json`。页面不会重新计算分数、运行评测、调用模型或网络，也不会写入报告。报告没有 `generated_at` 时明确显示“报告未提供生成时间”。

缺失的报告显示 `NOT_RUN` 与“未运行/报告缺失”。Baseline 比较完全采用 Release Gate 内 `candidate_vs_baseline` 的状态、原因和证据路径：manifest 缺失为 `MISSING`，上下文不兼容为 `NOT_COMPARABLE`，可比较的既有结果为 `AVAILABLE`。`PASS`、`FAIL`、`BLOCKED`、`REVIEW`、`NOT_RUN` 与 `NOT_COMPARABLE` 会保留原有含义，不互相折叠。

页面不会显示 `.env`、API Key、完整 Prompt、原始回答或其他未列入 View Model 的报告字段。
