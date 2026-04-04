import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import readline from 'node:readline/promises'

import { initProject, probeMcpConfig, uninstallProject, updateProject, writeMcpConfig, writeModelConfig } from './commands.mjs'
import { renderMainMenu } from './menu.mjs'
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

function optionValue(argv, flag, fallback = null) {
  const index = argv.indexOf(flag)
  if (index === -1 || index + 1 >= argv.length) {
    return fallback
  }
  return argv[index + 1]
}

async function runMenu() {
  if (!process.stdout.isTTY || !process.stdin.isTTY) {
    console.log(renderMainMenu())
    return
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  })
  console.log(renderMainMenu())
  const answer = await rl.question('\n选择操作编号: ')
  rl.close()
  if (answer === '1') {
    console.log(JSON.stringify(await initProject(process.cwd()), null, 2))
    return
  }
  if (answer === '2') {
    console.log(JSON.stringify(await updateProject(process.cwd()), null, 2))
    return
  }
  if (answer === '3' || answer.toUpperCase() === 'C') {
    console.log(JSON.stringify(await writeMcpConfig(process.cwd()), null, 2))
    return
  }
  if (answer === '4') {
    console.log(JSON.stringify(await writeModelConfig(process.cwd()), null, 2))
    return
  }
  if (answer === '5' || answer.toUpperCase() === 'T') {
    console.log(JSON.stringify(doctorPayload(), null, 2))
    return
  }
  if (answer === '6' || answer === '-') {
    console.log(JSON.stringify(await uninstallProject(process.cwd()), null, 2))
    return
  }
  if (answer.toUpperCase() === 'H') {
    console.log(
      [
        'RailForge 命令帮助',
        '',
        '/rf:spec-init',
        '/rf:spec-research',
        '/rf:spec-plan',
        '/rf:spec-impl',
        '/rf:spec-review',
        '',
        '常见问题请查看 docs/guide/faq.md',
        '更多信息请查看 README.md 和 docs/architecture/best-practices.md',
      ].join('\n'),
    )
    return
  }
  if (answer.toUpperCase() === 'Q') {
    console.log('已退出')
    return
  }
  console.log(`已选择: ${answer || '未输入'}`)
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
