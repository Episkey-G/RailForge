import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

import { MCP_GROUPS } from './mcp.mjs'

const RAILFORGE_AGENTS_START = '<!-- RAILFORGE-INSTALLER-START -->'
const RAILFORGE_AGENTS_END = '<!-- RAILFORGE-INSTALLER-END -->'
const RAILFORGE_MCP_IDS = ['ace-tool', 'ace-tool-rs', 'fast-context', 'contextweaver', 'Context7', 'Playwright', 'mcp-deepwiki', 'exa', 'grok-search']
const GROK_SEARCH_RULE_NAME = 'ccg-grok-search.md'
const FAST_CONTEXT_RULE_NAME = 'ccg-fast-context.md'
const FAST_CONTEXT_MARKER_START = '<!-- RAILFORGE-FAST-CONTEXT-START -->'
const FAST_CONTEXT_MARKER_END = '<!-- RAILFORGE-FAST-CONTEXT-END -->'
const OUTPUT_STYLE_TEMPLATES = {
  'engineer-professional': '# engineer-professional\n\nUse a concise, professional engineering tone.\n',
  'nekomata-engineer': '# nekomata-engineer\n\nUse a warm but technically precise cat-eared engineer tone.\n',
  'laowang-engineer': '# laowang-engineer\n\nUse a direct, practical, senior engineer tone.\n',
  'ojousama-engineer': '# ojousama-engineer\n\nUse a precise but stylized noble-engineer tone.\n',
  'abyss-cultivator': '# abyss-cultivator\n\nUse a dramatic, dense, high-signal technical narration style.\n',
  'abyss-concise': '# abyss-concise\n\nUse a terse, high-density technical style.\n',
  'abyss-command': '# abyss-command\n\nUse a command-like, operationally focused style.\n',
  'abyss-ritual': '# abyss-ritual\n\nUse a ritualized but still technically accurate style.\n',
}

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

1. 运行 \`railforge spec-init --workspace <当前仓库路径>\`
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

1. 运行 \`railforge spec-research\`
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

1. 运行 \`railforge spec-plan\`
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

1. 运行 \`railforge spec-impl\`
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

1. 运行 \`railforge spec-review\`
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

- Entry point: \`railforge resume\`
`,
  'rf-status': `---
name: rf-status
description: Codex CLI-first skill for checking the current RailForge workflow state.
---

# RF Status

- Entry point: \`railforge status\`
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

const INSTALLER_PACKAGE = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))
const INSTALLER_VERSION = INSTALLER_PACKAGE.version
const RAILFORGE_BINARY_VERSION = INSTALLER_PACKAGE.railforgeBinaryVersion || INSTALLER_VERSION
const GITHUB_REPO = 'Episkey-G/RailForge'
const RELEASE_TAG = 'railforge-preset'

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

function installedBinaryName(baseName) {
  return `${baseName}${process.platform === 'win32' ? '.exe' : ''}`
}

function binarySources() {
  const customBaseUrls = (process.env.RAILFORGE_BINARY_BASE_URL || '')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean)
  if (customBaseUrls.length > 0) {
    return customBaseUrls.map(url => ({ name: 'custom', url, timeoutMs: 15_000 }))
  }
  return [
    {
      name: 'GitHub Release',
      url: `https://github.com/${GITHUB_REPO}/releases/download/${RELEASE_TAG}`,
      timeoutMs: 120_000,
    },
  ]
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

const GROK_SEARCH_PROMPT = `## 0. Language and Format Standards

- Interaction language between tools/models should be English; user-facing output should be Chinese.
- Use standard Markdown and keep answers concise, evidence-oriented, and explicit about uncertainty.

## 1. Search and Evidence Standards

- Use the \`mcp__grok-search\` tool for web searches when up-to-date external information matters.
- Treat search output as evidence to evaluate, not truth by default.
- Important factual claims should be cross-checked against multiple independent sources when possible.
- If sources conflict, explain the conflict and identify the stronger evidence.

## 2. Reasoning Standards

- Be direct and information-dense.
- State assumptions, scope limits, and uncertainty explicitly.
- Challenge flawed premises with evidence instead of silently accepting them.
`

const FAST_CONTEXT_PROMPT_PRIMARY = `# fast-context MCP 工具使用指南

## 核心原则

任何需要理解代码上下文、探索性搜索、或自然语言定位代码的场景，优先使用 \`mcp__fast-context__fast_context_search\`。
`

const FAST_CONTEXT_PROMPT_AUXILIARY = `# fast-context MCP 工具使用指南（辅助模式）

## 核心原则

主检索工具为 ace-tool。只有当 ace-tool 无法满足语义搜索需求时，才使用 \`mcp__fast-context__fast_context_search\` 作为补充。
`

function grokSearchServerConfig(env = {}) {
  const config = {
    command: 'npx',
    args: ['-y', 'github:GuDaStudio/GrokSearch@grok-with-tavily', 'grok-search'],
  }
  const filteredEnv = Object.fromEntries(
    Object.entries(env).filter(([, value]) => value !== null && value !== undefined && value !== ''),
  )
  if (Object.keys(filteredEnv).length > 0) {
    config.env = filteredEnv
  }
  return config
}

function aceToolServerConfig({ baseUrl = '', token = '' } = {}) {
  const args = ['-y', 'ace-tool@latest']
  if (baseUrl) args.push('--base-url', baseUrl)
  if (token) args.push('--token', token)
  return { command: 'npx', args }
}

function aceToolRsServerConfig({ baseUrl = '', token = '' } = {}) {
  const args = ['ace-tool-rs']
  if (baseUrl) args.push('--base-url', baseUrl)
  if (token) args.push('--token', token)
  return { command: 'npx', args, env: { RUST_LOG: 'info' } }
}

function fastContextServerConfig({ apiKey = '', includeSnippets = false } = {}) {
  const env = {}
  if (apiKey) env.WINDSURF_API_KEY = apiKey
  if (includeSnippets) env.FC_INCLUDE_SNIPPETS = 'true'
  return {
    command: 'npx',
    args: ['-y', '--prefer-online', 'fast-context-mcp@latest'],
    ...(Object.keys(env).length > 0 ? { env } : {}),
  }
}

function contextWeaverServerConfig() {
  return { command: 'contextweaver', args: ['mcp'] }
}

function genericServerConfig(command, args, env = {}) {
  const filteredEnv = Object.fromEntries(
    Object.entries(env).filter(([, value]) => value !== null && value !== undefined && value !== ''),
  )
  return { command, args, ...(Object.keys(filteredEnv).length > 0 ? { env: filteredEnv } : {}) }
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
    binaryStatePath: path.join(railforgeRoot, 'binaries.json'),
    claudeMcpPath: path.join(homeRoot, '.claude', '.mcp.json'),
    claudeSettingsPath: path.join(homeRoot, '.claude', 'settings.json'),
    geminiSettingsPath: path.join(homeRoot, '.gemini', 'settings.json'),
    railforgeBinPath: path.join(codexRoot, 'bin', installedBinaryName('railforge')),
    codeagentBinPath: path.join(codexRoot, 'bin', installedBinaryName('railforge-codeagent')),
    railforgeAssetName: binaryFileName('railforge'),
    codeagentAssetName: binaryFileName('railforge-codeagent'),
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

function timestampForBackup() {
  return new Date().toISOString().replaceAll(':', '-').replaceAll('.', '-')
}

async function backupFileIfExists(filePath, backupDir, prefix) {
  if (!(await fileExists(filePath))) {
    return null
  }
  await ensureDir(backupDir)
  const backupPath = path.join(backupDir, `${prefix}-${timestampForBackup()}.json`)
  await fs.copyFile(filePath, backupPath)
  return backupPath
}

async function upsertMarkedBlockWithMarkers(filePath, block, startMarker, endMarker) {
  await ensureDir(path.dirname(filePath))
  const createdFile = !(await fileExists(filePath))
  const content = createdFile ? '' : await fs.readFile(filePath, 'utf8')
  const markerRegex = new RegExp(`\\n?${escapeRegex(startMarker)}[\\s\\S]*?${escapeRegex(endMarker)}\\n?`, 'm')
  const markedBlock = `${startMarker}\n${block}\n${endMarker}\n`
  const next = markerRegex.test(content)
    ? content.replace(markerRegex, `\n${markedBlock}`)
    : (content.trimEnd() ? `${content.trimEnd()}\n\n${markedBlock}` : markedBlock)
  await fs.writeFile(filePath, next, 'utf8')
  return { path: filePath, createdFile, type: 'marked_block' }
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

function removeTomlSection(content, sectionName) {
  return restoreTomlSection(content, sectionName, null)
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
  const legacySectionsToRemove = [
    'mcp_servers.context7',
    'mcp_servers.context7.env',
    'mcp_servers.playwright',
    'mcp_servers.playwright.env',
    'mcp_servers.ace-tool.env',
    'mcp_servers.ace-tool-rs.env',
    'mcp_servers.fast-context.env',
    'mcp_servers.contextweaver.env',
    'mcp_servers.grok-search.env',
    'mcp_servers.exa.env',
    'mcp_servers.mcp-deepwiki.env',
  ]
  for (const sectionName of legacySectionsToRemove) {
    content = removeTomlSection(content, sectionName)
  }
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
    if (config.env && typeof config.env === 'object' && Object.keys(config.env).length > 0) {
      const envEntries = Object.entries(config.env)
        .map(([key, value]) => `${key} = "${String(value).replaceAll('"', '\\"')}"`)
        .join(', ')
      bodyLines.push(`env = { ${envEntries} }`)
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

function normalizeBinaryVersion(output) {
  const trimmed = output.trim()
  if (!trimmed) {
    return ''
  }
  const lines = trimmed.split(/\r?\n/).map(line => line.trim()).filter(Boolean)
  const lastLine = lines[lines.length - 1]
  const versionMatch = lastLine.match(/\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$/)
  return versionMatch ? versionMatch[0] : lastLine
}

function installedBinaryVersion(filePath) {
  try {
    const output = execFileSync(filePath, ['--version'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    return normalizeBinaryVersion(output)
  }
  catch {
    return null
  }
}

async function downloadToFile(url, destPath, timeoutMs) {
  const response = await fetch(url, {
    redirect: 'follow',
    signal: AbortSignal.timeout(timeoutMs),
    headers: {
      'user-agent': `railforge-workflow/${INSTALLER_VERSION}`,
    },
  })
  if (!response.ok) {
    throw new Error(`download failed: ${response.status} ${response.statusText}`)
  }
  const bytes = Buffer.from(await response.arrayBuffer())
  await fs.writeFile(destPath, bytes)
}

async function installBinaryRelease(destPath, assetName, expectedVersion) {
  if (await fileExists(destPath)) {
    const currentVersion = installedBinaryVersion(destPath)
    if (currentVersion === expectedVersion) {
      return {
        path: destPath,
        assetName,
        status: 'existing',
        version: currentVersion,
      }
    }
  }

  const tmpPath = `${destPath}.download`
  const errors = []
  for (const source of binarySources()) {
    const baseUrl = source.url.replace(/\/$/, '')
    const url = `${baseUrl}/${assetName}`
    try {
      await downloadToFile(url, tmpPath, source.timeoutMs)
      if (process.platform !== 'win32') {
        await fs.chmod(tmpPath, 0o755)
      }
      const downloadedVersion = installedBinaryVersion(tmpPath)
      if (downloadedVersion !== expectedVersion) {
        throw new Error(`expected ${expectedVersion}, got ${downloadedVersion || 'unknown'}`)
      }
      await fs.rm(destPath, { force: true })
      await fs.rename(tmpPath, destPath)
      return {
        path: destPath,
        assetName,
        status: 'installed',
        version: downloadedVersion,
        source: url,
      }
    }
    catch (error) {
      errors.push(`${source.name}: ${error instanceof Error ? error.message : String(error)}`)
    }
    finally {
      await fs.rm(tmpPath, { force: true }).catch(() => {})
    }
  }

  return {
    path: destPath,
    assetName,
    status: 'missing',
    version: null,
    errors,
  }
}

async function installBinaryFiles(paths, installedFiles) {
  if (process.env.RAILFORGE_SKIP_BINARY_INSTALL === '1') {
    const binaries = [
      {
        name: 'railforge',
        path: paths.railforgeBinPath,
        assetName: paths.railforgeAssetName,
        status: 'skipped',
        version: null,
      },
      {
        name: 'railforge-codeagent',
        path: paths.codeagentBinPath,
        assetName: paths.codeagentAssetName,
        status: 'skipped',
        version: null,
      },
    ]
    await fs.writeFile(
      paths.binaryStatePath,
      JSON.stringify(
        {
          version: RAILFORGE_BINARY_VERSION,
          releaseTag: RELEASE_TAG,
          skipped: true,
          binaries,
        },
        null,
        2
      ),
      'utf8'
    )
    installedFiles.push(paths.binaryStatePath)
    return { binaries, warnings: [] }
  }

  const entries = [
    { key: 'railforge', destPath: paths.railforgeBinPath, assetName: paths.railforgeAssetName },
    { key: 'railforge-codeagent', destPath: paths.codeagentBinPath, assetName: paths.codeagentAssetName },
  ]

  const binaries = []
  const warnings = []
  for (const entry of entries) {
    const result = await installBinaryRelease(entry.destPath, entry.assetName, RAILFORGE_BINARY_VERSION)
    binaries.push({ name: entry.key, ...result })
    if (result.status !== 'missing') {
      installedFiles.push(entry.destPath)
      continue
    }
    warnings.push(
      `未能下载 ${entry.assetName}，已保留 Python 回退路径。${(result.errors || []).join(' | ')}`
    )
  }

  await fs.writeFile(
    paths.binaryStatePath,
    JSON.stringify(
      {
        version: RAILFORGE_BINARY_VERSION,
        releaseTag: RELEASE_TAG,
        binaries,
      },
      null,
      2
    ),
    'utf8'
  )
  installedFiles.push(paths.binaryStatePath)

  return { binaries, warnings }
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

async function writeGrokSearchRulesFile(targetDir) {
  const rulesDir = path.join(resolveInstallPaths(targetDir).homeRoot, '.claude', 'rules')
  await ensureDir(rulesDir)
  const rulePath = path.join(rulesDir, GROK_SEARCH_RULE_NAME)
  await fs.writeFile(rulePath, GROK_SEARCH_PROMPT, 'utf8')
  return rulePath
}

async function loadOrDefaultMcpConfig(catalogPath) {
  if (await fileExists(catalogPath)) {
    return JSON.parse(await fs.readFile(catalogPath, 'utf8'))
  }
  return defaultMcpConfig()
}

async function writeFastContextPromptFiles(targetDir, { auxiliaryMode = false } = {}) {
  const paths = resolveInstallPaths(targetDir)
  const promptContent = auxiliaryMode ? FAST_CONTEXT_PROMPT_AUXILIARY : FAST_CONTEXT_PROMPT_PRIMARY

  const claudeRulesDir = path.join(paths.homeRoot, '.claude', 'rules')
  await ensureDir(claudeRulesDir)
  const claudeRulePath = path.join(claudeRulesDir, FAST_CONTEXT_RULE_NAME)
  await fs.writeFile(claudeRulePath, promptContent, 'utf8')

  const codexAgentsPath = path.join(paths.homeRoot, '.codex', 'AGENTS.md')
  const geminiInstructionsPath = path.join(paths.homeRoot, '.gemini', 'GEMINI.md')
  await upsertMarkedBlockWithMarkers(codexAgentsPath, promptContent, FAST_CONTEXT_MARKER_START, FAST_CONTEXT_MARKER_END)
  await upsertMarkedBlockWithMarkers(geminiInstructionsPath, promptContent, FAST_CONTEXT_MARKER_START, FAST_CONTEXT_MARKER_END)

  return {
    claudeRulePath,
    codexAgentsPath,
    geminiInstructionsPath,
  }
}

async function configureClaudeSettings(targetDir, mutator) {
  const paths = resolveInstallPaths(targetDir)
  await ensureDir(path.dirname(paths.claudeSettingsPath))
  const { payload } = await readJsonIfExists(paths.claudeSettingsPath, {})
  const settings = payload && typeof payload === 'object' ? payload : {}
  mutator(settings)
  await fs.writeFile(paths.claudeSettingsPath, JSON.stringify(settings, null, 2), 'utf8')
  return paths.claudeSettingsPath
}

export async function configureApiSettings(targetDir, options = {}) {
  const settingsPath = await configureClaudeSettings(targetDir, (settings) => {
    if (!settings.env) settings.env = {}
    if (options.provider === 'official') {
      delete settings.env.ANTHROPIC_BASE_URL
      delete settings.env.ANTHROPIC_AUTH_TOKEN
      delete settings.env.ANTHROPIC_API_KEY
    }
    else if (options.provider === '302ai') {
      settings.env.ANTHROPIC_BASE_URL = 'https://api.302.ai/cc'
      settings.env.ANTHROPIC_AUTH_TOKEN = options.apiKey || ''
      delete settings.env.ANTHROPIC_API_KEY
    }
    else if (options.provider === 'custom') {
      settings.env.ANTHROPIC_BASE_URL = options.apiUrl || ''
      settings.env.ANTHROPIC_AUTH_TOKEN = options.apiKey || ''
      delete settings.env.ANTHROPIC_API_KEY
    }

    Object.assign(settings.env, {
      DISABLE_TELEMETRY: '1',
      DISABLE_ERROR_REPORTING: '1',
      CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1',
      CLAUDE_CODE_ATTRIBUTION_HEADER: '0',
      MCP_TIMEOUT: '60000',
      API_TIMEOUT_MS: '3000000',
      BASH_DEFAULT_TIMEOUT_MS: '600000',
      BASH_MAX_TIMEOUT_MS: '3600000',
      CODEX_TIMEOUT: '7200',
    })
  })

  return {
    action: 'config-api',
    status: 'written',
    file: settingsPath,
    provider: options.provider || 'official',
  }
}

export async function configureOutputStyle(targetDir, style = 'default') {
  const paths = resolveInstallPaths(targetDir)
  const settingsPath = await configureClaudeSettings(targetDir, (settings) => {
    if (style === 'default') {
      delete settings.outputStyle
    }
    else {
      settings.outputStyle = style
    }
  })

  let styleFile = null
  if (style !== 'default') {
    const outputStylesDir = path.join(paths.homeRoot, '.claude', 'output-styles')
    await ensureDir(outputStylesDir)
    styleFile = path.join(outputStylesDir, `${style}.md`)
    await fs.writeFile(styleFile, OUTPUT_STYLE_TEMPLATES[style] || `# ${style}\n\nUse the ${style} response style.\n`, 'utf8')
  }

  return {
    action: 'config-style',
    status: 'written',
    file: settingsPath,
    style,
    styleFile,
  }
}

async function writeContextWeaverEnvFile(targetDir, siliconflowApiKey) {
  const paths = resolveInstallPaths(targetDir)
  const contextWeaverDir = path.join(paths.homeRoot, '.contextweaver')
  await ensureDir(contextWeaverDir)
  const envPath = path.join(contextWeaverDir, '.env')
  const envContent = `# ContextWeaver 配置 (由 RailForge 自动生成)

EMBEDDINGS_API_KEY=${siliconflowApiKey}
EMBEDDINGS_BASE_URL=https://api.siliconflow.cn/v1/embeddings
EMBEDDINGS_MODEL=Qwen/Qwen3-Embedding-8B
EMBEDDINGS_MAX_CONCURRENCY=10
EMBEDDINGS_DIMENSIONS=1024

RERANK_API_KEY=${siliconflowApiKey}
RERANK_BASE_URL=https://api.siliconflow.cn/v1/rerank
RERANK_MODEL=Qwen/Qwen3-Reranker-8B
RERANK_TOP_N=20
`
  await fs.writeFile(envPath, envContent, 'utf8')
  return envPath
}

async function configureManagedMcp(targetDir, { id, serverConfig, backupClaude = false, extraFiles = {}, catalogName = null }) {
  const paths = resolveInstallPaths(targetDir)
  await ensureDir(paths.railforgeRoot)

  const mcpConfig = await loadOrDefaultMcpConfig(paths.mcpCatalogPath)
  mcpConfig.mcpServers[id] = serverConfig
  await fs.writeFile(paths.mcpCatalogPath, JSON.stringify(mcpConfig, null, 2), 'utf8')

  const backupPath = backupClaude
    ? await backupFileIfExists(paths.claudeMcpPath, path.join(paths.homeRoot, '.claude', 'backup'), 'claude-config')
    : null

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
    tool: catalogName || id,
    status: 'configured',
    target: paths.codexRoot,
    backupPath,
    mirrors: mirrorState.mirrors,
    extraFiles,
  }
}

export async function configureGrokSearchMcp(targetDir, options = {}) {
  const paths = resolveInstallPaths(targetDir)
  await ensureDir(paths.railforgeRoot)

  const env = {
    GROK_API_URL: options.grokApiUrl || '',
    GROK_API_KEY: options.grokApiKey || '',
    TAVILY_API_KEY: options.tavilyApiKey || '',
    FIRECRAWL_API_KEY: options.firecrawlApiKey || '',
  }

  const mcpConfig = await loadOrDefaultMcpConfig(paths.mcpCatalogPath)
  mcpConfig.mcpServers['grok-search'] = grokSearchServerConfig(env)
  await fs.writeFile(paths.mcpCatalogPath, JSON.stringify(mcpConfig, null, 2), 'utf8')

  const backupPath = await backupFileIfExists(
    paths.claudeMcpPath,
    path.join(paths.homeRoot, '.claude', 'backup'),
    'claude-config',
  )

  const state = await loadInstallerState(paths.statePath)
  const mirrorState = await writeMirrorFiles(targetDir, mcpConfig)
  state.sharedPatches = {
    ...(state.sharedPatches || {}),
    codexConfig: mirrorState.codex,
    claudeMcp: mirrorState.claude,
    geminiSettings: mirrorState.gemini,
  }
  await saveInstallerState(paths.statePath, state)

  const rulePath = await writeGrokSearchRulesFile(targetDir)
  const codexSynced = ['Context7', 'Playwright', 'grok-search'].map((item) => item.replace('Playwright', 'playwright'))
  const geminiSynced = ['Context7', 'Playwright', 'grok-search'].map((item) =>
    item.replace('Context7', 'context7').replace('Playwright', 'playwright'),
  )

  return {
    action: 'config-mcp',
    tool: 'grok-search',
    status: 'configured',
    target: paths.codexRoot,
    backupPath,
    rulePath,
    mirrors: mirrorState.mirrors,
    envKeys: Object.keys(grokSearchServerConfig(env).env || {}),
    synced: [
      `Codex(${codexSynced.join(',')})`,
      `Gemini(${geminiSynced.join(',')})`,
    ],
  }
}

export async function configureAceToolMcp(targetDir, options = {}) {
  return configureManagedMcp(targetDir, {
    id: 'ace-tool',
    serverConfig: aceToolServerConfig(options),
    backupClaude: true,
  })
}

export async function configureAceToolRsMcp(targetDir, options = {}) {
  return configureManagedMcp(targetDir, {
    id: 'ace-tool-rs',
    serverConfig: aceToolRsServerConfig(options),
    backupClaude: true,
  })
}

export async function configureFastContextMcp(targetDir, options = {}) {
  const promptFiles = await writeFastContextPromptFiles(targetDir, { auxiliaryMode: Boolean(options.auxiliaryMode) })
  return configureManagedMcp(targetDir, {
    id: 'fast-context',
    serverConfig: fastContextServerConfig(options),
    backupClaude: true,
    extraFiles: promptFiles,
    catalogName: 'fast-context',
  })
}

export async function configureContextWeaverMcp(targetDir, options = {}) {
  const envPath = await writeContextWeaverEnvFile(targetDir, options.siliconflowApiKey || '')
  return configureManagedMcp(targetDir, {
    id: 'contextweaver',
    serverConfig: contextWeaverServerConfig(),
    backupClaude: true,
    extraFiles: { envPath },
    catalogName: 'contextweaver',
  })
}

export async function configureAuxiliaryMcp(targetDir, tool, options = {}) {
  const definitions = {
    context7: { id: 'Context7', config: genericServerConfig('npx', ['-y', '@upstash/context7-mcp@latest']) },
    playwright: { id: 'Playwright', config: genericServerConfig('npx', ['-y', '@playwright/mcp@latest']) },
    deepwiki: { id: 'mcp-deepwiki', config: genericServerConfig('npx', ['-y', 'mcp-deepwiki@latest']) },
    exa: { id: 'exa', config: genericServerConfig('npx', ['-y', 'exa-mcp-server@latest'], { EXA_API_KEY: options.exaApiKey || '' }) },
  }
  const selected = definitions[tool]
  if (!selected) {
    throw new Error(`Unsupported auxiliary MCP: ${tool}`)
  }
  return configureManagedMcp(targetDir, {
    id: selected.id,
    serverConfig: selected.config,
    backupClaude: true,
    catalogName: tool,
  })
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
  const mcpConfig = await loadOrDefaultMcpConfig(paths.mcpCatalogPath)
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
if [[ ! -x "$RAILFORGE_BIN" && -x "$CODEX_ROOT/bin/railforge.exe" ]]; then
  RAILFORGE_BIN="$CODEX_ROOT/bin/railforge.exe"
fi
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
  const warnings = []

  await ensureDir(paths.codexRoot)
  await ensureDir(paths.binRoot)
  await ensureDir(paths.skillsRoot)
  await ensureDir(paths.railforgeRoot)
  await writeFile(paths.modelsPath, MODELS_YAML, installedFiles)
  await writeFile(paths.policiesPath, POLICIES_YAML, installedFiles)
  const mcpConfig = await loadOrDefaultMcpConfig(paths.mcpCatalogPath)
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

  const binaryInstall = await installBinaryFiles(paths, installedFiles)
  warnings.push(...binaryInstall.warnings)

  const state = await loadInstallerState(paths.statePath)
  const mirrorState = await writeMirrorFiles(targetDir, mcpConfig)
  const agentsPatch = await upsertMarkedBlock(paths.codexAgentsPath, DEFAULT_AGENTS_MD)

  state.installedFiles = installedFiles
  state.binaries = binaryInstall.binaries
  state.sharedPatches = {
    codexAgents: agentsPatch,
    codexConfig: mirrorState.codex,
    claudeMcp: mirrorState.claude,
    geminiSettings: mirrorState.gemini,
  }
  await saveInstallerState(paths.statePath, state)

  return {
    action: 'init',
    status: 'installed',
    target: paths.codexRoot,
    installedFiles,
    binaries: binaryInstall.binaries,
    warnings,
  }
}

export async function updateProject(targetDir) {
  const result = await initProject(targetDir)
  return {
    action: 'update',
    status: 'updated',
    target: result.target,
    installedFiles: result.installedFiles,
    binaries: result.binaries,
    warnings: result.warnings,
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
  await pruneIfEmpty(paths.binRoot, paths.codexRoot)
  await pruneIfEmpty(path.join(paths.codexRoot, 'skills'), paths.codexRoot)
  await pruneIfEmpty(paths.codexRoot, paths.homeRoot)
  await pruneIfEmpty(path.dirname(paths.claudeMcpPath), paths.homeRoot)
  await pruneIfEmpty(path.dirname(paths.geminiSettingsPath), paths.homeRoot)

  return { action: 'uninstall', status: 'removed', target: paths.codexRoot }
}
