import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import * as readline from 'node:readline'
import { createInterface } from 'node:readline/promises'

import { initProject, probeMcpConfig, uninstallProject, updateProject, writeMcpConfig, writeModelConfig } from './commands.mjs'
import { mainMenuChoices, mcpMenuChoices, modelMenuChoices, renderHeader } from './menu.mjs'
import { MCP_GROUPS } from './mcp.mjs'

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
  const modelsPath = path.join(target, '.railforge', 'runtime', 'models.yaml')
  return fs.existsSync(modelsPath)
}

function optionValue(argv, flag, fallback = null) {
  const index = argv.indexOf(flag)
  if (index === -1 || index + 1 >= argv.length) {
    return fallback
  }
  return argv[index + 1]
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

async function fallbackListPrompt(message, choices) {
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
    const frame = renderFallbackList(message, choices, selectedIndex)
    if (renderedLines > 0) {
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

async function fallbackInputPrompt(message) {
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  })
  try {
    return await rl.question(`${message} `)
  }
  finally {
    await rl.close()
  }
}

async function promptWithFallback(questions, inquirer) {
  if (inquirer) {
    return await inquirer.prompt(questions)
  }

  const answers = {}
  for (const question of questions) {
    if (question.type === 'list') {
      answers[question.name] = await fallbackListPrompt(question.message, question.choices)
      continue
    }
    if (question.type === 'input') {
      answers[question.name] = await fallbackInputPrompt(question.message)
    }
  }
  return answers
}

async function runMenu() {
  if (!process.stdout.isTTY || !process.stdin.isTTY) {
    console.log(renderHeader())
    return
  }

  const inquirer = await getPromptEngine()

  while (true) {
    console.log(renderHeader())
    let action
    if (inquirer) {
      const answer = await promptWithFallback([
        {
          type: 'list',
          name: 'action',
          message: 'RailForge 主菜单',
          choices: mainMenuChoices(),
        },
      ], inquirer)
      action = answer.action
    }
    else {
      const answer = await promptWithFallback([
        {
          type: 'list',
          name: 'action',
          message: 'RailForge 主菜单',
          choices: mainMenuChoices(),
        },
      ], null)
      action = answer.action
    }

    if (action === 'init') {
      console.log(JSON.stringify(await initProject(process.cwd()), null, 2))
    }
    else if (action === 'update') {
      if (!installState(process.cwd())) {
        console.log(JSON.stringify({ action: 'update', status: 'not-installed', suggestion: '先执行初始化 RailForge 配置' }, null, 2))
      }
      else {
        console.log(JSON.stringify(await updateProject(process.cwd()), null, 2))
      }
    }
    else if (action === 'config-mcp') {
      await runMcpMenu(process.cwd())
    }
    else if (action === 'config-model') {
      await runModelMenu(process.cwd())
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
      console.log(JSON.stringify(await uninstallProject(process.cwd()), null, 2))
    }
    else if (action === 'quit') {
      console.log('已退出')
      return
    }

    if (inquirer) {
      await promptWithFallback([
        {
          type: 'input',
          name: 'continue',
          message: '按 Enter 返回主菜单...',
        },
      ], inquirer)
    }
  }
}

async function runMcpMenu(target) {
  const inquirer = await getPromptEngine()
  let action
  if (inquirer) {
    const answer = await promptWithFallback([
      {
        type: 'list',
        name: 'action',
        message: '配置 MCP',
        choices: mcpMenuChoices(),
      },
    ], inquirer)
    action = answer.action
  }
  else {
    const answer = await promptWithFallback([
      {
        type: 'list',
        name: 'action',
        message: '配置 MCP',
        choices: mcpMenuChoices(),
      },
    ], null)
    action = answer.action
  }
  if (action === 'back') {
    return
  }
  if (action === 'write-config' || action === 'code-retrieval' || action === 'web-search' || action === 'auxiliary') {
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
    const answer = await promptWithFallback([
      {
        type: 'list',
        name: 'leadWriter',
        message: '配置模型路由',
        choices: modelMenuChoices(),
      },
    ], inquirer)
    leadWriter = answer.leadWriter
  }
  else {
    const answer = await promptWithFallback([
      {
        type: 'list',
        name: 'leadWriter',
        message: '配置模型路由',
        choices: modelMenuChoices(),
      },
    ], null)
    leadWriter = answer.leadWriter
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
  const [command = 'menu'] = argv
  const targetFlag = argv.indexOf('--target')
  const target = targetFlag >= 0 ? argv[targetFlag + 1] : process.cwd()

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
