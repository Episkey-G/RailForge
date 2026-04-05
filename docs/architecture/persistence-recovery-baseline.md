# RailForge 持久化与恢复设计基线

本文档基于 `railforge_cf_blueprint.md` 与 harness-engineering 的核心原则整理 RailForge 的持久化、恢复和 system of record 设计，并记录 3.x 持久化恢复任务落地后的当前实现。

## 设计原则

1. `railforge_cf_blueprint.md` 已明确：文件 + git 为业务真源，checkpoint 只是恢复辅助层。
2. harness-engineering 强调 repository knowledge is the system of record，也就是 system of record 必须落在仓库可见、可版本化、可重建的工件上。
3. RailForge 当前采用双层真相：
   - OpenSpec 保存 change proposal / design / tasks / spec
   - `.railforge/runtime/` 保存 runtime state、approvals、execution requests/results、reviews、proposals、notes、checkpoints 与 traces

## 当前分层

| 层级 | 目标职责 | 当前实现现状 | 备注 |
| --- | --- | --- | --- |
| 版本化文件层 | 承载可审计、可恢复的规范与运行工件 | `openspec/` 与 `.railforge/` 已被初始化、读取和写回 | 当前最接近 system of record |
| git 层 | 记录业务真相的版本历史，并在恢复或提交时提供额外锚点 | `DryRunGitAdapter.inspect_workspace()` 会把 `HEAD/branch/status/dirty` 纳入 checkpoint 与恢复裁决 | “文件 + git 为业务真源”已被固化到运行时 |
| checkpoint 层 | 在状态迁移后落盘快照，加速恢复，保留 thread/checkpoint 指针 | `FileCheckpointStore` 现在会保存 `run_state/resume/backlog/current_task/langgraph/git/truth_layer`；`LangGraph` 仍是 checkpoint layer，不是业务真源 | 不能替代版本化工件 |
| 运行态桥接层 | 给 Hosted Codex 和外部 specialist/evaluator 提供握手载荷 | `prepare-execution / record-execution` 已工作 | 与恢复关系紧密，但不定义业务真相 |

## 当前已落地的持久化能力

### 1. `.railforge/` 已经是运行时主记录面

`WorkspaceLayout` 会确保以下目录存在：

- `.railforge/runtime`
- `docs/product-specs/active`
- `docs/exec-plans/active`
- `docs/quality/active`
- `.railforge/runtime/runs`
- `.railforge/runtime/checkpoints`
- `.railforge/runtime/approvals`
- `.railforge/runtime/execution_requests`
- `.railforge/runtime/execution_results`
- `.railforge/runtime/traces`
- `.railforge/runtime/reviews`
- `.railforge/runtime/proposals`
- `.railforge/runtime/failure_signatures`
- `.railforge/runtime/notes`

对应验证见 `tests/unit/test_truth_layer.py`。

当前 canonical runtime 拓扑遵循两条规则：

1. 语义根决定“工件是什么”
2. `run_id` 决定“它属于哪次运行”，`task_id` 只在任务级工件里出现

### 2. 状态迁移后会写 checkpoint

`RailForgeHarness._snapshot()` 当前会在每次关键状态迁移后：

1. 读取当前 backlog 与 current task
2. 向 `LangGraph` bridge 记录 `thread_id` 和 `checkpoint_ref`
3. 采集当前 git 状态，并通过 `FileCheckpointStore.save()` 落盘 checkpoint JSON
4. 把 checkpoint 索引和 ref 回写到 `run_state.json`

这说明 checkpoint layer 已经存在，但它是附属层，不是 system of record。

### 3. `BLOCKED` 已具备可恢复语义

- `resume()` 只能从 `BLOCKED` 状态继续。
- `blocked_reason` 与 `resume_from_state` 会落入 `run_state.json` 和 interrupt 工件。
- 研究阶段的澄清阻塞、spec/backlog 审批阻塞、Hosted Codex 握手阻塞和 repair loop 阻塞都已经存在。

### 4. `FAILED` 语义已进入恢复裁决

- Blueprint 已定义 `FAILED` 是不可恢复故障。
- 当前 `RuntimeRecovery` 已能在缺失 `resume_from_state`、执行态缺失 current task、或真源无法重建时把运行转为 `FAILED`。
- 对应测试已覆盖 `BLOCKED`、`FAILED` 和 checkpoint 分歧裁决。

## 当前恢复流程

现在的恢复流程遵循“先重建业务真相，再恢复 checkpoint 指针”的分层规则。

### 已实现部分

1. `RuntimeRecovery` 先从 `.railforge/runtime/current_run.json`、`.railforge/runtime/runs/<run_id>/run_state.json`、backlog 文件、task 工件和审批文件重建业务真相。
2. 当 `run_state.current_task_id` 缺失时，恢复层会优先用 backlog 的 `current_task` 或唯一 `in_progress` task 回填。
3. 当 task 文件缺失但 backlog 仍保留任务定义时，恢复层会从 backlog 重新生成 task 工件。
4. 恢复层会对比最新 checkpoint 与文件真相；若状态或 current task 不一致，则标记 `checkpoint_mismatch`，并丢弃过期 checkpoint 引用。
5. 只有在 checkpoint 与文件真相一致时，才复用 `thread_id` / `checkpoint_ref` 作为恢复辅助信息。
6. `resume()`、`execute_current_task()`、`prepare_execution_payload()` 与 `record_execution_result()` 都已接入这套分层恢复逻辑。

### LangGraph 集成现状

- `langgraph_bridge.py` 现在会把 latest ref 和历史 ref 以文件形式落到 `.railforge/runtime/langgraph/`，从而提供可恢复、可跨进程复用的 checkpoint integration。
- 如果环境里存在 LangGraph 依赖，bridge 会继续调用图运行并记录真实 `checkpoint_id`；若没有，则退回合成 ref，但仍会持久化到文件层。
- 这意味着 LangGraph 已经不再只是完全内存内的占位层，但它依旧只是 checkpoint layer，而不是新的 system of record。

## Legacy 兼容边界

- loader 可以为旧 `.railforge/execution/*`、`runtime/execution/tasks/*`、runtime 根 hosted execution 文件提供只读 fallback
- writer 只允许写 canonical run-first 路径
- 恢复逻辑优先使用新路径，只有在新路径缺失时才读 legacy 工件
- 兼容层存在的目的只是迁移与恢复，不是继续维持旧 ownership

## BLOCKED / FAILED 基线定义

### BLOCKED

- 语义：可恢复暂停
- 当前已覆盖场景：
  - 澄清问题未回答
  - spec/backlog 审批未完成
  - Hosted Codex 执行结果待回写
  - repair budget 耗尽或 failure signature 重复
- 当前恢复方式：补充人工输入后调用 `resume`

### FAILED

- 语义：不可恢复故障
- Blueprint 要求：当工件、git、checkpoint 无法重建一致业务真相时进入 FAILED
- 当前现状：恢复层已把 `blocked_without_resume`、`current_task_missing` 等场景收敛为 `FAILED`，并保留 `recovery_failed` 诊断语义

## 当前结论

RailForge 已经把“文件 + git 为业务真源、checkpoint layer 附属、BLOCKED 可恢复、FAILED 不可恢复”这套规则落到了代码与测试里：

1. git 状态已经进入 checkpoint 和恢复裁决，但当前仍以只读快照为主，没有做更深的 git 一致性修复动作。
2. `LangGraph` 已具备文件化 ref 恢复能力，但未来仍可替换为更强的 durable checkpointer backend。
3. 分层恢复入口已经接到 Hosted Codex 往返、BLOCKED 恢复和 task 续跑路径上。
4. `BLOCKED`、`FAILED` 和 checkpoint 分歧已经有对应测试闭环。

因此，当前基线可以被描述为：RailForge 已完成 blueprint 要求的 artifact-first 分层恢复主路径，并把 LangGraph 明确压在 checkpoint layer 的职责边界内。
