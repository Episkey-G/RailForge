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

当主工作流进入 OpenSpec 生命周期动作时，使用桥接入口：

- `rf-openspec-apply` 或 `/rf:openspec-apply`
- `rf-openspec-archive` 或 `/rf:openspec-archive`

只有在调试、恢复或排查工作流状态时，才直接使用底层 Python CLI。

## HITL 规划阶段

`spec-research` 是人机协同的规划入口，不是实现入口。
它需要把未决假设、范围边界、风险点和需要人工拍板的问题显式列出来，确认完成后再进入 `spec-plan` 和 `execute`。

## Hosted Codex

- 默认 lead writer 模式是 `hosted_codex`。
- Python 内核通过 `prepare-execution / record-execution` 与当前 Codex 主会话协作。
- `railforge.codeagent` 主要负责 `Claude / Gemini`，以及 `Codex` 的 fallback/headless 路径。
- 对普通用户来说，这些低层协议应由 `rf-spec-impl` 或 `/rf:spec-impl` 隐藏起来，不应成为主要操作入口。
- `spec-review` 会主动汇总独立双模型评估，并在全部 task 完成后写入 `docs/quality/active/final_review.json`。

## 安装

推荐入口：

```bash
npx railforge-workflow
```

安装器目标是提供与 CCG 接近的交互式初始化体验，包括：

- 在 `~/.codex/skills/railforge/` 下安装 `spec-*` 主工作流 skills
- 在 `~/.codex/.railforge/` 下安装 RailForge 用户级配置
- 把必要的 MCP 镜像同步到 `~/.claude/.mcp.json` 与 `~/.gemini/settings.json`
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
- `.codex/`：项目级 Codex 配置、hooks 和角色定义。
- `docs/product-specs/active/`、`docs/exec-plans/active/`、`docs/quality/active/`：长期知识真源。
- `.railforge/runtime/`：运行态与观测层，只保存当前或历史 run 的审批、checkpoint、execution requests/results、traces、reviews、proposals、notes 等工件。
- `tests/`：单元测试和集成 smoke 测试。

## Runtime 拓扑

RailForge 采用 run-first、semantic-rooted 的 runtime 布局：

- 语义根决定“这是什么工件”，例如 `execution_requests/`、`execution_results/`、`traces/`、`reviews/`、`proposals/`
- `run_id` 决定“它属于哪次运行”
- `task_id` 只在任务级工件中作为子维度出现
- 旧 `.railforge/execution/*`、`runtime/execution/tasks/*` 和 runtime 根 hosted execution 文件只保留 loader-only 兼容，不再新增写入

这让恢复、审计、trace replay、hosted execution writeback 都保持 run-scoped，同时把长期真源继续留在 `docs/` 与 `openspec/changes/`。

安装后用户级文件布局为：

```text
~/.codex/
├── bin/
├── skills/railforge/
├── AGENTS.md
└── .railforge/
    ├── models.yaml
    ├── policies.yaml
    ├── mcp.json
    └── installer-state.json
```

安装器会把当前平台的预编译二进制下载到：

```text
~/.codex/bin/railforge
~/.codex/bin/railforge-codeagent
```

GitHub Release 中发布的原始平台资产仍然使用带平台后缀的名字：

```text
railforge-<platform>-<arch>
railforge-codeagent-<platform>-<arch>
```

如果显式传入 `--target /some/base`，安装位置会变成：

```text
/some/base/.codex/
```

也就是说，`--target` 代表“用户级安装根的父目录”，而不是旧版那种“直接把文件铺到目标根目录”。

## 最佳实践

建议先阅读：

- `docs/architecture/best-practices.md`
- `docs/guide/commands.md`
- `docs/guide/faq.md`
- `docs/guide/release-notes.md`
- `docs/guide/npm-publish-checklist.md`
