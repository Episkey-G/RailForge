import fs from 'node:fs'
import { homedir } from 'node:os'
import path from 'node:path'
import process from 'node:process'
import * as readline from 'node:readline'

import {
  configureAceToolMcp,
  configureApiSettings,
  configureAceToolRsMcp,
  configureAuxiliaryMcp,
  configureContextWeaverMcp,
  configureOutputStyle,
  configureFastContextMcp,
  configureGrokSearchMcp,
  initProject,
  probeMcpConfig,
  uninstallProject,
  updateProject,
  writeMcpConfig,
  writeModelConfig,
} from './commands.mjs'
import { mainMenuChoices, mcpMenuChoices, modelMenuChoices, renderHeader, renderMainMenuBody } from './menu.mjs'
import { MCP_GROUPS } from './mcp.mjs'

async function maybeRunEvalHook() {
  const raw = process.env.RAILFORGE_INSTALLER_EVAL
  if (!raw) return false
  const payload = JSON.parse(raw)
  if (payload.module !== 'commands') {
    throw new Error(`Unsupported eval module: ${payload.module}`)
  }
  const commands = await import('./commands.mjs')
  const fn = commands[payload.fn]
  if (typeof fn !== 'function') {
    throw new Error(`Unsupported eval function: ${payload.fn}`)
  }
  const result = await fn(...(payload.args || []))
  console.log(JSON.stringify(result, null, 2))
  return true
}

function detectBinary(name) {
  const pathValue = process.env.PATH || ''
  for (const dir of pathValue.split(path.delimiter)) {
    if (!dir) continue
    const candidate = path.join(dir, name)
    if (fs.existsSync(candidate)) return candidate
  }
  return null
}

function doctorPayload() {
  return {
    node: process.version,
    codex: detectBinary('codex'),
    claude: detectBinary('claude'),
    gemini: detectBinary('gemini'),
    python: detectBinary('python3') || detectBinary('python'),
    jq: detectBinary('jq'),
    mcpGroups: MCP_GROUPS
  }
}

function installState(target) {
  const modelsPath = path.join(target, '.codex', '.railforge', 'models.yaml')
  return fs.existsSync(modelsPath)
}

async function runInitWizard(target, inquirer) {
  console.log()
  console.log('  🔑 Step 1/6 — 配置 Codex 主写作模型')
  console.log()
  const modelAnswer = await inquirer.prompt([{
    type: 'list',
    name: 'leadWriter',
    message: '选择默认主写作路径',
    choices: [
      { name: 'Hosted Codex (推荐)', value: 'hosted_codex' },
      { name: 'Codex CLI fallback', value: 'codex_cli' },
    ],
    default: 'hosted_codex',
  }])

  console.log()
  console.log('  🤝 Step 2/6 — 配置协作模型')
  console.log()
  const collaboratorAnswer = await inquirer.prompt([
    {
      type: 'list',
      name: 'backendSpecialist',
      message: '选择后端 specialist / evaluator',
      choices: [
        { name: 'Claude CLI (推荐)', value: 'claude_cli' },
        { name: 'Gemini CLI', value: 'gemini_cli' },
      ],
      default: 'claude_cli',
    },
    {
      type: 'list',
      name: 'frontendSpecialist',
      message: '选择前端 specialist / evaluator',
      choices: [
        { name: 'Gemini CLI (推荐)', value: 'gemini_cli' },
        { name: 'Claude CLI', value: 'claude_cli' },
      ],
      default: 'gemini_cli',
    },
  ])

  console.log()
  console.log('  🔍 Step 3/6 — 选择代码检索 MCP')
  console.log()
  const retrievalAnswer = await inquirer.prompt([{
    type: 'list',
    name: 'tool',
    message: '选择代码检索工具',
    choices: [
      { name: 'ace-tool (推荐)', value: 'ace-tool' },
      { name: 'ace-tool-rs (推荐)', value: 'ace-tool-rs' },
      { name: 'fast-context (推荐)', value: 'fast-context' },
      { name: 'ContextWeaver', value: 'contextweaver' },
      { name: '跳过', value: 'skip' },
    ],
    default: 'ace-tool',
  }])

  let retrievalOptions = {}
  if (retrievalAnswer.tool === 'ace-tool' || retrievalAnswer.tool === 'ace-tool-rs') {
    retrievalOptions = await inquirer.prompt([
      { type: 'input', name: 'baseUrl', message: 'Base URL (中转服务必填，官方留空)', default: '' },
      { type: 'password', name: 'token', message: 'Token (必填)', mask: '*' },
    ])
  }
  else if (retrievalAnswer.tool === 'fast-context') {
    retrievalOptions = await inquirer.prompt([
      { type: 'input', name: 'apiKey', message: 'WINDSURF_API_KEY (可选)', default: '' },
      { type: 'confirm', name: 'includeSnippets', message: '返回完整代码片段？', default: false },
    ])
  }
  else if (retrievalAnswer.tool === 'contextweaver') {
    retrievalOptions = await inquirer.prompt([
      { type: 'password', name: 'siliconflowApiKey', message: '硅基流动 API Key', mask: '*' },
    ])
  }

  console.log()
  console.log('  🌐 Step 4/6 — 配置联网搜索 MCP')
  console.log()
  const grokWant = await inquirer.prompt([{
    type: 'confirm',
    name: 'enabled',
    message: '安装 grok-search 联网搜索 MCP？',
    default: true,
  }])
  let grokOptions = {}
  if (grokWant.enabled) {
    grokOptions = await inquirer.prompt([
      { type: 'input', name: 'grokApiUrl', message: 'GROK_API_URL (可选)', default: '' },
      { type: 'password', name: 'grokApiKey', message: 'GROK_API_KEY (可选)', mask: '*' },
      { type: 'password', name: 'tavilyApiKey', message: 'TAVILY_API_KEY (可选)', mask: '*' },
      { type: 'password', name: 'firecrawlApiKey', message: 'FIRECRAWL_API_KEY (可选)', mask: '*' },
    ])
  }

  console.log()
  console.log('  🧰 Step 5/6 — 选择辅助 MCP')
  console.log()
  const auxiliaryAnswer = await inquirer.prompt([{
    type: 'checkbox',
    name: 'selected',
    message: '选择要安装的辅助工具（空格选择，回车确认）',
    choices: [
      { name: 'Context7 - 获取最新库文档', value: 'context7' },
      { name: 'Playwright - 浏览器自动化/测试', value: 'playwright' },
      { name: 'DeepWiki - 知识库查询', value: 'deepwiki' },
      { name: 'Exa - 搜索引擎（需 API Key）', value: 'exa' },
    ],
  }])

  console.log()
  console.log('  🎨 Step 6/6 — 配置输出风格与 Claude 协作 API')
  console.log()
  const styleAnswer = await inquirer.prompt([{
    type: 'list',
    name: 'style',
    message: '选择输出风格',
    choices: [
      { name: 'default', value: 'default' },
      { name: 'engineer-professional', value: 'engineer-professional' },
      { name: 'ojousama-engineer', value: 'ojousama-engineer' },
      { name: 'abyss-concise', value: 'abyss-concise' },
    ],
    default: 'default',
  }])

  const apiAnswer = await inquirer.prompt([{
    type: 'list',
    name: 'provider',
    message: 'Claude 协作 API 配置',
    choices: [
      { name: 'official - 使用 Claude 官方配置', value: 'official' },
      { name: 'custom - 自定义 API 端点', value: 'custom' },
      { name: '302ai - 使用 302.AI', value: '302ai' },
      { name: 'skip - 暂不配置', value: 'skip' },
    ],
    default: 'skip',
  }])

  let apiOptions = {}
  if (apiAnswer.provider === 'custom') {
    apiOptions = await inquirer.prompt([
      { type: 'input', name: 'apiUrl', message: 'API URL', default: '' },
      { type: 'password', name: 'apiKey', message: 'API Key', mask: '*' },
    ])
  }
  else if (apiAnswer.provider === '302ai') {
    apiOptions = await inquirer.prompt([
      { type: 'password', name: 'apiKey', message: '302.AI API Key', mask: '*' },
    ])
  }

  const initResult = await initProject(target)
  await writeModelConfig(target, {
    leadWriter: modelAnswer.leadWriter,
    backendSpecialist: collaboratorAnswer.backendSpecialist,
    frontendSpecialist: collaboratorAnswer.frontendSpecialist,
    backendEvaluator: collaboratorAnswer.backendSpecialist,
    frontendEvaluator: collaboratorAnswer.frontendSpecialist,
  })

  if (retrievalAnswer.tool === 'ace-tool') {
    await configureAceToolMcp(target, retrievalOptions)
  }
  else if (retrievalAnswer.tool === 'ace-tool-rs') {
    await configureAceToolRsMcp(target, retrievalOptions)
  }
  else if (retrievalAnswer.tool === 'fast-context') {
    await configureFastContextMcp(target, retrievalOptions)
  }
  else if (retrievalAnswer.tool === 'contextweaver') {
    await configureContextWeaverMcp(target, retrievalOptions)
  }

  if (grokWant.enabled) {
    await configureGrokSearchMcp(target, grokOptions)
  }

  for (const tool of auxiliaryAnswer.selected || []) {
    let options = {}
    if (tool === 'exa') {
      options = await inquirer.prompt([{ type: 'password', name: 'exaApiKey', message: 'Exa API Key', mask: '*' }])
    }
    await configureAuxiliaryMcp(target, tool, options)
  }

  await configureOutputStyle(target, styleAnswer.style)
  if (apiAnswer.provider !== 'skip') {
    await configureApiSettings(target, { provider: apiAnswer.provider, ...apiOptions })
  }

  return {
    ...initResult,
    wizard: {
      leadWriter: modelAnswer.leadWriter,
      backendSpecialist: collaboratorAnswer.backendSpecialist,
      frontendSpecialist: collaboratorAnswer.frontendSpecialist,
      retrievalTool: retrievalAnswer.tool,
      grokSearch: grokWant.enabled,
      auxiliary: auxiliaryAnswer.selected || [],
      outputStyle: styleAnswer.style,
      apiProvider: apiAnswer.provider,
    },
  }
}

function optionValue(argv, flag, fallback = null) {
  const index = argv.indexOf(flag)
  if (index === -1 || index + 1 >= argv.length) {
    return fallback
  }
  return argv[index + 1]
}

function defaultInstallTarget() {
  return homedir()
}

async function getPromptEngine() {
  try {
    const module = await import('inquirer')
    return module.default
  }
  catch {
    return null
  }
}

function renderFallbackList(message, choices, selectedIndex) {
  const lines = [`? ${message}`]
  for (const [index, choice] of choices.entries()) {
    const prefix = index === selectedIndex ? '❯' : ' '
    lines.push(`${prefix} ${choice.name}`)
  }
  lines.push('')
  lines.push('↑↓ navigate • ⏎ select')
  return lines.join('\n')
}

async function fallbackListPrompt(message, choices, renderer = null, prefixFrame = '') {
  const input = process.stdin
  const output = process.stdout
  const canUseRawMode = input.isTTY && typeof input.setRawMode === 'function'
  readline.emitKeypressEvents(input)
  if (canUseRawMode) {
    input.setRawMode(true)
  }

  let selectedIndex = 0
  let renderedLines = 0

  const repaint = () => {
    const frame = renderer ? renderer(selectedIndex) : renderFallbackList(message, choices, selectedIndex)
    if (renderedLines === 0 && prefixFrame) {
      output.write(`${prefixFrame}\n\n`)
    }
    else if (renderedLines > 0) {
      output.write(`\x1b[${renderedLines}F\x1b[J`)
    }
    output.write(frame)
    renderedLines = frame.split('\n').length
  }

  repaint()

  return await new Promise((resolve, reject) => {
    const cleanup = () => {
      input.off('keypress', onKeypress)
      input.off('end', onEnd)
      if (canUseRawMode) {
        input.setRawMode(false)
      }
      output.write('\n')
    }

    const onEnd = () => {
      cleanup()
      reject(new Error('prompt_aborted'))
    }

    const onKeypress = (chars, key = {}) => {
      if (key.name === 'up') {
        selectedIndex = (selectedIndex - 1 + choices.length) % choices.length
        repaint()
        return
      }
      if (key.name === 'down') {
        selectedIndex = (selectedIndex + 1) % choices.length
        repaint()
        return
      }
      if (key.name === 'return' || key.name === 'enter') {
        const value = choices[selectedIndex]?.value
        cleanup()
        resolve(value)
        return
      }
      if (chars === '\u0004' || (key.ctrl && (key.name === 'd' || key.name === 'c'))) {
        cleanup()
        reject(new Error('prompt_aborted'))
      }
    }

    input.on('keypress', onKeypress)
    input.on('end', onEnd)
  })
}

async function waitForEnter(message) {
  const input = process.stdin
  const output = process.stdout
  const canUseRawMode = input.isTTY && typeof input.setRawMode === 'function'
  readline.emitKeypressEvents(input)
  if (canUseRawMode) {
    input.setRawMode(true)
  }
  output.write(`${message} `)

  return await new Promise((resolve, reject) => {
    const cleanup = () => {
      input.off('keypress', onKeypress)
      input.off('end', onEnd)
      if (canUseRawMode) {
        input.setRawMode(false)
      }
      output.write('\n')
    }

    const onEnd = () => {
      cleanup()
      reject(new Error('prompt_aborted'))
    }

    const onKeypress = (chars, key = {}) => {
      if (key.name === 'return' || key.name === 'enter') {
        cleanup()
        resolve('')
        return
      }
      if (chars === '\u0004' || (key.ctrl && (key.name === 'd' || key.name === 'c'))) {
        cleanup()
        reject(new Error('prompt_aborted'))
      }
    }

    input.on('keypress', onKeypress)
    input.on('end', onEnd)
  })
}

async function runMenu() {
  if (!process.stdout.isTTY || !process.stdin.isTTY) {
    console.log(`${renderHeader()}\n\n${renderMainMenuBody(0)}`)
    return
  }

  const inquirer = await getPromptEngine()

  while (true) {
    let action
    if (inquirer) {
      console.log()
      console.log(renderHeader())
      console.log()
      const answer = await inquirer.prompt([{
        type: 'list',
        name: 'action',
        message: 'RailForge 主菜单',
        pageSize: 20,
        choices: mainMenuChoices(),
      }])
      action = answer.action
    }
    else {
      action = await fallbackListPrompt(
        'RailForge 主菜单',
        mainMenuChoices(),
        (selectedIndex) => `${renderMainMenuBody(selectedIndex)}\n\n↑↓ navigate • ⏎ select`,
        renderHeader()
      )
    }
    const target = defaultInstallTarget()

    if (action === 'init') {
      console.log(JSON.stringify(inquirer ? await runInitWizard(target, inquirer) : await initProject(target), null, 2))
    }
    else if (action === 'update') {
      if (!installState(target)) {
        console.log(JSON.stringify({ action: 'update', status: 'not-installed', suggestion: '先执行初始化 RailForge 配置' }, null, 2))
      }
      else {
        console.log(JSON.stringify(await updateProject(target), null, 2))
      }
    }
    else if (action === 'config-mcp') {
      await runMcpMenu(target)
    }
    else if (action === 'config-model') {
      await runModelMenu(target)
    }
    else if (action === 'tools' || action === 'check-cli') {
      console.log(JSON.stringify(doctorPayload(), null, 2))
    }
    else if (action === 'help') {
      console.log(
        [
          'RailForge 命令帮助',
          '',
          '/rf:spec-init',
          '/rf:spec-research',
          '/rf:spec-plan',
          '/rf:spec-impl',
          '/rf:spec-review',
          '/rf:openspec-apply',
          '/rf:openspec-archive',
          '',
          '常见问题请查看 docs/guide/faq.md',
          '更多信息请查看 README.md 和 docs/architecture/best-practices.md',
        ].join('\n'),
      )
    }
    else if (action === 'uninstall') {
      console.log(JSON.stringify(await uninstallProject(target), null, 2))
    }
    else if (action === 'quit') {
      console.log('已退出')
      return
    }

    if (inquirer) {
      await inquirer.prompt([{
        type: 'input',
        name: 'continue',
        message: '按 Enter 返回主菜单...',
      }])
    }
    else {
      await waitForEnter('按 Enter 返回主菜单...')
    }
  }
}

async function runMcpMenu(target) {
  const inquirer = await getPromptEngine()
  let action
  if (inquirer) {
    const answer = await inquirer.prompt([{
      type: 'list',
      name: 'action',
      message: '配置 MCP',
      choices: mcpMenuChoices(),
    }])
    action = answer.action
  }
  else {
    action = await fallbackListPrompt('配置 MCP', mcpMenuChoices())
  }
  if (action === 'back') {
    return
  }
  if (action === 'code-retrieval') {
    if (!inquirer) {
      console.log(JSON.stringify({ action: 'config-mcp', group: 'code-retrieval', status: 'requires-interactive-prompt' }, null, 2))
      return
    }
    const answer = await inquirer.prompt([{
      type: 'list',
      name: 'tool',
      message: '选择代码检索工具',
      choices: [
        { name: 'ace-tool (推荐) - 代码检索', value: 'ace-tool' },
        { name: 'ace-tool-rs (推荐) - Rust 版本', value: 'ace-tool-rs' },
        { name: 'fast-context (推荐) - Windsurf Fast Context', value: 'fast-context' },
        { name: 'ContextWeaver - 本地混合搜索', value: 'contextweaver' },
        { name: '返回', value: 'back' },
      ],
    }])
    if (answer.tool === 'back') return
    if (answer.tool === 'ace-tool' || answer.tool === 'ace-tool-rs') {
      const answers = await inquirer.prompt([
        { type: 'input', name: 'baseUrl', message: 'Base URL (中转服务必填，官方留空)', default: '' },
        { type: 'password', name: 'token', message: 'Token (必填)', mask: '*' },
      ])
      const result = answer.tool === 'ace-tool'
        ? await configureAceToolMcp(target, answers)
        : await configureAceToolRsMcp(target, answers)
      console.log(JSON.stringify(result, null, 2))
      return
    }
    if (answer.tool === 'fast-context') {
      const answers = await inquirer.prompt([
        { type: 'input', name: 'apiKey', message: 'WINDSURF_API_KEY (本地装了 Windsurf 可留空自动提取)', default: '' },
        { type: 'confirm', name: 'includeSnippets', message: '返回完整代码片段？', default: false },
      ])
      console.log(JSON.stringify(await configureFastContextMcp(target, answers), null, 2))
      return
    }
    if (answer.tool === 'contextweaver') {
      const answers = await inquirer.prompt([
        { type: 'password', name: 'siliconflowApiKey', message: '硅基流动 API Key', mask: '*' },
      ])
      console.log(JSON.stringify(await configureContextWeaverMcp(target, answers), null, 2))
      return
    }
  }
  if (action === 'web-search') {
    if (!inquirer) {
      console.log(JSON.stringify({ action: 'config-mcp', tool: 'grok-search', status: 'requires-interactive-prompt' }, null, 2))
      return
    }
    console.log()
    console.log('  🔍 联网搜索 MCP (grok-search)')
    console.log('  比 Claude Code 内置联网更好用')
    console.log()
    console.log('  📖 获取 API Keys：')
    console.log('     Tavily: https://www.tavily.com/ (免费额度 1000次/月)')
    console.log('     Firecrawl: https://www.firecrawl.dev/ (注册即送额度)')
    console.log('     Grok API: 需自行部署 grok2api（可选）')
    console.log()
    const answers = await inquirer.prompt([
      { type: 'input', name: 'grokApiUrl', message: 'GROK_API_URL (可选)', default: '' },
      { type: 'password', name: 'grokApiKey', message: 'GROK_API_KEY (可选)', mask: '*' },
      { type: 'password', name: 'tavilyApiKey', message: 'TAVILY_API_KEY (可选)', mask: '*' },
      { type: 'password', name: 'firecrawlApiKey', message: 'FIRECRAWL_API_KEY (可选)', mask: '*' },
    ])
    console.log()
    console.log('⏳ 正在安装 grok-search MCP...')
    const result = await configureGrokSearchMcp(target, answers)
    console.log()
    if (result.backupPath) {
      console.log(`  ✓ Backup created: ${result.backupPath}`)
      console.log()
    }
    console.log('✓ grok-search MCP 配置成功！')
    console.log(`✓ 全局搜索提示词已写入 ${result.rulePath}`)
    console.log(`✓ MCP 已同步到 ${result.synced.join(' + ')}`)
    console.log('  重启 Claude Code CLI 使配置生效')
    return
  }
  if (action === 'auxiliary') {
    if (!inquirer) {
      console.log(JSON.stringify({ action: 'config-mcp', group: 'auxiliary', status: 'requires-interactive-prompt' }, null, 2))
      return
    }
    const answers = await inquirer.prompt([{
      type: 'checkbox',
      name: 'selected',
      message: '选择要安装的辅助工具（空格选择，回车确认）',
      choices: [
        { name: 'Context7 - 获取最新库文档', value: 'context7' },
        { name: 'Playwright - 浏览器自动化/测试', value: 'playwright' },
        { name: 'DeepWiki - 知识库查询', value: 'deepwiki' },
        { name: 'Exa - 搜索引擎（需 API Key）', value: 'exa' },
      ],
    }])
    for (const tool of answers.selected || []) {
      let options = {}
      if (tool === 'exa') {
        options = await inquirer.prompt([{ type: 'password', name: 'exaApiKey', message: 'Exa API Key', mask: '*' }])
      }
      console.log(JSON.stringify(await configureAuxiliaryMcp(target, tool, options), null, 2))
    }
    return
  }
  if (action === 'write-config') {
    console.log(JSON.stringify(await writeMcpConfig(target), null, 2))
    return
  }
  if (action === 'probe') {
    console.log(JSON.stringify(await probeMcpConfig(target), null, 2))
  }
}

async function runModelMenu(target) {
  const inquirer = await getPromptEngine()
  let leadWriter
  if (inquirer) {
    const answer = await inquirer.prompt([{
      type: 'list',
      name: 'leadWriter',
      message: '配置模型路由',
      choices: modelMenuChoices(),
    }])
    leadWriter = answer.leadWriter
  }
  else {
    leadWriter = await fallbackListPrompt('配置模型路由', modelMenuChoices())
  }
  if (leadWriter === 'back') {
    return
  }
  console.log(
    JSON.stringify(
      await writeModelConfig(target, {
        leadWriter,
        backendSpecialist: 'claude_cli',
        frontendSpecialist: 'gemini_cli',
        backendEvaluator: 'claude_cli',
        frontendEvaluator: 'gemini_cli',
      }),
      null,
      2,
    ),
  )
}

export async function main(argv = []) {
  if (await maybeRunEvalHook()) {
    return
  }

  const [command = 'menu'] = argv
  const targetFlag = argv.indexOf('--target')
  const target = targetFlag >= 0 ? argv[targetFlag + 1] : defaultInstallTarget()

  if (command === 'menu') {
    await runMenu()
    return
  }

  if (command === 'doctor') {
    console.log(JSON.stringify(doctorPayload(), null, 2))
    return
  }

  if (command === 'init') {
    console.log(JSON.stringify(await initProject(target), null, 2))
    return
  }

  if (command === 'update') {
    console.log(JSON.stringify(await updateProject(target), null, 2))
    return
  }

  if (command === 'config-mcp') {
    const tool = optionValue(argv, '--tool')
    if (tool === 'grok-search') {
      console.log(
        JSON.stringify(
          await configureGrokSearchMcp(target, {
            grokApiUrl: optionValue(argv, '--grok-api-url', ''),
            grokApiKey: optionValue(argv, '--grok-api-key', ''),
            tavilyApiKey: optionValue(argv, '--tavily-api-key', ''),
            firecrawlApiKey: optionValue(argv, '--firecrawl-api-key', ''),
          }),
          null,
          2,
        ),
      )
      return
    }
    if (tool === 'ace-tool') {
      console.log(JSON.stringify(await configureAceToolMcp(target, {
        baseUrl: optionValue(argv, '--base-url', ''),
        token: optionValue(argv, '--token', ''),
      }), null, 2))
      return
    }
    if (tool === 'ace-tool-rs') {
      console.log(JSON.stringify(await configureAceToolRsMcp(target, {
        baseUrl: optionValue(argv, '--base-url', ''),
        token: optionValue(argv, '--token', ''),
      }), null, 2))
      return
    }
    if (tool === 'fast-context') {
      console.log(JSON.stringify(await configureFastContextMcp(target, {
        apiKey: optionValue(argv, '--windsurf-api-key', ''),
        includeSnippets: argv.includes('--include-snippets'),
      }), null, 2))
      return
    }
    if (tool === 'contextweaver') {
      console.log(JSON.stringify(await configureContextWeaverMcp(target, {
        siliconflowApiKey: optionValue(argv, '--siliconflow-api-key', ''),
      }), null, 2))
      return
    }
    if (['context7', 'playwright', 'deepwiki', 'exa'].includes(tool)) {
      console.log(JSON.stringify(await configureAuxiliaryMcp(target, tool, {
        exaApiKey: optionValue(argv, '--exa-api-key', ''),
      }), null, 2))
      return
    }
    console.log(JSON.stringify(await writeMcpConfig(target), null, 2))
    return
  }

  if (command === 'probe-mcp') {
    console.log(JSON.stringify(await probeMcpConfig(target), null, 2))
    return
  }

  if (command === 'config-model') {
    console.log(
      JSON.stringify(
        await writeModelConfig(target, {
          leadWriter: optionValue(argv, '--lead-writer', 'hosted_codex'),
          backendSpecialist: optionValue(argv, '--backend-specialist', 'claude_cli'),
          frontendSpecialist: optionValue(argv, '--frontend-specialist', 'gemini_cli'),
          backendEvaluator: optionValue(argv, '--backend-evaluator', 'claude_cli'),
          frontendEvaluator: optionValue(argv, '--frontend-evaluator', 'gemini_cli'),
        }),
        null,
        2,
      ),
    )
    return
  }

  if (command === 'help') {
    console.log(
      [
        'RailForge Workflow Installer',
        '',
        'Commands:',
        '  menu',
        '  init --target <dir>',
        '  update --target <dir>',
        '  config-mcp --target <dir>',
        '  probe-mcp --target <dir>',
        '  config-model --target <dir> --lead-writer hosted_codex|codex_cli',
        '  doctor',
        '  uninstall --target <dir>',
        '',
        'Spec Workflow:',
        '  /rf:spec-init',
        '  /rf:spec-research',
        '  /rf:spec-plan',
        '  /rf:spec-impl',
        '  /rf:spec-review',
        '  /rf:openspec-apply',
        '  /rf:openspec-archive',
      ].join('\n'),
    )
    return
  }

  if (command === 'uninstall') {
    console.log(JSON.stringify(await uninstallProject(target), null, 2))
    return
  }

  console.log(`未知命令: ${command}`)
  process.exitCode = 1
}
