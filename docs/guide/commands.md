# RailForge 命令手册

## 主工作流

推荐优先使用这 5 个阶段命令：

| 命令 | 说明 |
|------|------|
| `/rf:spec-init` | 初始化 OpenSpec 与 RailForge runtime，返回 READY/DEGRADED/BLOCKED |
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
- `rf-status`
- `rf-resume`

## 桥接命令（人工响应）

当工作流阻塞等待人工输入时，用这些命令一步完成确认并自动继续：

| 命令 | 说明 | 何时使用 |
|------|------|---------|
| `approve-and-resume --target <spec\|backlog\|contract>` | 批准并自动恢复 | blocked_reason 为 `*_approval_required` |
| `answer-and-resume --file <answers.yaml>` | 回答澄清问题并自动恢复 | blocked_reason 为 `clarification_required` |
| `adopt-worktree --task-id <id> [--note "说明"]` | 吸收人工修复，跳到 review | blocked_reason 为 `repair_budget_exhausted` 等 |

注意：
- `approve-and-resume` 会校验当前 `blocked_reason` 是否与 `--target` 匹配，不匹配时只写入审批不自动恢复
- `adopt-worktree` 会拒绝存在越界改动（out-of-scope changes）的工作区，需先清理再采纳

## OpenSpec 生命周期桥接

当 RailForge 主线需要切回 OpenSpec 生命周期动作时：

- `rf-openspec-apply` 或 `/rf:openspec-apply` -> `openspec-apply-change`
- `rf-openspec-archive` 或 `/rf:openspec-archive` -> `openspec-archive-change`

## 低层协议命令

以下命令主要用于调试和高级恢复，**需要显式传 `--workspace`**：

| 命令 | 用途 |
|------|------|
| `prepare-execution` | 生成 Hosted Codex 当前 task 的执行上下文 |
| `record-execution` | 将 Hosted Codex 执行结果回写给 Python 状态机 |
| `resume` | 手动恢复 BLOCKED 工作流 |
| `answer` | 通过 YAML 文件提交答案（不自动恢复）|
| `approve` | 手动写入审批（不自动恢复）|
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

## 最终闸门

- backlog 清空后，RailForge 会生成 `docs/quality/active/final_review.json`
- 该工件汇总所有 task 级 QA 结果，并作为 change 完成前的最终审查闸门
- 只有 final review 通过后，才建议进入 `rf-openspec-archive`

## Runtime 约定

- `.railforge/runtime/` 只保存运行态工件，不承载长期 product / planning / quality 真源
- canonical runtime 路径采用 run-first、semantic-rooted 布局
- 旧 `.railforge/execution/*`、`runtime/execution/tasks/*` 与 runtime 根 hosted execution 文件只做读取兼容，不再写入

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

## 安装位置

- 默认用户级安装根是 `~/.codex`
- RailForge 二进制目标目录是 `~/.codex/bin/`
- 安装后实际可执行文件名是 `~/.codex/bin/railforge` 和 `~/.codex/bin/railforge-codeagent`
- GitHub Release 发布的原始资产名是 `railforge-<platform>-<arch>` 与 `railforge-codeagent-<platform>-<arch>`
- RailForge skills 安装到 `~/.codex/skills/railforge/`
- RailForge 用户级配置安装到 `~/.codex/.railforge/`
- `~/.codex/AGENTS.md` 只会追加 RailForge 标记块
- `~/.claude/.mcp.json` 与 `~/.gemini/settings.json` 只同步 RailForge 管理的 MCP 条目
- 若传入 `--target /some/base`，实际安装位置是 `/some/base/.codex/`
- 卸载时只移除 RailForge 自己的命名空间目录和共享文件中的标记块/镜像条目
