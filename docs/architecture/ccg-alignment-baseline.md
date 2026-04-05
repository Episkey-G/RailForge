# RailForge 对齐 `ccg-workflow` 阶段 1 审计基线

本文档用于兑现变更 `align-railforge-with-ccg-three-phase-loop` 的第 1 组任务，记录阶段 1 审计时 RailForge 与 `ccg-workflow` 的对齐面、已验证能力和明确缺口。
它是基线快照，不负责实时覆盖后续任务对这些缺口的修复进展。

> 注：本文档保留的是阶段 1 审计快照。当前主线实现已经进一步收敛为 Codex CLI front door + run-first semantic-rooted runtime；若与本文快照冲突，应以最新 `README.md`、`AGENTS.md` 和 `docs/architecture/*` 的现状说明为准。

## 对齐矩阵

| 维度 | `ccg-workflow` 期望 | RailForge 当前现状 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
| 安装器 | 提供接近 CCG 的菜单式初始化、MCP 配置、模型路由和 doctor 体验 | `installer/src/cli.mjs`、`installer/src/menu.mjs`、`installer/src/commands.mjs` 已提供 `init/update/config-mcp/config-model/doctor/help/uninstall` 骨架；测试覆盖菜单文案与命令模板 richness | 部分对齐 | `installer/src/menu.mjs`、`installer/src/commands.mjs`、`tests/integration/test_installer_menu_parity.py` |
| skills | 用户可沿主工作流持续推进，不必手拼低层命令 | 仓库内已有 `rf-spec-init / rf-spec-research / rf-spec-plan / rf-spec-impl / rf-spec-review / rf-resume / rf-status`，同时保留 `rf-execute / rf-review` 旧入口；安装器模板目前只生成 `rf-spec-*` 主线 | 部分对齐 | `.agents/skills/`、`installer/src/commands.mjs`、`tests/integration/test_skill_entrypoints.py` |
| 工作流入口 | 主线以 `spec-init / spec-research / spec-plan / spec-impl / spec-review` 为核心，并桥接恢复与状态查询 | `railforge/cli.py` 与 `railforge/commands.py` 已暴露这五个入口；README 与 guide 也主推 `rf-spec-*`/`/rf:spec-*`；但 `AGENTS.md` 仍以 `rf-execute / rf-review` 叙述旧入口 | 部分对齐 | `railforge/cli.py`、`railforge/commands.py`、`README.md`、`docs/guide/commands.md`、`AGENTS.md` |
| MCP 分组 | 代码检索、联网搜索、辅助工具三组能力与 CCG 的菜单分组和镜像同步方式一致 | `installer/src/mcp.mjs` 已定义三组菜单；`writeMcpConfig()` 和镜像写入逻辑会同步 `.codex/.gemini/.claude` 配置 | 已对齐到当前骨架 | `installer/src/mcp.mjs`、`installer/src/commands.mjs`、`tests/integration/test_installer_docs.py` |
| 运行时闭环 | 具备 research → plan → impl → review 的完整闭环，并由状态机、contract、review、repair、commit 推进 | `run_loop.py` 已覆盖 intake、spec expansion、backlog build、task selection、contract、implement、static review、runtime QA、repair、commit、next task、blocked/resume；Hosted Codex 握手已可用 | 部分对齐 | `railforge/orchestrator/run_loop.py`、`tests/integration/test_prepare_record_execution.py`、`tests/integration/test_run_loop.py` |

## 已验证的当前能力

1. 安装器骨架、MCP 分组和多宿主镜像配置已具备最小可用形态。
2. `spec-init / spec-research / spec-plan / spec-impl / spec-review` 命令都存在，且主工作流 smoke 测试可运行。
3. Hosted Codex 的 `prepare-execution / record-execution` 协议已串上状态机，能够把当前 task 和 contract 交给主写作者。
4. `.railforge/runtime/` 目录承担 runtime truth layer，包含 execution、approvals、interrupts、context packs 和 checkpoints；长期 product/planning/quality 真源转到 `docs/`。

## 已标记并验证的关键缺口（阶段 1 审计快照）

### 1. 固定 backlog 仍是占位实现

- `railforge/planner/backlog_builder.py` 目前固定生成三条任务：
  - `T-001 Backend validation`
  - `T-002 Frontend feedback`
  - `T-003 Verification coverage`
- 这三条任务的 `allowed_paths`、`verification` 和依赖关系也是硬编码的，不会根据真实需求变化。
- 回归证据：`tests/unit/test_planner.py` 已锁定这组固定模板。

### 2. OpenSpec 写入仍然是简化占位

- `handle_spec_research()` 只写入简短 proposal 快照：change、request、result state。
- `handle_spec_plan()` 目前只是把 product spec 和固定 backlog 投影成简化版的 `design.md / tasks.md / spec.md`。
- 回归证据：`tests/integration/test_spec_command_baselines.py` 已验证当前 placeholder proposal、design、tasks 和 spec 的写法。

### 3. `spec-review` 仍是被动别名

- `railforge/commands.py` 中 `handle_spec_review()` 直接返回 `handle_review(args)`。
- 这意味着 `spec-review` 现在只是读取已有 `qa_report` 或 `run_state`，并不会主动重跑独立双模型评估。
- 回归证据：`tests/integration/test_spec_command_baselines.py` 已验证 `spec-review` 与 `review` 输出完全一致。

### 4. `langgraph_bridge.py` 仍是 checkpoint 占位层

- 当前 bridge 只用 `InMemorySaver` 或生成合成的 `checkpoint_ref`。
- 它会把 `thread_id` / `checkpoint_ref` 写进 checkpoint，但没有 durable 恢复入口，也没有冲突校验逻辑。
- 回归证据：`tests/unit/test_langgraph_bridge.py` 只验证 ref 生成与持久化，不验证真实恢复。

### 5. 文档与实现仍存在不一致点

- README、`docs/guide/commands.md`、`docs/architecture/best-practices.md` 已把 `rf-spec-impl / rf-spec-review` 作为主线。
- 但仓库根 `AGENTS.md` 仍以 `rf-execute / rf-review` 描述执行与复盘入口。
- 安装器模板中的 `DEFAULT_AGENTS_MD` 与仓库现有 `AGENTS.md` 也还没有完全收敛。

## 阶段 1 审计结论

RailForge 已经具备与 `ccg-workflow` 对齐所需的主框架：安装器骨架、MCP 分组、`spec-*` 命令、Hosted Codex 协议和状态机闭环都在。
但现阶段仍然是“骨架可运行、深度未对齐”的状态，尤其是固定 backlog、简化 OpenSpec 写入、被动 `spec-review`、`langgraph_bridge.py` 占位层，以及 `AGENTS.md` 等文档/实现不一致点，都是后续任务必须继续消化的真实缺口。
