# Clarification Question Template

- `prompt`: 面向用户的零决策问题，必须能直接消除实现拍板点。
- `category`: 使用稳定领域标签，例如 `clarification`、`timezone`、`copy`、`api_contract`。
- `default`: 只有在存在安全默认值且不会破坏 planning truth 时才填写。
- `blocking_reason`: 明确说明为什么不回答该问题会阻塞 backlog、contract 或 task decomposition。
- `source`: 说明问题由哪一段 ambiguity、约束、答案冲突或审批上下文触发。
