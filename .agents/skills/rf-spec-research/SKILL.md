---
name: rf-spec-research
description: Use when a requirement must be transformed into constraint sets, HITL questions, and an OpenSpec proposal before any planning or implementation begins.
---

# RF Spec Research

## Core Philosophy

- 研究阶段输出的是约束集，不是信息堆砌。
- 目标是缩小解空间，让后续 `spec-plan` 变成零决策规划。
- 所有未决假设都必须显式写出来，不能悄悄带入实现阶段。

## Guardrails

- 这一阶段只做研究和 proposal，不进入实现。
- 必须整理 HITL 问题、范围边界和风险点。
- 必须把结果写入 OpenSpec proposal 和 `.railforge/product/*`。
- 如果存在关键歧义，必须 `BLOCKED`，不要继续到 `spec-plan`。

## Steps

1. 运行 `railforge spec-research`
2. 读取当前需求、相关上下文和代码约束
3. 提炼：
   - 约束
   - 风险
   - 依赖
   - open questions
4. 写入：
   - OpenSpec proposal
   - `product_spec.draft.yaml`
   - `questions.yaml`
   - `decisions.yaml`
5. 如果仍有歧义，停止并交还人工确认

## Required Outputs

- OpenSpec proposal
- 约束集
- HITL 问题清单
- 成功判据初稿

## Phase Boundary

- 不要进入 `spec-plan`
- 不要进入 `spec-impl`
- 研究完成后，下一步应该是 `rf-spec-plan` 或 `/rf:spec-plan`
