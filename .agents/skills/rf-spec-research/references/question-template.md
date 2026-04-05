# Clarification Question Template

- `prompt`: 面向用户的澄清问题，必须能直接回答。
- `category`: 使用稳定领域标签，例如 `clarification`、`timezone`、`copy`、`api_contract`。
- `default`: 只有在存在安全默认值时才填写。
- `blocking_reason`: 明确说明为什么该问题会阻塞 planning 或 contract。
- `source`: 说明问题由哪一段 ambiguity、约束或上下文触发。
