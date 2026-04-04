# RailForge 发布说明

## 版本

- RailForge Python core: `0.1.0`
- `railforge-workflow` installer: `0.1.1`

## 本次发布内容

### 1. Spec 主工作流

新增并收敛了以下主工作流命令：

- `spec-init`
- `spec-research`
- `spec-plan`
- `spec-impl`
- `spec-review`

同时提供对应的主入口：

- `rf-spec-init`
- `rf-spec-research`
- `rf-spec-plan`
- `rf-spec-impl`
- `rf-spec-review`

以及安装器写入的 slash command 模板：

- `/rf:spec-init`
- `/rf:spec-research`
- `/rf:spec-plan`
- `/rf:spec-impl`
- `/rf:spec-review`
- `/rf:openspec-apply`
- `/rf:openspec-archive`

### 2. Hosted Codex 默认执行路径

- `lead_writer` 默认切换为 `hosted_codex`
- Python 状态机通过 `prepare-execution / record-execution` 与当前 Codex 主会话协作
- `Claude / Gemini` 继续由 `railforge.codeagent` 驱动

### 3. OpenSpec 与 `.railforge` 双真源

- OpenSpec 负责 proposal / design / tasks / spec
- `.railforge/` 负责 runtime state / backlog / approvals / qa / checkpoints
- `spec-review` 会把主动双模型审查回写到 task 级 `qa_report.json`
- backlog 完成后会生成 change 级 `.railforge/execution/final_review.json`

### 4. 安装器

新增 `railforge-workflow` 安装器骨架，支持：

- `menu`
- `init`
- `update`
- `config-mcp`
- `probe-mcp`
- `config-model`
- `doctor`
- `help`
- `uninstall`

### 5. MCP 对齐

安装器的 MCP 分组和目标集合已经与 CCG 对齐：

- 代码检索：`ace-tool`、`ace-tool-rs`、`fast-context`、`ContextWeaver`
- 联网搜索：`grok-search`
- 辅助工具：`Context7`、`Playwright`、`DeepWiki`、`Exa`

## 测试结果

- `python -m pytest -q`: `119 passed`
- `railforge.codeagent probe --backend codex|claude|gemini`: 已验证
- installer `doctor/update/config-model/config-mcp/probe-mcp/help/uninstall`: 已验证

## 当前边界

- `railforge-workflow` 已完成 `0.1.1` 发布前验证，等待或已执行 npm 发布
- 安装器已经可用，但与 CCG 的完整菜单深度和跨宿主自动化相比仍有继续迭代空间
