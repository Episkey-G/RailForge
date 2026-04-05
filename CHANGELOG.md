# Changelog

本文件记录 RailForge 的所有版本更新和修改日志。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## [Unreleased]

### Added
- `approve-and-resume` 命令：一步完成批准并自动恢复工作流，带 blocked_reason 匹配校验
- `answer-and-resume` 命令：一步完成澄清回答并自动恢复工作流
- `adopt-worktree` 命令：人工修复吸收口，扫描全部 changed files 划分 in-scope/out-of-scope，有越界则拒绝
- `RunMeta.recovery_action` 字段：区分 blocked_reason（根因）和 recovery_action（下一步动作）
- `ContractGate.validate_repo_reality()`：在 CONTRACT_NEGOTIATION 阶段校验 allowed_paths 在工作区实际存在
- `spec_init` doctor 分级：返回 READY / DEGRADED / BLOCKED 三级状态
- workspace 自动推断：前门命令自动向上查找 `.railforge/` 或 `.git/` 标记
- 14 个新增回归测试覆盖全部 stabilize 修复点

### Changed
- `_handle_repairing()` 恢复目标从 `IMPLEMENTING` 改为 `STATIC_REVIEW`（repair 耗尽后 resume 不再重放 lead writer）
- FSM 新增 `REPAIRING -> STATIC_REVIEW` 合法转换
- `resume()` 恢复到 STATIC_REVIEW 时自动填充 `_last_implementation`
- 前门命令（spec-*, status, approve, resume 等）`--workspace` 从 required 改为 optional
- 低层协议命令（prepare-execution, record-execution, answer）`--workspace` 保持 required
- repo reality audit 从 `run_loop.py` 下沉到 `ContractGate`

### Fixed
- 修复 repair_budget_exhausted 后 resume 重新触发 lead writer 导致错误执行重放的问题
- 修复人工修复后 record-execution 拒绝写回（因不在 hosted_execution_required 状态）的问题
- 修复 contract 指向不存在目录时执行器系统性偏航的问题
- 修复 spec-impl 等命令不传 --workspace 直接报错的前门 UX 问题
- 修复批准和恢复需要两步操作的交互问题

---

## [0.1.7] - 2025-04-05

### Added
- Spec 主工作流命令：`spec-init`, `spec-research`, `spec-plan`, `spec-impl`, `spec-review`
- 对应 Skill 入口：`rf-spec-init`, `rf-spec-research`, `rf-spec-plan`, `rf-spec-impl`, `rf-spec-review`
- Hosted Codex 默认执行路径：`prepare-execution / record-execution` 协议
- OpenSpec 生命周期桥接：`rf-openspec-apply`, `rf-openspec-archive`
- Spec review 双模型评估和 `final_review.json` 闸门
- Run-first、semantic-rooted runtime 拓扑
- `railforge.codeagent` 内置多后端 runner (Claude/Gemini/Codex fallback)
- `.agents/skills/` Codex CLI workflow skill 入口
- 平台二进制构建（`scripts/build_binaries.py` + GitHub Actions）

### Added (Installer)
- `railforge-workflow` npm 安装器 v0.1.13
- 交互式菜单：init, update, config-mcp, config-model, probe-mcp, doctor, help, uninstall
- MCP 分组与 CCG 对齐：ace-tool, fast-context, ContextWeaver, grok-search, Context7, Playwright, DeepWiki, Exa
- Codex-first 命名空间安装：`~/.codex/bin/`, `~/.codex/skills/railforge/`, `~/.codex/.railforge/`
- 共享文件增量写入和增量回滚

---

## [0.1.6] - 2025-04-04

### Fixed
- 安装器主菜单返回主菜单功能修复
- 菜单交互使用方向键而非编号输入

## [0.1.5] - 2025-04-04

### Changed
- 安装根从 target 根目录改为 `target/.codex`
- 卸载只删除 RailForge 自己的命名空间目录

## [0.1.4] - 2025-04-04

### Fixed
- 安装器菜单模板对齐

## [0.1.3] - 2025-04-04

### Fixed
- 安装器重复菜单问题
