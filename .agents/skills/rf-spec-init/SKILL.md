---
name: rf-spec-init
description: Use when a repository needs the RailForge spec workflow initialized, OpenSpec scaffolded, MCP readiness checked, or the user is starting the workflow for the first time.
---

# RF Spec Init

## Core Philosophy

- OpenSpec 提供规范框架，RailForge 负责工作流编排与多模型协作。
- 这一阶段必须先把环境和工具准备好，避免在执行中途才发现依赖缺失。
- 失败要尽早暴露，不要把问题拖到 `spec-plan` 或 `spec-impl`。

## Guardrails

- 不要跳过初始化直接进入 `spec-research`。
- 不要覆盖用户已有配置，除非安装器或用户明确要求。
- 必须确认 OpenSpec、`.railforge`、Codex、Claude、Gemini 和 MCP 状态，再宣布环境可用。
- 发现依赖缺失时，输出明确的下一步修复建议。

## Steps

1. 运行 `python3 -m railforge spec-init --workspace <当前仓库路径>`
2. 确认 `openspec/changes` 和 `openspec/specs` 已存在
3. 确认 `.railforge/runtime/models.yaml` 与 `.railforge/runtime/policies.yaml` 已生成
4. 通过安装器 `npx railforge-workflow doctor` 确认：
   - Codex CLI
   - Claude CLI
   - Gemini CLI
   - jq
   - MCP 分组配置
5. 输出初始化结果和后续建议

## Summary Report

至少应报告：

- OpenSpec 环境是否就绪
- RailForge runtime 是否就绪
- Hosted Codex 路径是否可用
- Claude / Gemini runner 是否可用
- MCP 配置是否齐备

## Next Steps

1. 运行 `rf-spec-research` 或 `/rf:spec-research`
2. 若环境缺失，先通过 `npx railforge-workflow doctor` 或安装器重新初始化修复
