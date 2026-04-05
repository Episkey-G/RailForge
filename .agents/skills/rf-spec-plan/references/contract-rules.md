# Planning Contract Rules

- `spec-plan` 输出的是零决策实现合同，而不是实现代码。
- 合同必须声明 `allowed_paths`、`deliverables`、`locked_decisions`。
- `contract` 批准之前，`spec-impl` 只能返回 `BLOCKED`。
