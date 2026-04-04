import fs from 'node:fs/promises'
import path from 'node:path'

import { MCP_GROUPS } from './mcp.mjs'

const SKILL_CONTENT = {
  'rf-spec-init': `---
name: rf-spec-init
description: Use when a repository needs the RailForge spec workflow initialized, OpenSpec scaffolded, MCP readiness checked, or the user is starting the workflow for the first time.
---

# RF Spec Init

## Core Philosophy

- OpenSpec 提供规范框架，RailForge 负责工作流编排与多模型协作。
- 这一阶段先确保工具就绪，避免后续阶段中途发现依赖缺失。

## Guardrails

- 不要跳过初始化直接进入 \`spec-research\`。
- 必须确认 OpenSpec、\`.railforge\`、Codex、Claude、Gemini 和 MCP 状态。

## Steps

1. 运行 \`python -m railforge spec-init\`
2. 初始化 OpenSpec 和 \`.railforge\`
3. 验证环境是否可进入主工作流

## Next Steps

1. 运行 \`rf-spec-research\`
2. 如有缺失，先通过安装器或 doctor 修复
`,
  'rf-spec-research': `---
name: rf-spec-research
description: Use when a requirement must be transformed into constraint sets, HITL questions, and an OpenSpec proposal before any planning or implementation begins.
---

# RF Spec Research

## Core Philosophy

- 研究阶段输出的是约束集，不是信息堆砌。
- 所有未决假设都必须显式写出来，不能悄悄带进实现。

## Guardrails

- 这一阶段只生成 proposal 和研究工件。
- 不要进入 planning 或 implementation。

## Steps

1. 运行 \`python -m railforge spec-research\`
2. 提炼约束、风险、依赖和 open questions
3. 写入 OpenSpec proposal 与 \`.railforge/product/*\`

## Phase Boundary

- 不进入 \`spec-plan\`
- 不进入 \`spec-impl\`
`,
  'rf-spec-plan': `---
name: rf-spec-plan
description: Use when research is approved and the team must turn constraints into a zero-decision executable plan with tasks, contracts, and explicit ambiguity elimination.
---

# RF Spec Plan

## Core Philosophy

- \`spec-plan\` 的目标是消除实现阶段的决策点。

## Guardrails

- 不要带着关键歧义进入 \`spec-impl\`。
- 必须生成 design、tasks、spec 和 backlog/contract。

## Steps

1. 运行 \`python -m railforge spec-plan\`
2. 把 proposal 收敛成 zero-decision executable plan
3. 写入 OpenSpec 和 \`.railforge/planning/*\`
`,
  'rf-spec-impl': `---
name: rf-spec-impl
description: Use when spec planning is approved and the full implementation loop should run through Hosted Codex, dual-model review, repair, and completion gates.
---

# RF Spec Impl

## Core Philosophy

- \`spec-impl\` 是按批准计划进行机械执行，而不是重新做设计。

## Guardrails

- 不要越过 task scope 和 contract。
- Hosted Codex 的执行结果必须通过 \`record-execution\` 回写。
- 不要跳过 review、repair 和 blocked 语义。

## Hosted Codex Loop

1. 运行 \`python -m railforge spec-impl\`
2. 内部执行：
   - \`prepare-execution\`
   - Hosted Codex 主写作
   - \`record-execution\`
3. Python 状态机继续做 review / repair / next task
`,
  'rf-spec-review': `---
name: rf-spec-review
description: Use when an implementation or active change needs an independent dual-model compliance review against spec constraints, quality gates, and regression risks.
---

# RF Spec Review

## Core Philosophy

- 双模型交叉审查比单模型更容易发现盲点。
- \`spec-review\` 是独立工具，不依赖必须完成整个 \`spec-impl\`。

## Severity Model

- Critical
- Warning
- Info

## Steps

1. 运行 \`python -m railforge spec-review\`
2. 收集 OpenSpec 与 \`.railforge\` 工件
3. 触发 Python review gate
4. 汇总 Claude 和 Gemini 发现
`,
  'rf-resume': `---
name: rf-resume
description: Codex CLI-first skill for resuming a blocked or paused RailForge workflow.
---

# RF Resume

- Entry point: \`python -m railforge resume\`
`,
  'rf-status': `---
name: rf-status
description: Codex CLI-first skill for checking the current RailForge workflow state.
---

# RF Status

- Entry point: \`python -m railforge status\`
`
}

const COMMAND_TEMPLATES = {
  'spec-init.md': `# /rf:spec-init

初始化 OpenSpec 与 RailForge runtime，并检查多模型与 MCP 环境是否就绪。

## Next Steps
- /rf:spec-research "<需求描述>"
- /rf:spec-plan
- /rf:spec-impl
`,
  'spec-research.md': `# /rf:spec-research

将需求转为约束集、HITL 问题和 OpenSpec proposal。

## Guardrails
- 只做研究，不进入实现
- 输出 proposal 与约束，不做代码修改

## Next Step
- /rf:spec-plan
`,
  'spec-plan.md': `# /rf:spec-plan

把 proposal 收敛成零决策可执行计划。

## Guardrails
- 消除歧义
- 生成 design / tasks / spec / backlog / contract

## Next Step
- /rf:spec-impl
`,
  'spec-impl.md': `# /rf:spec-impl

运行批准后的规范实现主循环，默认使用 Hosted Codex。

## Internal Loop
- prepare-execution
- Hosted Codex implementation
- record-execution
- review / repair / next task

## Standalone Tool
- /rf:spec-review
`,
  'spec-review.md': `# /rf:spec-review

运行独立的双模型规范审查。

## Severity
- Critical
- Warning
- Info
`,
  'resume.md': `# /rf:resume\n\nUse the \`rf-resume\` skill to continue a blocked workflow.\n`,
  'status.md': `# /rf:status\n\nUse the \`rf-status\` skill to inspect the current RailForge state.\n`
}

const DEFAULT_AGENTS_MD = `# RailForge 工作约定

- 默认使用简体中文沟通。
- 主工作流优先使用：
  - rf-spec-init
  - rf-spec-research
  - rf-spec-plan
  - rf-spec-impl
  - rf-spec-review
- 默认 lead writer 路径是 hosted_codex。
`

const MODELS_YAML = `version: 2
roles:
  lead_writer:
    driver: hosted_codex
    adapter: hosted_codex
    model: gpt-5.4
  backend_specialist:
    driver: claude_cli
    adapter: claude_cli
    model: glm5
  frontend_specialist:
    driver: gemini_cli
    adapter: gemini_cli
    model: gemini-3.1-pro-preview
  backend_evaluator:
    driver: claude_cli
    adapter: claude_cli
    model: glm5
  frontend_evaluator:
    driver: gemini_cli
    adapter: gemini_cli
    model: gemini-3.1-pro-preview
`

const POLICIES_YAML = `version: 2
budgets:
  default_repair_budget: 2
  max_repair_attempts_per_task: 3
  require_manual_resume_after_blocked: true
guardrails:
  enforce_contract_gate: true
  enforce_allowed_paths: true
  enforce_verification: true
`

function defaultMcpConfig() {
  return {
    mcpServers: {
      context7: {
        command: 'npx',
        args: ['-y', '@upstash/context7-mcp@latest']
      },
      Playwright: {
        command: 'npx',
        args: ['-y', '@playwright/mcp@latest']
      },
      'grok-search': {
        command: 'npx',
        args: ['-y', 'github:GuDaStudio/GrokSearch@grok-with-tavily', 'grok-search']
      }
    },
    catalog: MCP_GROUPS
  }
}

function renderCodexToml(mcpConfig) {
  const servers = mcpConfig.mcpServers || {}
  const lines = []
  for (const [id, config] of Object.entries(servers)) {
    lines.push(`[mcp_servers.${id}]`)
    lines.push(`command = "${config.command}"`)
    if (config.args?.length) {
      lines.push(`args = [${config.args.map((item) => `"${item}"`).join(', ')}]`)
    }
    lines.push('')
  }
  return `${lines.join('\n').trim()}\n`
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true })
}

async function fileExists(filePath) {
  try {
    await fs.stat(filePath)
    return true
  }
  catch {
    return false
  }
}

async function writeMirrorFiles(target, mcpConfig, installedFiles = null) {
  const codexPath = path.join(target, '.codex', 'config.toml')
  const geminiPath = path.join(target, '.gemini', 'settings.json')
  const claudePath = path.join(target, '.claude', '.mcp.json')

  await ensureDir(path.dirname(codexPath))
  await ensureDir(path.dirname(geminiPath))
  await ensureDir(path.dirname(claudePath))

  await fs.writeFile(codexPath, renderCodexToml(mcpConfig), 'utf8')
  await fs.writeFile(geminiPath, JSON.stringify({ mcpServers: mcpConfig.mcpServers || {} }, null, 2), 'utf8')
  await fs.writeFile(claudePath, JSON.stringify(mcpConfig, null, 2), 'utf8')

  if (installedFiles) {
    installedFiles.push(codexPath, geminiPath, claudePath)
  }

  return [codexPath, geminiPath, claudePath]
}

function buildModelsYaml({
  leadWriter = 'hosted_codex',
  backendSpecialist = 'claude_cli',
  frontendSpecialist = 'gemini_cli',
  backendEvaluator = 'claude_cli',
  frontendEvaluator = 'gemini_cli',
} = {}) {
  return `version: 2
roles:
  lead_writer:
    driver: ${leadWriter}
    adapter: ${leadWriter}
    model: gpt-5.4
  backend_specialist:
    driver: ${backendSpecialist}
    adapter: ${backendSpecialist}
    model: glm5
  frontend_specialist:
    driver: ${frontendSpecialist}
    adapter: ${frontendSpecialist}
    model: gemini-3.1-pro-preview
  backend_evaluator:
    driver: ${backendEvaluator}
    adapter: ${backendEvaluator}
    model: glm5
  frontend_evaluator:
    driver: ${frontendEvaluator}
    adapter: ${frontendEvaluator}
    model: gemini-3.1-pro-preview
`
}

export async function writeMcpConfig(targetDir) {
  const target = path.resolve(targetDir)
  await ensureDir(target)
  const filePath = path.join(target, '.mcp.json')
  const mcpConfig = defaultMcpConfig()
  await fs.writeFile(filePath, JSON.stringify(mcpConfig, null, 2), 'utf8')
  const mirrors = await writeMirrorFiles(target, mcpConfig)
  return { action: 'config-mcp', status: 'written', target, file: filePath, mirrors, mcpGroups: MCP_GROUPS }
}

async function writeFile(filePath, content, installedFiles) {
  await ensureDir(path.dirname(filePath))
  await fs.writeFile(filePath, content, 'utf8')
  installedFiles.push(filePath)
}

async function writeExecutable(filePath, content, installedFiles) {
  await writeFile(filePath, content, installedFiles)
  await fs.chmod(filePath, 0o755)
}

function runScriptFor(command) {
  return `#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "\${BASH_SOURCE[0]}")/../../../../" && pwd)"
cd "$ROOT"

exec python -m railforge ${command} "$@"
`
}

export async function initProject(targetDir) {
  const target = path.resolve(targetDir)
  const installedFiles = []

  await ensureDir(target)
  await writeFile(path.join(target, 'AGENTS.md'), DEFAULT_AGENTS_MD, installedFiles)
  await ensureDir(path.join(target, 'openspec', 'changes'))
  await ensureDir(path.join(target, 'openspec', 'specs'))
  await ensureDir(path.join(target, '.railforge', 'runtime'))
  await writeFile(path.join(target, '.railforge', 'runtime', 'models.yaml'), MODELS_YAML, installedFiles)
  await writeFile(path.join(target, '.railforge', 'runtime', 'policies.yaml'), POLICIES_YAML, installedFiles)
  const mcpConfig = defaultMcpConfig()
  await writeFile(path.join(target, '.mcp.json'), JSON.stringify(mcpConfig, null, 2), installedFiles)
  await writeMirrorFiles(target, mcpConfig, installedFiles)

  const skillCommands = {
    'rf-spec-init': 'spec-init',
    'rf-spec-research': 'spec-research',
    'rf-spec-plan': 'spec-plan',
    'rf-spec-impl': 'spec-impl',
    'rf-spec-review': 'spec-review',
    'rf-resume': 'resume',
    'rf-status': 'status'
  }

  for (const [skillName, content] of Object.entries(SKILL_CONTENT)) {
    await writeFile(path.join(target, '.agents', 'skills', skillName, 'SKILL.md'), content, installedFiles)
    await writeExecutable(
      path.join(target, '.agents', 'skills', skillName, 'scripts', 'run.sh'),
      runScriptFor(skillCommands[skillName]),
      installedFiles
    )
  }

  for (const [filename, content] of Object.entries(COMMAND_TEMPLATES)) {
    await writeFile(path.join(target, '.claude', 'commands', 'rf', filename), content, installedFiles)
  }

  await writeFile(
    path.join(target, '.railforge', 'installer-state.json'),
    JSON.stringify({ installedFiles }, null, 2),
    installedFiles
  )

  return { action: 'init', status: 'installed', target, installedFiles }
}

export async function updateProject(targetDir) {
  const result = await initProject(targetDir)
  return {
    action: 'update',
    status: 'updated',
    target: result.target,
    installedFiles: result.installedFiles,
  }
}

export async function writeModelConfig(targetDir, options = {}) {
  const target = path.resolve(targetDir)
  const modelsPath = path.join(target, '.railforge', 'runtime', 'models.yaml')
  await ensureDir(path.dirname(modelsPath))
  const content = buildModelsYaml(options)
  await fs.writeFile(modelsPath, content, 'utf8')
  return {
    action: 'config-model',
    status: 'written',
    target,
    file: modelsPath,
    options,
  }
}

export async function probeMcpConfig(targetDir) {
  const target = path.resolve(targetDir)
  const filePath = path.join(target, '.mcp.json')
  let configured = []
  if (await fileExists(filePath)) {
    const payload = JSON.parse(await fs.readFile(filePath, 'utf8'))
    configured = Object.keys(payload.mcpServers || {})
  }
  const mirrors = [
    path.join(target, '.codex', 'config.toml'),
    path.join(target, '.gemini', 'settings.json'),
    path.join(target, '.claude', '.mcp.json'),
  ]
  const existingMirrors = []
  for (const mirror of mirrors) {
    if (await fileExists(mirror)) {
      existingMirrors.push(mirror)
    }
  }
  return {
    action: 'probe-mcp',
    status: 'checked',
    target,
    configured,
    mirrors: existingMirrors,
  }
}

export async function uninstallProject(targetDir) {
  const target = path.resolve(targetDir)
  const statePath = path.join(target, '.railforge', 'installer-state.json')
  let installedFiles = []
  try {
    installedFiles = JSON.parse(await fs.readFile(statePath, 'utf8')).installedFiles || []
  }
  catch {
    installedFiles = []
  }

  for (const file of installedFiles.slice().reverse()) {
    await fs.rm(file, { force: true })
  }

  await fs.rm(path.join(target, '.agents'), { recursive: true, force: true })
  await fs.rm(path.join(target, '.claude', 'commands', 'rf'), { recursive: true, force: true })
  await fs.rm(path.join(target, '.claude', '.mcp.json'), { force: true })
  await fs.rm(path.join(target, '.railforge'), { recursive: true, force: true })
  await fs.rm(path.join(target, '.codex'), { recursive: true, force: true })
  await fs.rm(path.join(target, '.gemini'), { recursive: true, force: true })
  await fs.rm(path.join(target, 'openspec'), { recursive: true, force: true })
  await fs.rm(path.join(target, 'AGENTS.md'), { force: true })
  await fs.rm(path.join(target, '.mcp.json'), { force: true })

  return { action: 'uninstall', status: 'removed', target }
}
