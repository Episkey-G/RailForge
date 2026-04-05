# RailForge 常见问题

## 1. `codeagent-wrapper: command not found`

RailForge 当前默认不依赖外部 `codeagent-wrapper` 作为主路径。

- Codex 主写作走 `hosted_codex`
- `railforge.codeagent` 负责 `Claude / Gemini` 和 `Codex fallback`

如果你仍然看到类似报错，通常说明：

- 你在使用旧模板
- 或者某条 fallback 路径还残留外部 wrapper 调用

优先检查：

- `rf-spec-impl`
- `/rf:spec-impl`
- `npx railforge-workflow doctor`

## 2. 如何让 codeagent 无需同意即可运行？

RailForge 不建议通过关闭所有保护来换取速度。

推荐方式：

- 让 Hosted Codex 作为默认 lead writer
- 用 `prepare-execution / record-execution` 驱动主循环
- 让 `Claude / Gemini` 保持在外部 runner 边界内

如果需要检查当前环境能力，先运行：

```bash
npx railforge-workflow doctor
```

## 3. Codex 任务卡住？

先区分是哪一层卡住：

- Hosted Codex 主会话卡住
- 还是 `codex exec` fallback 卡住

建议检查：

- `python -m railforge status --workspace <workspace>`
- `python -m railforge prepare-execution --workspace <workspace> --profile real`

如果是 fallback 路径，先确认：

- `codex` CLI 可用
- `model_reasoning_effort` 未被写成不支持的值

## 4. Claude Code 任务超时？

先看是：

- `Claude` review/evaluator 超时
- 还是安装器/CLI 自身阻塞

建议：

- 先跑 `npx railforge-workflow doctor`
- 再用 `python -m railforge.codeagent probe --backend claude --workspace <workspace>` 检查真实可用性

如果 `spec-review` 卡住，先确认当前 task 工件和 review 输入是否完整。

## 5. OpenSpec CLI 装不上？

RailForge 当前会初始化 `openspec/` 目录，但并不强依赖你必须全局手工安装旧的外部 OPSX 命令后才能开始主线。

先做这几步：

1. `rf-spec-init` 或 `/rf:spec-init`
2. 检查：
   - `openspec/`
   - `docs/product-specs/active/`
   - `docs/exec-plans/active/`
   - `.railforge/runtime/`
3. 如果你需要对齐外部 OpenSpec CLI，再单独检查 `openspec --version`

## 6. 什么时候应该直接用 Python 命令？

默认不要。

只有以下情况才建议直接用：

- 调试 `prepare-execution / record-execution`
- 手动 `resume`
- 查看底层 `status`
- 排查 `spec-review` 的底层结果

日常主线应该始终优先：

- `rf-spec-init`
- `rf-spec-research`
- `rf-spec-plan`
- `rf-spec-impl`
- `rf-spec-review`
