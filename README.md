# RailForge

RailForge 是一个以 Spec 驱动的代理编排项目，工作流优先围绕 Codex CLI 展开。

## 项目目标

项目把一次变更拆成明确的阶段：先做 `spec-research`，再做 `spec-plan`，然后才是 `execute`、`review`、`resume` 和 `status`。
这样可以把人类确认点、实现步骤和验证动作分开，减少把假设直接写进代码的风险。

## 推荐操作流

默认不要手动记一串 `python -m railforge ...` 命令。推荐在 Codex CLI 中直接使用主工作流入口：

1. `rf-spec-init` 或 `/rf:spec-init`
2. `rf-spec-research` 或 `/rf:spec-research`
3. `rf-spec-plan` 或 `/rf:spec-plan`
4. `rf-spec-impl` 或 `/rf:spec-impl`
5. `rf-spec-review` 或 `/rf:spec-review`

只有在调试、恢复或排查工作流状态时，才直接使用底层 Python CLI。

## HITL 规划阶段

`spec-research` 是人机协同的规划入口，不是实现入口。
它需要把未决假设、范围边界、风险点和需要人工拍板的问题显式列出来，确认完成后再进入 `spec-plan` 和 `execute`。

## Hosted Codex

- 默认 lead writer 模式是 `hosted_codex`。
- Python 内核通过 `prepare-execution / record-execution` 与当前 Codex 主会话协作。
- `railforge.codeagent` 主要负责 `Claude / Gemini`，以及 `Codex` 的 fallback/headless 路径。
- 对普通用户来说，这些低层协议应由 `rf-spec-impl` 或 `/rf:spec-impl` 隐藏起来，不应成为主要操作入口。

## 安装

推荐入口：

```bash
npx railforge-workflow
```

安装器目标是提供与 CCG 接近的交互式初始化体验，包括：

- 初始化 OpenSpec 与 `.railforge`
- 安装 `spec-*` 主工作流命令
- 配置模型路由
- 配置 MCP

### 配置 MCP

RailForge 安装器的 MCP 能力与 CCG 保持一致，安装菜单按以下分组提供：

- 代码检索：`ace-tool`、`ace-tool-rs`、`fast-context`、`ContextWeaver`
- 联网搜索：`grok-search`
- 辅助工具：`Context7`、`Playwright`、`DeepWiki`、`Exa`

## 目录说明

- `railforge/`：运行时代码。
- `railforge/codeagent/`：RailForge 内置多后端 runner，直接对接 `claude`、`gemini`，并保留 `codex` 的 fallback/headless 路径。
- `.agents/skills/`：Codex CLI 优先的 workflow skill 入口。
- `docs/architecture/`：长期有效的架构、仓库结构和测试矩阵说明。
- `.railforge/`：运行时真源，保存 spec、backlog、任务工件、checkpoint 和审批记录。
- `tests/`：单元测试和集成 smoke 测试。

## 最佳实践

建议先阅读：

- `docs/architecture/best-practices.md`
- `docs/guide/commands.md`
- `docs/guide/faq.md`
- `docs/guide/release-notes.md`
- `docs/guide/npm-publish-checklist.md`
