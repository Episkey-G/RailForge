# RailForge

RailForge 是一个以 Spec 驱动的代理编排系统，围绕 Codex CLI 构建，强调流程纪律和可控闭环。

## 快速开始

### 安装

```bash
npx railforge-workflow
```

安装器会自动完成：
- 下载平台二进制到 `~/.codex/bin/railforge`
- 安装 workflow skills 到 `~/.codex/skills/railforge/`
- 配置模型路由和 MCP
- 写入用户级配置到 `~/.codex/.railforge/`

### 环境检查

```bash
~/.codex/bin/railforge spec-init
```

返回 `READY` / `DEGRADED` / `BLOCKED` 三级状态，明确告知哪些组件就绪、哪些缺失。

## 操作流

### 主工作流（6 个阶段命令）

用户只需要记住这些命令，不需要接触底层协议：

| 阶段 | Skill 入口 | Slash 命令 | 说明 |
|------|-----------|-----------|------|
| 初始化 | `rf-spec-init` | `/rf:spec-init` | 初始化 OpenSpec + runtime + 环境检查 |
| 研究 | `rf-spec-research` | `/rf:spec-research` | 需求 → 约束集 + HITL 问题 + proposal |
| 规划 | `rf-spec-plan` | `/rf:spec-plan` | 约束 → 零决策可执行计划 |
| 实现 | `rf-spec-impl` | `/rf:spec-impl` | 按计划执行，默认走 Hosted Codex |
| 审查 | `rf-spec-review` | `/rf:spec-review` | 双模型规范审查，可独立运行 |
| 状态 | `rf-status` | - | 查看当前状态 |

### 桥接命令（人工响应）

当工作流需要人工输入时，使用以下桥接命令一步完成确认并继续：

| 命令 | 说明 |
|------|------|
| `approve-and-resume --target <spec\|backlog\|contract>` | 批准并自动继续 |
| `answer-and-resume --file <answers.yaml>` | 回答澄清问题并自动继续 |
| `adopt-worktree --task-id <id>` | 人工修复后吸收变更，跳到 review |

### OpenSpec 生命周期

| 入口 | 说明 |
|------|------|
| `rf-openspec-apply` | 开始实施 OpenSpec change |
| `rf-openspec-archive` | 归档已完成的 change |

### 低层协议命令（仅调试用）

以下命令需要显式传 `--workspace`，主要用于调试和高级恢复：

| 命令 | 用途 |
|------|------|
| `prepare-execution` | 生成 Hosted Codex 的执行上下文 |
| `record-execution` | 将 Hosted Codex 执行结果回写给状态机 |
| `resume` | 手动恢复 BLOCKED 工作流 |
| `answer` | 通过 YAML 文件提交答案 |

## Workspace 自动推断

前门命令（`spec-*`、`status`、`approve`、`resume` 等）的 `--workspace` 参数是可选的：
1. 自动向上查找 `.railforge/` 目录标记
2. 自动向上查找 `.git/` 根目录
3. 找不到时报错：`No RailForge workspace detected. Run rf-spec-init or pass --workspace.`

低层协议命令仍然要求显式 `--workspace`。

## 状态机

```
INTAKE → SPEC_EXPANSION → BACKLOG_BUILD → TASK_SELECTED → CONTRACT_NEGOTIATION
→ IMPLEMENTING → STATIC_REVIEW → RUNTIME_QA → REPAIRING → READY_TO_COMMIT
→ COMMITTED → NEXT_TASK → DONE
```

关键行为：
- **审批门**：spec / backlog / contract 各有独立审批点，未批准前不继续
- **repair 预算**：每个 task 有 repair 上限，耗尽后进入 `manual_repair_required`
- **恢复目标**：repair 耗尽后 resume 跳到 `STATIC_REVIEW`，不会重放 lead writer
- **repo reality audit**：在 `CONTRACT_NEGOTIATION` 阶段校验 allowed_paths 在工作区实际存在
- **commit gate**：lint + build + tests + acceptance criteria 全通过才允许 commit

## 目录结构

```
railforge/              Python 运行时核心
  orchestrator/         状态机和编排逻辑
  evaluator/            静态/运行时/结果评估器
  execution/            Codex writer、backend/frontend specialist
  guardrails/           repair budget、blocker detector
  application/          命令服务层
  core/                 数据模型、状态枚举、FSM
  adapters/             mock 和 real adapter
  codeagent/            内置多后端 runner (Claude/Gemini/Codex fallback)
.agents/skills/         Codex CLI workflow skill 入口
.codex/                 项目级 Codex 配置、hooks、角色定义
docs/
  architecture/         架构文档
  guide/                使用指南 (commands.md, faq.md, release-notes.md)
  product-specs/active/ 长期产品规格真源
  exec-plans/active/    长期执行计划真源
  quality/active/       质量闸门输出
installer/              npm 安装器 (railforge-workflow)
scripts/                构建脚本
tests/                  单元测试和集成测试
```

## Runtime 拓扑

`.railforge/runtime/` 采用 run-first、semantic-rooted 布局：

```
.railforge/runtime/
  runs/<run_id>/
    run_state.json
    tasks/<task_id>/
    approvals/
    checkpoints/
    execution_requests/
    execution_results/
    traces/
    reviews/
    proposals/
    notes/
  observability/
    ledgers/
    context/
```

## 更多文档

| 文件 | 说明 |
|------|------|
| [CHANGELOG.md](CHANGELOG.md) | 版本更新日志 |
| [docs/guide/commands.md](docs/guide/commands.md) | 命令完整手册 |
| [docs/guide/faq.md](docs/guide/faq.md) | 常见问题 |
| [docs/guide/build-and-publish.md](docs/guide/build-and-publish.md) | 打包和发布指南 |
| [docs/architecture/railforge-architecture.md](docs/architecture/railforge-architecture.md) | 架构说明 |
