# RailForge 工作约定

- 默认使用简体中文沟通。
- 本仓库的规范化工作流以 Codex CLI 优先。
- 涉及规范研究、计划、执行、复盘、恢复、状态查询时，优先使用对应 skill 入口：
  - `rf-spec-research`
  - `rf-spec-plan`
  - `rf-execute`
  - `rf-review`
  - `rf-resume`
  - `rf-status`
- `rf-execute` 例外：它需要通过 `prepare-execution / record-execution` 与 Python 状态机协作，并在当前 hosted Codex 会话中完成主写作。
- 默认 lead writer 路径是 `hosted_codex`，`railforge.codeagent` 中的 Codex 路径只作为 fallback/headless runner。
- `spec-research` 阶段必须整理 HITL 问题、范围边界和未决假设；这些问题没有澄清之前，不进入 `execute`。
- 只修改被明确授权的文件，避免回滚他人工作。
