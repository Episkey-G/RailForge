# RailForge Testing Matrix

## Smoke Coverage

| Test | What it checks |
| --- | --- |
| `tests/integration/test_alignment_baseline_docs.py` | 第 1 组基线文档已经落地，明确记录 CCG 对齐矩阵、持久化/恢复基线与已验证缺口。 |
| `tests/integration/test_spec_command_baselines.py` | `spec-research / spec-plan / spec-review` 的 research/plan 富化行为、规划期 contract 落盘和 unresolved question 阻塞语义有稳定回归覆盖。 |
| `tests/integration/test_skill_entrypoints.py` | Skill directories exist, `run.sh` files are executable, README points to the formal docs path, and the formal repository no longer keeps `docs/superpowers/`. |
| `tests/integration/test_module_entry.py` | The `python -m railforge` module entrypoint still works for the runtime CLI. |
| `tests/integration/test_codeagent_cli.py` | `python -m railforge.codeagent` 的 `run / probe` 入口能输出稳定 JSON。 |
| `tests/integration/test_prepare_record_execution.py` | `prepare-execution / record-execution` 的 hosted Codex 协议能生成上下文并回写执行结果。 |
| `tests/integration/test_spec_review_flow.py` | 从 `spec-init` 到 `spec-review` 的 hosted smoke 流程可跨进程完成初始化、规划、Hosted Codex 握手和 change 级最终审查。 |
| `tests/integration/test_skill_hosted_protocol.py` | `rf-execute / rf-review / rf-resume` 的 skill 文档已经切到 hosted 协议。 |
| `tests/integration/test_docs_guides.py` | 命令手册与 FAQ 已生成并覆盖主工作流与常见问题。 |
| `tests/integration/test_run_loop.py` | The harness run and resume flow still reaches the expected terminal states. |
| `tests/unit/test_truth_layer.py` | `WorkspaceLayout` bootstraps `.railforge/{runtime,product,planning,execution}` correctly. |
| `tests/unit/test_file_lock_and_execution.py` | Execution and review services forward `.railforge/execution/tasks/...` writable paths. |
| `tests/unit/test_codeagent_real_failures.py` | Codex 兼容层不会继续发出 `xhigh`，Gemini 超时会返回结构化失败。 |

## Recommended Checks

- Run unit tests first when changing path layout or artifact storage.
- Run integration smoke tests after moving docs or changing skill wrappers.
- Run the full test suite after any change to `WorkspaceLayout`, artifact store, or run loop path semantics.
- Re-run hosted Codex protocol tests whenever `rf-execute`, `prepare-execution`, or `record-execution` changes.

## Installer / MCP Scope

- Installer entry: `npx railforge-workflow`
- MCP parity targets: `ace-tool`, `ace-tool-rs`, `fast-context`, `ContextWeaver`, `grok-search`, `Context7`, `Playwright`, `DeepWiki`, `Exa`
