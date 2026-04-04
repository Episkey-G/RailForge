# RailForge 使用最佳实践

## 1. 默认心智

RailForge 应该按下面这条主线使用：

1. `rf-spec-init` 或 `/rf:spec-init`
2. `rf-spec-research` 或 `/rf:spec-research`
3. `rf-spec-plan` 或 `/rf:spec-plan`
4. `rf-spec-impl` 或 `/rf:spec-impl`
5. `rf-spec-review` 或 `/rf:spec-review`

不要把低层命令当成主要入口。对大多数任务来说：

- 主入口是 `rf-spec-*` 或 `/rf:spec-*`
- 低层 Python 命令只是调试和恢复工具

## 2. 先初始化，再开始研究

第一次在一个仓库里使用 RailForge 时，先在 Codex CLI 中运行：

```bash
rf-spec-init
```

最佳实践：

- 确认 `openspec/` 已创建
- 确认 `.railforge/runtime/models.yaml` 和 `.railforge/runtime/policies.yaml` 已创建
- 确认 `codex / claude / gemini / jq / python / node` 都能被 `doctor` 检出

不要跳过初始化直接进入 `spec-research`。

## 3. 一切从 `spec-research` 开始

`spec-research` 的目标不是写代码，而是把需求变成：

- 约束
- 风险
- HITL 问题
- OpenSpec proposal

最佳实践：

- 一次只输入一个完整需求，不要在一句话里混多个独立子系统
- 如果任务明显能拆分，先拆 change，再做研究
- 遇到 `BLOCKED` 不要强行往后跑，先回答问题或做人工审批

不要把 `spec-research` 当成“顺手开始实现”的入口。

## 4. 在 `spec-plan` 把决策做完

`spec-plan` 的目标是生成零决策执行计划。

最佳实践：

- 进入 `spec-plan` 前先完成 `spec-research` 的关键澄清
- 把实现阶段会拍脑袋的决策前移到这里
- 审查 OpenSpec 里的 `design.md / tasks.md / spec.md`
- 审查 `.railforge/planning/backlog.yaml` 和 task contract

如果计划还存在关键歧义，不要进入 `spec-impl`。

## 5. `spec-impl` 走 Hosted Codex 主路径

当前默认 lead writer 是 `hosted_codex`。

这意味着：

- Python 内核负责状态机和工件
- 当前 Codex 主会话负责主写作
- `Claude / Gemini` 负责外部 review / evaluator

最佳实践：

1. 在 Codex CLI 中运行：

```bash
rf-spec-impl
```

2. 让 skill 或 slash command 驱动完整主循环：

- `prepare-execution`
- Hosted Codex 主写作
- `record-execution`
- review / repair loop

3. 只有在需要调试 Hosted 协议时，才手动使用：

```bash
python -m railforge prepare-execution --profile real --workspace <workspace>
python -m railforge record-execution --profile real --workspace <workspace> --file <execution-result.json>
```

最小 `execution-result.json`：

```json
{
  "task_id": "T-001",
  "summary": "完成后端校验与测试",
  "changed_files": [
    "backend/todos.py",
    "tests/test_due_date.py"
  ]
}
```

不要把 `prepare-execution / record-execution` 当成日常主入口。

## 6. 评审永远独立看待

`spec-review` 应被当成独立工具，而不是实现后的附带步骤。

最佳实践：

- 在大任务完成后单独跑一次 `spec-review`
- 在人工修改后再跑一次
- 发现问题时优先回到 `spec-impl` 的当前 task 修复，不要跳过 review

如果 review 结果不干净，不要急着归档。

## 7. 遇到 BLOCKED 的处理方式

RailForge 的 `BLOCKED` 是正常状态，不是异常退出。

最佳实践：

- 用 `status` 先看：
  - `blocked_reason`
  - `resume_from_state`
  - `current_task_id`
- 如果是审批类阻塞：
  - 用 `approve`
- 如果是 hosted 执行类阻塞：
  - 完成 Hosted Codex 执行并用 `record-execution`
- 如果是人工决策类阻塞：
  - 先补问题答案，再 `resume`

不要在不理解 `blocked_reason` 的情况下直接反复 `resume`。

## 8. 主命令与低层命令的边界

优先使用：

- `rf-spec-init` / `/rf:spec-init`
- `rf-spec-research` / `/rf:spec-research`
- `rf-spec-plan` / `/rf:spec-plan`
- `rf-spec-impl` / `/rf:spec-impl`
- `rf-spec-review` / `/rf:spec-review`

只在这些场景使用低层命令：

- `prepare-execution`
  - 需要拿 Hosted Codex 上下文时
- `record-execution`
  - 需要把 Hosted 执行结果回写时
- `resume`
  - 处理明确 blocker 时
- `status`
  - 查状态时

不要让团队成员直接记一堆低层命令，主流程应始终围绕 `rf-spec-*` 或 `/rf:spec-*`。

## 9. MCP 推荐组合

与 CCG 对齐的推荐组合：

- 代码检索：
  - `ace-tool` 或 `ace-tool-rs`
  - `fast-context`
  - `ContextWeaver`
- 联网搜索：
  - `grok-search`
- 辅助工具：
  - `Context7`
  - `Playwright`

最低建议：

- 至少一个代码检索 MCP
- `Context7`
- `Playwright`

如果要做真实 spec workflow，不要只装模型 CLI，不装 MCP。

## 10. 团队协作建议

推荐团队约定：

- 统一用 `spec-*` 主命令
- 统一保留 OpenSpec 与 `.railforge/`
- 统一在 review 通过前不归档
- 统一记录 HITL 决策，不口头跳过

如果团队里有人直接跳过 `spec-research / spec-plan` 进入实现，这套工作流很快就会退化成普通脚本集合。

## 11. 当前最稳的实际流程

在当前版本里，最稳的使用方式是：

```text
rf-spec-init
rf-spec-research
rf-spec-plan
rf-spec-impl
rf-spec-review
```

如果安装了 slash commands，则优先使用：

```text
/rf:spec-init
/rf:spec-research
/rf:spec-plan
/rf:spec-impl
/rf:spec-review
```

只有在以下场景才直接敲 Python：

- 调试 `prepare-execution / record-execution`
- 手动恢复 `resume`
- 查看底层 `status`

如果你在日常工作里坚持这条主线，RailForge 的价值才会体现出来。
