import fs from 'node:fs'
import { MCP_GROUPS } from './mcp.mjs'

const { version } = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url), 'utf8'))

export function renderHeader() {
  const versionLine = `║       v${version}  |  9 commands  |  zh-CN  |  ace-tool       ║`
  return [
    '╔════════════════════════════════════════════════════════════╗',
    '║                                                            ║',
    '║                ██████╗  ███████╗  ███████╗                 ║',
    '║                ██╔══██╗ ██╔════╝  ██╔════╝                 ║',
    '║                ██████╔╝ █████╗    █████╗                   ║',
    '║                ██╔══██╗ ██╔══╝    ██╔══╝                   ║',
    '║                ██║  ██║ ██║       ██║                      ║',
    '║                ╚═╝  ╚═╝ ╚═╝       ╚═╝                      ║',
    '║                                                            ║',
    '║                 Claude + Codex + Gemini                   ║',
    '║                Multi-Model Collaboration                  ║',
    '║                                                            ║',
    versionLine,
    '║                                                            ║',
    '╚════════════════════════════════════════════════════════════╝',
  ].join('\n')
}

export function renderMainMenuBody(selectedIndex = 0) {
  const mcpSummary = MCP_GROUPS.map((group) => `- ${group.title}: ${group.items.map((item) => item.label).join(', ')}`)
  const menuLines = mainMenuChoices().map((item, index) => {
    const prefix = index === selectedIndex ? '❯' : ' '
    return `${prefix} ${item.name}`
  })
  return [
    '? RailForge 主菜单',
    ' ────────────── Codex CLI ───────────────',
    ...menuLines.slice(0, 4),
    ' ──────────────── 其他工具 ────────────────',
    ...menuLines.slice(4, 6),
    ' ───────────────── RailForge ─────────────────',
    ...menuLines.slice(6, 8),
    ' ──────────────────────────────────────────',
    menuLines[8],
    '',
    'MCP 分组：',
    ...mcpSummary,
  ].join('\n')
}

export function mainMenuChoices() {
  return [
    { name: '1. 初始化 RailForge 配置      - 安装 spec 工作流', value: 'init' },
    { name: '2. 更新工作流               - 更新到最新版本', value: 'update' },
    { name: '3. 配置 MCP                 - 代码检索 MCP 工具', value: 'config-mcp' },
    { name: '4. 配置模型路由             - Hosted Codex / Claude / Gemini', value: 'config-model' },
    { name: 'T. 实用工具                 - doctor, probes, diagnostics', value: 'tools' },
    { name: 'C. 检查宿主 CLI             - Codex / Claude / Gemini / jq', value: 'check-cli' },
    { name: 'H. 帮助                     - 查看全部斜杠命令', value: 'help' },
    { name: '-. 卸载 RailForge           - 移除 RailForge 配置', value: 'uninstall' },
    { name: 'Q. 退出', value: 'quit' },
  ]
}

export function mcpMenuChoices() {
  return [
    { name: '1. 代码检索 MCP           - ace-tool / ace-tool-rs / fast-context / ContextWeaver', value: 'code-retrieval' },
    { name: '2. 联网搜索 MCP           - grok-search', value: 'web-search' },
    { name: '3. 辅助工具 MCP           - Context7 / Playwright / DeepWiki / Exa', value: 'auxiliary' },
    { name: '4. 写入项目 .mcp.json      - 同步镜像配置', value: 'write-config' },
    { name: '5. 探测 MCP 配置           - probe-mcp', value: 'probe' },
    { name: 'B. 返回主菜单', value: 'back' },
  ]
}

export function modelMenuChoices() {
  return [
    { name: '1. Hosted Codex 默认主写作', value: 'hosted_codex' },
    { name: '2. Codex CLI fallback 主写作', value: 'codex_cli' },
    { name: 'B. 返回主菜单', value: 'back' },
  ]
}
