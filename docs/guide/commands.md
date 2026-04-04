# RailForge 命令手册

## 主工作流

推荐优先使用这 5 个命令：

| 命令 | 说明 |
|------|------|
| `/rf:spec-init` | 初始化 OpenSpec 与 RailForge runtime，并检查多模型与 MCP 环境 |
| `/rf:spec-research` | 需求 → 约束集 + HITL 问题 + OpenSpec proposal |
| `/rf:spec-plan` | 约束 → 零决策可执行计划 |
| `/rf:spec-impl` | 按计划执行，默认走 Hosted Codex 主循环 |
| `/rf:spec-review` | 双模型规范审查，可独立运行 |

## Skill 入口

如果宿主优先发现 skills，也可以直接使用：

- `rf-spec-init`
- `rf-spec-research`
- `rf-spec-plan`
- `rf-spec-impl`
- `rf-spec-review`

## 低层协议命令

以下命令主要用于调试和高级恢复：

| 命令 | 用途 |
|------|------|
| `prepare-execution` | 生成 Hosted Codex 当前 task 的执行上下文 |
| `record-execution` | 将 Hosted Codex 执行结果回写给 Python 状态机 |
| `resume` | 恢复 `BLOCKED` 工作流 |
| `status` | 查看当前 run state、blocker 和 next action |
| `review` | 运行低层 review gate |

## 推荐主线

```text
/rf:spec-init
/rf:spec-research
/rf:spec-plan
/rf:spec-impl
/rf:spec-review
```

## Hosted Codex 说明

- 默认 lead writer 是 `hosted_codex`
- Python 内核通过 `prepare-execution / record-execution` 与当前 Codex 主会话协作
- `Claude / Gemini` 继续由 `railforge.codeagent` 驱动

## 安装器相关命令

```bash
npx railforge-workflow
npx railforge-workflow doctor
npx railforge-workflow config-mcp --target <dir>
npx railforge-workflow config-model --target <dir>
npx railforge-workflow init --target <dir>
npx railforge-workflow update --target <dir>
npx railforge-workflow uninstall --target <dir>
```
