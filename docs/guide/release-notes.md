# RailForge 发布说明

## 版本

- RailForge Python core: `0.1.0`
- `railforge-workflow` installer: `0.1.5`

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

此外，`0.1.5` 继续强化了 Codex-first 命名空间安装模型：

- 默认安装根从 `target` 根目录改为 `target/.codex`
- 主工作流 skills 安装到 `skills/railforge/`
- RailForge 用户级配置安装到 `.codex/.railforge/`
- 卸载只删除 RailForge 自己安装的命名空间目录和标记块，不再删整棵 `.codex`
- `~/.codex/AGENTS.md`、`~/.codex/config.toml`、`~/.claude/.mcp.json`、`~/.gemini/settings.json` 改为增量写入与增量回滚
- 默认 `npx railforge-workflow` 安装根改为用户主目录下的 `~/.codex`

同时，`0.1.5` 保持了对齐后的安装器主菜单模板：

- 主菜单重新回到接近 CCG 的静态模板布局
- 保留方向键交互，不再退回“输入编号或字母”
- 去掉了重复的 `? ? RailForge 主菜单` 提示
- 菜单文案、状态行和分组结构与 CCG 风格进一步对齐

### 5. MCP 对齐

安装器的 MCP 分组和目标集合已经与 CCG 对齐：

- 代码检索：`ace-tool`、`ace-tool-rs`、`fast-context`、`ContextWeaver`
- 联网搜索：`grok-search`
- 辅助工具：`Context7`、`Playwright`、`DeepWiki`、`Exa`

## 测试结果

- `python -m pytest -q`: `122 passed`
- `railforge.codeagent probe --backend codex|claude|gemini`: 已验证
- installer `doctor/update/config-model/config-mcp/probe-mcp/help/uninstall`: 已验证
- 本地源码目录 `npx railforge-workflow`：已验证显示 `↑↓ navigate • ⏎ select`
- 本地源码目录 `npx railforge-workflow`：已验证只显示一份 CCG 风格主菜单模板
- 最新整仓验证：`120 passed`

## 当前边界

- `railforge-workflow` 已完成 `0.1.5` 发布前验证，等待或已执行 npm 发布
- 安装器已经可用，但与 CCG 的完整菜单深度和跨宿主自动化相比仍有继续迭代空间
