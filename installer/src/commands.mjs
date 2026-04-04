import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

import { MCP_GROUPS } from './mcp.mjs'

const RAILFORGE_AGENTS_START = '<!-- RAILFORGE-INSTALLER-START -->'
const RAILFORGE_AGENTS_END = '<!-- RAILFORGE-INSTALLER-END -->'
const RAILFORGE_MCP_IDS = ['Context7', 'Playwright', 'grok-search']

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

1. 运行 \`python3 -m railforge spec-init --workspace <当前仓库路径>\`
2. 初始化 OpenSpec 和 \`.railforge\`
3. 验证环境是否可进入主工作流

## Next Steps

1. 运行 \`rf-spec-research\`
2. 如有缺失，先通过 \`npx railforge-workflow doctor\` 或安装器重新初始化修复
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
  'rf-openspec-apply': `---
name: rf-openspec-apply
description: Use when an approved RailForge change should hand off to the OpenSpec implementation lifecycle and continue through pending tasks.
---

# RF OpenSpec Apply

- 这是 RailForge 到 OpenSpec 生命周期的桥接入口。
- 进入条件：\`spec-review\` 已给出明确结论，且当前 change 需要继续推进剩余实现任务。
- 调用目标：\`openspec-apply-change\`

## Steps

1. 确认当前 change 名称
2. 调用 \`openspec-apply-change\`
3. 完成后回到 \`rf-spec-review\` 或发布说明收口
`,
  'rf-openspec-archive': `---
name: rf-openspec-archive
description: Use when a RailForge change has passed its final review gate and should be archived through the OpenSpec lifecycle.
---

# RF OpenSpec Archive

- 这是 RailForge 到 OpenSpec 生命周期的归档桥接入口。
- 进入条件：change 级 \`final_review.json\` 已批准，且没有待处理 blocker。
- 调用目标：\`openspec-archive-change\`

## Steps

1. 确认 final review 通过
2. 调用 \`openspec-archive-change\`
3. 记录 release notes 或对照文档
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
  'openspec-apply.md': `# /rf:openspec-apply

将当前 RailForge change 桥接到 OpenSpec 生命周期继续实施。

## Bridge Target
- openspec-apply-change

## Preconditions
- 已有批准后的 planning / review 结论
- 当前 change 仍有待完成任务
`,
  'openspec-archive.md': `# /rf:openspec-archive

在 RailForge 最终评审通过后桥接到 OpenSpec 归档动作。

## Bridge Target
- openspec-archive-change

## Preconditions
- final_review.json 已批准
- 当前 change 没有 blocker
`,
  'resume.md': `# /rf:resume\n\nUse the \`rf-resume\` skill to continue a blocked workflow.\n`,
  'status.md': `# /rf:status\n\nUse the \`rf-status\` skill to inspect the current RailForge state.\n`
}

const DEFAULT_AGENTS_MD = `# RailForge 工作约定

- 默认使用简体中文沟通。
- RailForge 已安装在 ~/.codex 命名空间。
- 优先在 Codex CLI 中使用以下 skills：
  - rf-spec-init
  - rf-spec-research
  - rf-spec-plan
  - rf-spec-impl
  - rf-spec-review
  - rf-openspec-apply
  - rf-openspec-archive
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

const RAILFORGE_BINARY_VERSION = '0.1.0'

function platformSuffix() {
  const platform = process.platform === 'darwin'
    ? 'darwin'
    : process.platform === 'win32'
      ? 'windows'
      : 'linux'
  const arch = os.arch() === 'arm64' ? 'arm64' : 'amd64'
  return `${platform}-${arch}`
}

function binaryFileName(baseName) {
  const ext = process.platform === 'win32' ? '.exe' : ''
  return `${baseName}-${platformSuffix()}${ext}`
}

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
      Context7: {
        command: 'npx',
        args: ['-y', '@upstash/context7-mcp@latest'],
        startup_timeout_sec: 30,
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
  const lines = ['model_reasoning_effort = "high"', 'sandbox_mode = "workspace-write"', '']
  for (const [id, config] of Object.entries(servers)) {
    lines.push(`[mcp_servers.${id}]`)
    lines.push(`command = "${config.command}"`)
    if (config.args?.length) {
      lines.push(`args = [${config.args.map((item) => `"${item}"`).join(', ')}]`)
    }
    if (config.startup_timeout_sec) {
      lines.push(`startup_timeout_sec = ${config.startup_timeout_sec}`)
    }
    if (config.tool_timeout_sec) {
      lines.push(`tool_timeout_sec = ${config.tool_timeout_sec}`)
    }
    lines.push('')
  }
  return `${lines.join('\n').trim()}\n`
}

function resolveInstallPaths(targetDir) {
  const homeRoot = path.resolve(targetDir)
  const codexRoot = path.join(homeRoot, '.codex')
  const railforgeRoot = path.join(codexRoot, '.railforge')
  return {
    homeRoot,
    codexRoot,
    railforgeRoot,
    binRoot: path.join(codexRoot, 'bin'),
    skillsRoot: path.join(codexRoot, 'skills', 'railforge'),
    codexAgentsPath: path.join(codexRoot, 'AGENTS.md'),
    codexConfigPath: path.join(codexRoot, 'config.toml'),
    modelsPath: path.join(railforgeRoot, 'models.yaml'),
    policiesPath: path.join(railforgeRoot, 'policies.yaml'),
    mcpCatalogPath: path.join(railforgeRoot, 'mcp.json'),
    statePath: path.join(railforgeRoot, 'installer-state.json'),
    claudeMcpPath: path.join(homeRoot, '.claude', '.mcp.json'),
    geminiSettingsPath: path.join(homeRoot, '.gemini', 'settings.json'),
    railforgeBinPath: path.join(codexRoot, 'bin', binaryFileName('railforge')),
    codeagentBinPath: path.join(codexRoot, 'bin', binaryFileName('railforge-codeagent')),
  }
}

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function readJsonIfExists(filePath, fallback = {}) {
  if (!(await fileExists(filePath))) {
    return { payload: structuredClone(fallback), createdFile: true }
  }
  return { payload: JSON.parse(await fs.readFile(filePath, 'utf8')), createdFile: false }
}

async function loadInstallerState(statePath) {
  if (!(await fileExists(statePath))) {
    return { installedFiles: [], sharedPatches: {} }
  }
  return JSON.parse(await fs.readFile(statePath, 'utf8'))
}

async function saveInstallerState(statePath, state) {
  await ensureDir(path.dirname(statePath))
  await fs.writeFile(statePath, JSON.stringify(state, null, 2), 'utf8')
}

async function upsertMarkedBlock(filePath, block) {
  await ensureDir(path.dirname(filePath))
  const createdFile = !(await fileExists(filePath))
  const markerRegex = new RegExp(`\\n?${escapeRegex(RAILFORGE_AGENTS_START)}[\\s\\S]*?${escapeRegex(RAILFORGE_AGENTS_END)}\\n?`, 'm')
  const content = createdFile ? '' : await fs.readFile(filePath, 'utf8')
  const markedBlock = `${RAILFORGE_AGENTS_START}\n${block}\n${RAILFORGE_AGENTS_END}\n`
  const next = markerRegex.test(content)
    ? content.replace(markerRegex, `\n${markedBlock}`)
    : (content.trimEnd() ? `${content.trimEnd()}\n\n${markedBlock}` : markedBlock)
  await fs.writeFile(filePath, next, 'utf8')
  return { path: filePath, createdFile, type: 'marked_block' }
}

async function removeMarkedBlock(patch) {
  const filePath = patch.path
  if (!(await fileExists(filePath))) {
    return
  }
  const markerRegex = new RegExp(`\\n?${escapeRegex(RAILFORGE_AGENTS_START)}[\\s\\S]*?${escapeRegex(RAILFORGE_AGENTS_END)}\\n?`, 'm')
  const content = await fs.readFile(filePath, 'utf8')
  const next = content.replace(markerRegex, '').trim()
  if (!next) {
    if (patch.createdFile) {
      await fs.rm(filePath, { force: true })
      return
    }
    await fs.writeFile(filePath, '', 'utf8')
    return
  }
  await fs.writeFile(filePath, `${next}\n`, 'utf8')
}

async function mergeMcpServersFile(filePath, servers, managedIds = RAILFORGE_MCP_IDS) {
  await ensureDir(path.dirname(filePath))
  const { payload, createdFile } = await readJsonIfExists(filePath, {})
  if (!payload.mcpServers || typeof payload.mcpServers !== 'object') {
    payload.mcpServers = {}
  }
  const previous = {}
  for (const id of managedIds) {
    previous[id] = Object.prototype.hasOwnProperty.call(payload.mcpServers, id) ? payload.mcpServers[id] : null
    if (!(id in servers) && id in payload.mcpServers) {
      delete payload.mcpServers[id]
    }
  }
  for (const [id, config] of Object.entries(servers)) {
    payload.mcpServers[id] = config
  }
  await fs.writeFile(filePath, JSON.stringify(payload, null, 2), 'utf8')
  return { path: filePath, createdFile, previous, type: 'json_mcp' }
}

async function restoreMcpServersFile(patch) {
  const filePath = patch.path
  if (!(await fileExists(filePath))) {
    return
  }
  const { payload } = await readJsonIfExists(filePath, {})
  if (!payload.mcpServers || typeof payload.mcpServers !== 'object') {
    payload.mcpServers = {}
  }
  for (const [id, previous] of Object.entries(patch.previous || {})) {
    if (previous === null) {
      delete payload.mcpServers[id]
    }
    else {
      payload.mcpServers[id] = previous
    }
  }
  const onlyEmptyMcpServers = Object.keys(payload).length === 1 && Object.keys(payload.mcpServers).length === 0
  if (patch.createdFile && (onlyEmptyMcpServers || Object.keys(payload).length === 0)) {
    await fs.rm(filePath, { force: true })
    return
  }
  await fs.writeFile(filePath, JSON.stringify(payload, null, 2), 'utf8')
}

function findTomlSection(lines, sectionName) {
  const header = `[${sectionName}]`
  const start = lines.findIndex(line => line.trim() === header)
  if (start === -1) {
    return null
  }
  let end = lines.length
  for (let i = start + 1; i < lines.length; i += 1) {
    if (/^\[.+\]$/.test(lines[i].trim())) {
      end = i
      break
    }
  }
  return { start, end }
}

function upsertTomlScalar(content, key, valueLiteral) {
  const regex = new RegExp(`^${escapeRegex(key)}\\s*=.*$`, 'm')
  const line = `${key} = ${valueLiteral}`
  const match = content.match(regex)
  if (match) {
    return {
      content: content.replace(regex, line),
      previous: match[0],
    }
  }
  return {
    content: `${line}\n${content}`.trimStart(),
    previous: null,
  }
}

function restoreTomlScalar(content, key, previous) {
  const regex = new RegExp(`^${escapeRegex(key)}\\s*=.*$(?:\\n)?`, 'm')
  if (previous === null) {
    return content.replace(regex, '')
  }
  if (regex.test(content)) {
    return content.replace(regex, `${previous}\n`)
  }
  return `${previous}\n${content}`.trimStart()
}

function upsertTomlSection(content, sectionName, bodyLines) {
  const lines = content.split('\n')
  const range = findTomlSection(lines, sectionName)
  const blockLines = [`[${sectionName}]`, ...bodyLines, '']
  let previous = null
  if (range) {
    previous = lines.slice(range.start, range.end).join('\n')
    lines.splice(range.start, range.end - range.start, ...blockLines)
  }
  else {
    if (lines.length && lines[lines.length - 1] !== '') {
      lines.push('')
    }
    lines.push(...blockLines)
  }
  return {
    content: lines.join('\n').replace(/\n{3,}/g, '\n\n').trimEnd() + '\n',
    previous,
  }
}

function restoreTomlSection(content, sectionName, previous) {
  const lines = content.split('\n')
  const range = findTomlSection(lines, sectionName)
  if (range) {
    if (previous === null) {
      lines.splice(range.start, range.end - range.start)
    }
    else {
      lines.splice(range.start, range.end - range.start, ...previous.split('\n'))
    }
  }
  else if (previous !== null) {
    lines.push(...previous.split('\n'))
  }
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trimEnd() + '\n'
}

async function patchCodexConfig(filePath, mcpConfig) {
  await ensureDir(path.dirname(filePath))
  const createdFile = !(await fileExists(filePath))
  let content = createdFile ? '' : await fs.readFile(filePath, 'utf8')

  const scalars = {}
  for (const [key, valueLiteral] of [
    ['model_reasoning_effort', '"high"'],
    ['sandbox_mode', '"workspace-write"'],
  ]) {
    const result = upsertTomlScalar(content, key, valueLiteral)
    content = result.content
    scalars[key] = result.previous
  }

  const sections = {}
  for (const id of RAILFORGE_MCP_IDS) {
    if (mcpConfig.mcpServers && id in mcpConfig.mcpServers) {
      continue
    }
    const sectionName = `mcp_servers.${id}`
    const result = upsertTomlSection(content, sectionName, [])
    content = result.content
    sections[sectionName] = result.previous
    content = restoreTomlSection(content, sectionName, null)
  }
  for (const [id, config] of Object.entries(mcpConfig.mcpServers || {})) {
    const sectionName = `mcp_servers.${id}`
    const bodyLines = [`command = "${config.command}"`]
    if (config.args?.length) {
      bodyLines.push(`args = [${config.args.map(item => `"${item}"`).join(', ')}]`)
    }
    if (config.startup_timeout_sec) {
      bodyLines.push(`startup_timeout_sec = ${config.startup_timeout_sec}`)
    }
    if (config.tool_timeout_sec) {
      bodyLines.push(`tool_timeout_sec = ${config.tool_timeout_sec}`)
    }
    const result = upsertTomlSection(content, sectionName, bodyLines)
    content = result.content
    sections[sectionName] = result.previous
  }

  await fs.writeFile(filePath, content, 'utf8')
  return { path: filePath, createdFile, scalars, sections, type: 'toml' }
}

async function restoreCodexConfig(patch) {
  const filePath = patch.path
  if (!(await fileExists(filePath))) {
    return
  }
  let content = await fs.readFile(filePath, 'utf8')
  for (const [sectionName, previous] of Object.entries(patch.sections || {})) {
    content = restoreTomlSection(content, sectionName, previous)
  }
  for (const [key, previous] of Object.entries(patch.scalars || {})) {
    content = restoreTomlScalar(content, key, previous)
  }
  const next = content.trim()
  if (patch.createdFile && !next) {
    await fs.rm(filePath, { force: true })
    return
  }
  await fs.writeFile(filePath, next ? `${next}\n` : '', 'utf8')
}

async function pruneIfEmpty(dirPath, stopAt = null) {
  let current = dirPath
  while (current && current !== stopAt) {
    try {
      const entries = await fs.readdir(current)
      if (entries.length > 0) {
        return
      }
      await fs.rmdir(current)
      current = path.dirname(current)
    }
    catch {
      return
    }
  }
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

async function writeMirrorFiles(targetDir, mcpConfig) {
  const paths = resolveInstallPaths(targetDir)
  return {
    codex: await patchCodexConfig(paths.codexConfigPath, mcpConfig),
    claude: await mergeMcpServersFile(paths.claudeMcpPath, mcpConfig.mcpServers || {}, RAILFORGE_MCP_IDS),
    gemini: await mergeMcpServersFile(paths.geminiSettingsPath, mcpConfig.mcpServers || {}, RAILFORGE_MCP_IDS),
    mirrors: [paths.codexConfigPath, paths.geminiSettingsPath, paths.claudeMcpPath],
  }
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
  const paths = resolveInstallPaths(targetDir)
  await ensureDir(paths.railforgeRoot)
  const mcpConfig = defaultMcpConfig()
  await fs.writeFile(paths.mcpCatalogPath, JSON.stringify(mcpConfig, null, 2), 'utf8')

  const state = await loadInstallerState(paths.statePath)
  const mirrorState = await writeMirrorFiles(targetDir, mcpConfig)
  state.sharedPatches = {
    ...(state.sharedPatches || {}),
    codexConfig: mirrorState.codex,
    claudeMcp: mirrorState.claude,
    geminiSettings: mirrorState.gemini,
  }
  await saveInstallerState(paths.statePath, state)

  return {
    action: 'config-mcp',
    status: 'written',
    target: paths.codexRoot,
    file: paths.mcpCatalogPath,
    mirrors: mirrorState.mirrors,
    mcpGroups: MCP_GROUPS,
  }
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

SCRIPT_DIR="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RAILFORGE_BIN="$CODEX_ROOT/bin/railforge"
PYTHON_BIN="\${RAILFORGE_PYTHON_BIN:-}"

if [[ -x "$RAILFORGE_BIN" ]]; then
  if [[ " $* " == *" --workspace "* ]]; then
    exec "$RAILFORGE_BIN" ${command} "$@"
  fi

  exec "$RAILFORGE_BIN" ${command} --workspace "$PWD" "$@"
fi

if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python not found. Install RailForge binary or set RAILFORGE_PYTHON_BIN." >&2
    exit 1
  fi
fi

if [[ " $* " == *" --workspace "* ]]; then
  exec "$PYTHON_BIN" -m railforge ${command} "$@"
fi

exec "$PYTHON_BIN" -m railforge ${command} --workspace "$PWD" "$@"
`
}

function bridgeScriptFor(skillName, bridgeName) {
  return `#!/usr/bin/env bash
set -euo pipefail

echo "${skillName} bridges to ${bridgeName}. Invoke that skill from Codex CLI."
`
}

export async function initProject(targetDir) {
  const paths = resolveInstallPaths(targetDir)
  const installedFiles = []

  await ensureDir(paths.codexRoot)
  await ensureDir(paths.binRoot)
  await ensureDir(paths.skillsRoot)
  await ensureDir(paths.railforgeRoot)
  await writeFile(paths.modelsPath, MODELS_YAML, installedFiles)
  await writeFile(paths.policiesPath, POLICIES_YAML, installedFiles)
  const mcpConfig = defaultMcpConfig()
  await writeFile(paths.mcpCatalogPath, JSON.stringify(mcpConfig, null, 2), installedFiles)

  const skillCommands = {
    'rf-spec-init': 'spec-init',
    'rf-spec-research': 'spec-research',
    'rf-spec-plan': 'spec-plan',
    'rf-spec-impl': 'spec-impl',
    'rf-spec-review': 'spec-review',
    'rf-resume': 'resume',
    'rf-status': 'status'
  }
  const bridgeSkills = {
    'rf-openspec-apply': 'openspec-apply-change',
    'rf-openspec-archive': 'openspec-archive-change',
  }

  for (const [skillName, content] of Object.entries(SKILL_CONTENT)) {
    await writeFile(path.join(paths.skillsRoot, skillName, 'SKILL.md'), content, installedFiles)
    await writeExecutable(
      path.join(paths.skillsRoot, skillName, 'scripts', 'run.sh'),
      bridgeSkills[skillName]
        ? bridgeScriptFor(skillName, bridgeSkills[skillName])
        : runScriptFor(skillCommands[skillName]),
      installedFiles
    )
  }

  const state = await loadInstallerState(paths.statePath)
  const mirrorState = await writeMirrorFiles(targetDir, mcpConfig)
  const agentsPatch = await upsertMarkedBlock(paths.codexAgentsPath, DEFAULT_AGENTS_MD)

  state.installedFiles = installedFiles
  state.sharedPatches = {
    codexAgents: agentsPatch,
    codexConfig: mirrorState.codex,
    claudeMcp: mirrorState.claude,
    geminiSettings: mirrorState.gemini,
  }
  await saveInstallerState(paths.statePath, state)

  return { action: 'init', status: 'installed', target: paths.codexRoot, installedFiles }
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
  const paths = resolveInstallPaths(targetDir)
  await ensureDir(paths.railforgeRoot)
  const content = buildModelsYaml(options)
  await fs.writeFile(paths.modelsPath, content, 'utf8')
  const state = await loadInstallerState(paths.statePath)
  const installedFiles = new Set(state.installedFiles || [])
  installedFiles.add(paths.modelsPath)
  state.installedFiles = Array.from(installedFiles)
  await saveInstallerState(paths.statePath, state)
  return {
    action: 'config-model',
    status: 'written',
    target: paths.codexRoot,
    file: paths.modelsPath,
    options,
  }
}

export async function probeMcpConfig(targetDir) {
  const paths = resolveInstallPaths(targetDir)
  const filePath = paths.mcpCatalogPath
  let configured = []
  if (await fileExists(filePath)) {
    const payload = JSON.parse(await fs.readFile(filePath, 'utf8'))
    configured = Object.keys(payload.mcpServers || {})
  }
  const mirrors = [paths.codexConfigPath, paths.geminiSettingsPath, paths.claudeMcpPath]
  const existingMirrors = []
  for (const mirror of mirrors) {
    if (await fileExists(mirror)) {
      existingMirrors.push(mirror)
    }
  }
  return {
    action: 'probe-mcp',
    status: 'checked',
    target: paths.codexRoot,
    configured,
    mirrors: existingMirrors,
  }
}

export async function uninstallProject(targetDir) {
  const paths = resolveInstallPaths(targetDir)
  const state = await loadInstallerState(paths.statePath)

  for (const file of (state.installedFiles || []).slice().reverse()) {
    await fs.rm(file, { force: true })
  }

  if (state.sharedPatches?.codexAgents) {
    await removeMarkedBlock(state.sharedPatches.codexAgents)
  }
  if (state.sharedPatches?.codexConfig) {
    await restoreCodexConfig(state.sharedPatches.codexConfig)
  }
  if (state.sharedPatches?.claudeMcp) {
    await restoreMcpServersFile(state.sharedPatches.claudeMcp)
  }
  if (state.sharedPatches?.geminiSettings) {
    await restoreMcpServersFile(state.sharedPatches.geminiSettings)
  }

  await fs.rm(paths.statePath, { force: true })
  await fs.rm(path.join(paths.codexRoot, 'skills', 'railforge'), { recursive: true, force: true })
  await fs.rm(paths.railforgeRoot, { recursive: true, force: true })
  await pruneIfEmpty(path.join(paths.codexRoot, 'skills'), paths.codexRoot)
  await pruneIfEmpty(paths.codexRoot, paths.homeRoot)
  await pruneIfEmpty(path.dirname(paths.claudeMcpPath), paths.homeRoot)
  await pruneIfEmpty(path.dirname(paths.geminiSettingsPath), paths.homeRoot)

  return { action: 'uninstall', status: 'removed', target: paths.codexRoot }
}
